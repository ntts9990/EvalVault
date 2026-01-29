from __future__ import annotations

import argparse
import hashlib
import json
import logging
from collections.abc import Iterable
from pathlib import Path

from evalvault.adapters.inbound.api.routers.chat import _chunk_user_guide, _load_user_guide_text
from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter
from evalvault.adapters.outbound.nlp.korean.dense_retriever import KoreanDenseRetriever
from evalvault.adapters.outbound.retriever.pgvector_store import PgvectorStore
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import Settings

logger = logging.getLogger(__name__)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _batched(items: list[str], batch_size: int) -> Iterable[list[str]]:
    for index in range(0, len(items), batch_size):
        yield items[index : index + batch_size]


def _build_conn_string(settings: Settings) -> str:
    if settings.postgres_connection_string:
        return settings.postgres_connection_string
    host = settings.postgres_host or "localhost"
    port = settings.postgres_port
    database = settings.postgres_database
    user = settings.postgres_user or "postgres"
    password = settings.postgres_password or ""
    return f"host={host} port={port} dbname={database} user={user} password={password}"


def _embedding_func(
    *,
    settings: Settings,
    embedding_model: str,
    matryoshka_dim: int | None,
    batch_size: int,
):
    settings.ollama_embedding_model = embedding_model
    adapter = OllamaAdapter(settings)
    retriever = KoreanDenseRetriever(
        model_name=embedding_model,
        ollama_adapter=adapter,
        matryoshka_dim=matryoshka_dim,
        batch_size=batch_size,
    )
    return retriever.dimension, retriever.get_embedding_func()


def _embed_texts(
    texts: list[str],
    embedding_func,
    batch_size: int,
):
    embeddings: list[list[float]] = []
    for batch in _batched(texts, batch_size):
        embeddings.extend(embedding_func(batch))
    return embeddings


def _build_user_guide_chunks(limit: int) -> list[str]:
    content = _load_user_guide_text()
    if content is None:
        return []
    return _chunk_user_guide(content, limit)


def _format_metrics(metrics) -> str:
    if not metrics:
        return ""
    parts = []
    for metric in metrics:
        name = getattr(metric, "name", None)
        score = getattr(metric, "score", None)
        threshold = getattr(metric, "threshold", None)
        passed = getattr(metric, "passed", None)
        if name is None:
            continue
        parts.append(f"{name}={score} (threshold={threshold}, passed={passed})")
    return ", ".join(parts)


def _build_run_documents(run) -> list[str]:
    documents: list[str] = []
    summary = run.to_summary_dict()
    documents.append("[RUN SUMMARY]\n" + json.dumps(summary, ensure_ascii=False))

    retrieval_meta = getattr(run, "retrieval_metadata", None)
    if retrieval_meta:
        documents.append("[RUN RETRIEVAL]\n" + json.dumps(retrieval_meta, ensure_ascii=False))

    for result in run.results:
        parts = ["[TEST CASE]"]
        if result.test_case_id:
            parts.append(f"test_case_id: {result.test_case_id}")
        if result.question:
            parts.append(f"question: {result.question}")
        if result.ground_truth:
            parts.append(f"ground_truth: {result.ground_truth}")
        if result.answer:
            parts.append(f"answer: {result.answer}")
        if result.prediction:
            parts.append(f"prediction: {result.prediction}")
        if result.contexts:
            parts.append("contexts:")
            parts.extend([f"- {ctx}" for ctx in result.contexts])
        metric_summary = _format_metrics(result.metrics)
        if metric_summary:
            parts.append(f"metrics: {metric_summary}")
        documents.append("\n".join(parts))

    return documents


def _upsert_documents(
    *,
    store: PgvectorStore,
    source: str,
    documents: list[str],
    embedding_func,
    batch_size: int,
):
    if not documents:
        return 0
    source_hash = _hash_text("\n\n".join(documents))
    existing_hash, existing_count = store.get_source_state(source=source)
    if existing_hash == source_hash and existing_count == len(documents):
        logger.info("Skipping %s (already indexed)", source)
        return 0
    embeddings = _embed_texts(documents, embedding_func, batch_size)
    store.replace_documents(
        source=source,
        source_hash=source_hash,
        documents=documents,
        embeddings=embeddings,
    )
    logger.info("Indexed %s (%d docs)", source, len(documents))
    return len(documents)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preindex USER_GUIDE and run results into pgvector"
    )
    parser.add_argument("--source-db", type=Path, default=None)
    parser.add_argument("--limit-runs", type=int, default=None)
    parser.add_argument("--user-guide-limit", type=int, default=20)
    parser.add_argument("--embedding-model", type=str, default="qwen3-embedding:8b")
    parser.add_argument("--matryoshka-dim", type=int, default=1024)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--skip-user-guide", action="store_true")
    parser.add_argument("--skip-runs", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    settings = Settings()

    conn_string = _build_conn_string(settings)
    store = PgvectorStore(conn_string)

    dimension, embedding_func = _embedding_func(
        settings=settings,
        embedding_model=args.embedding_model,
        matryoshka_dim=args.matryoshka_dim,
        batch_size=args.batch_size,
    )
    store.ensure_schema(dimension=dimension)

    total_docs = 0
    if not args.skip_user_guide:
        user_chunks = _build_user_guide_chunks(args.user_guide_limit)
        total_docs += _upsert_documents(
            store=store,
            source="user_guide",
            documents=user_chunks,
            embedding_func=embedding_func,
            batch_size=args.batch_size,
        )

    if not args.skip_runs:
        source_db = args.source_db or Path(settings.evalvault_db_path)
        storage = build_storage_adapter(db_path=source_db)
        offset = 0
        page_size = 200
        remaining = args.limit_runs
        while True:
            page_limit = page_size if remaining is None else min(page_size, remaining)
            if page_limit <= 0:
                break
            runs = storage.list_runs(limit=page_limit, offset=offset)
            if not runs:
                break
            for run in runs:
                docs = _build_run_documents(run)
                total_docs += _upsert_documents(
                    store=store,
                    source=f"run:{run.run_id}",
                    documents=docs,
                    embedding_func=embedding_func,
                    batch_size=args.batch_size,
                )
            offset += len(runs)
            if remaining is not None:
                remaining -= len(runs)

    logger.info("Total indexed documents: %d", total_docs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
