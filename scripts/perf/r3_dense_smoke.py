"""R3 dense retriever performance smoke test.

Log format (JSONL):
  - event: r3.smoke.index | r3.smoke.search | r3.smoke.summary
  - ts: unix epoch seconds (float)
  - run_id: unique identifier for this run
  - metrics: flat fields per event (see output)
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
import tracemalloc
from pathlib import Path
from typing import Any

import numpy as np

from evalvault.adapters.outbound.nlp.korean.dense_retriever import KoreanDenseRetriever

WORDS = [
    "insurance",
    "premium",
    "coverage",
    "policy",
    "benefit",
    "contract",
    "deductible",
    "claim",
    "risk",
    "term",
    "renewal",
    "payment",
    "document",
    "customer",
    "period",
    "limit",
    "provider",
    "product",
    "amount",
    "rate",
]


class _MockModel:
    """Fast deterministic embedding generator."""

    def __init__(self, dimension: int, seed: int) -> None:
        self._dimension = dimension
        self._rng = np.random.default_rng(seed)

    def encode(self, texts: list[str], **_kwargs: Any) -> np.ndarray:
        vectors = self._rng.random((len(texts), self._dimension))
        return vectors.astype(np.float32)


def _build_documents(
    count: int,
    min_words: int,
    max_words: int,
    seed: int,
) -> list[str]:
    rng = random.Random(seed)
    documents = []
    for idx in range(count):
        length = rng.randint(min_words, max_words)
        tokens = rng.choices(WORDS, k=length)
        documents.append(f"doc-{idx} " + " ".join(tokens))
    return documents


def _build_queries(count: int, min_words: int, max_words: int, seed: int) -> list[str]:
    rng = random.Random(seed + 999)
    queries = []
    for idx in range(count):
        length = rng.randint(min_words, max_words)
        tokens = rng.sample(WORDS, k=min(length, len(WORDS)))
        queries.append(f"query-{idx} " + " ".join(tokens))
    return queries


def _log_event(event: str, run_id: str, payload: dict[str, Any], sink: Any | None) -> None:
    record = {"event": event, "ts": time.time(), "run_id": run_id, **payload}
    line = json.dumps(record, ensure_ascii=True)
    print(line)
    if sink:
        sink.write(line + "\n")
        sink.flush()


def _configure_retriever(args: argparse.Namespace) -> tuple[KoreanDenseRetriever, str, bool]:
    retriever = KoreanDenseRetriever(
        model_name=args.model_name,
        profile=args.profile,
        device=args.device,
        batch_size=args.batch_size,
        use_faiss=args.use_faiss,
        faiss_use_gpu=args.faiss_use_gpu,
        query_cache_size=args.query_cache_size,
        search_cache_size=args.search_cache_size,
        normalize_embeddings=not args.disable_normalize,
    )

    embedding_mode = "real"
    fallback = False

    if args.mock_embeddings:
        retriever._model = _MockModel(args.embedding_dim, args.seed)
        retriever._model_type = "sentence-transformers"
        retriever._matryoshka_dim = args.embedding_dim
        embedding_mode = "mock"
        return retriever, embedding_mode, fallback

    try:
        retriever._load_model()
    except Exception:
        fallback = True
        retriever._model = _MockModel(args.embedding_dim, args.seed)
        retriever._model_type = "sentence-transformers"
        retriever._matryoshka_dim = args.embedding_dim
        embedding_mode = "mock"

    return retriever, embedding_mode, fallback


def _percentile(values: list[float], value: float) -> float:
    if not values:
        return 0.0
    return float(np.percentile(values, value))


def main() -> None:
    parser = argparse.ArgumentParser(description="R3 dense retriever smoke test.")
    parser.add_argument("--documents", type=int, default=1000)
    parser.add_argument("--queries", type=int, default=200)
    parser.add_argument("--min-words", type=int, default=80)
    parser.add_argument("--max-words", type=int, default=180)
    parser.add_argument("--query-min-words", type=int, default=3)
    parser.add_argument("--query-max-words", type=int, default=6)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model-name", type=str, default=None)
    parser.add_argument("--profile", type=str, default=None)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--use-faiss", action="store_true")
    parser.add_argument("--faiss-gpu", dest="faiss_use_gpu", action="store_true", default=None)
    parser.add_argument("--faiss-cpu", dest="faiss_use_gpu", action="store_false", default=None)
    parser.add_argument("--allow-omp-duplicate", action="store_true")
    parser.add_argument("--mock-embeddings", action="store_true")
    parser.add_argument("--embedding-dim", type=int, default=256)
    parser.add_argument("--query-cache-size", type=int, default=0)
    parser.add_argument("--search-cache-size", type=int, default=0)
    parser.add_argument("--disable-normalize", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if args.allow_omp_duplicate:
        os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

    run_id = f"r3-smoke-{int(time.time())}"
    sink = args.output.open("a", encoding="utf-8") if args.output else None

    documents = _build_documents(args.documents, args.min_words, args.max_words, args.seed)
    queries = _build_queries(args.queries, args.query_min_words, args.query_max_words, args.seed)

    retriever, embedding_mode, fallback = _configure_retriever(args)

    tracemalloc.start()
    index_start = time.perf_counter()
    retriever.index(documents)
    index_ms = (time.perf_counter() - index_start) * 1000
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    faiss_enabled = retriever._faiss_index is not None

    _log_event(
        "r3.smoke.index",
        run_id,
        {
            "documents": args.documents,
            "index_ms": round(index_ms, 3),
            "index_build_time_ms": round(index_ms, 3),
            "index_docs_per_sec": round(args.documents / (index_ms / 1000), 3),
            "memory_peak_mb": round(peak / (1024 * 1024), 3),
            "memory_source": "tracemalloc",
            "embedding_mode": embedding_mode,
            "embedding_fallback": fallback,
            "embedding_model": retriever.model_name,
            "embedding_dim": retriever.dimension,
            "device": args.device,
            "batch_size": args.batch_size,
            "use_faiss": args.use_faiss,
            "faiss_enabled": faiss_enabled,
            "faiss_gpu": args.faiss_use_gpu,
            "faiss_gpu_active": retriever.faiss_gpu_active,
            "normalize_embeddings": not args.disable_normalize,
            "query_cache_size": args.query_cache_size,
            "search_cache_size": args.search_cache_size,
            "index_size": args.documents,
        },
        sink,
    )

    latencies_ms: list[float] = []
    search_start = time.perf_counter()
    for query in queries:
        t0 = time.perf_counter()
        retriever.search(query, top_k=args.top_k)
        latencies_ms.append((time.perf_counter() - t0) * 1000)
    total_search_ms = (time.perf_counter() - search_start) * 1000

    _log_event(
        "r3.smoke.search",
        run_id,
        {
            "queries": args.queries,
            "top_k": args.top_k,
            "search_total_ms": round(total_search_ms, 3),
            "search_qps": round(args.queries / (total_search_ms / 1000), 3),
            "search_ms_p50": round(_percentile(latencies_ms, 50), 3),
            "search_ms_p95": round(_percentile(latencies_ms, 95), 3),
            "search_ms_p99": round(_percentile(latencies_ms, 99), 3),
            "search_ms_mean": round(float(np.mean(latencies_ms)), 3),
            "search_ms_min": round(float(min(latencies_ms)), 3),
            "search_ms_max": round(float(max(latencies_ms)), 3),
            "total_docs_searched": args.documents,
        },
        sink,
    )

    _log_event(
        "r3.smoke.summary",
        run_id,
        {
            "documents": args.documents,
            "queries": args.queries,
            "index_ms": round(index_ms, 3),
            "search_total_ms": round(total_search_ms, 3),
            "search_ms_p95": round(_percentile(latencies_ms, 95), 3),
            "memory_peak_mb": round(peak / (1024 * 1024), 3),
            "faiss_enabled": faiss_enabled,
            "embedding_mode": embedding_mode,
        },
        sink,
    )

    if sink:
        sink.close()


if __name__ == "__main__":
    main()
