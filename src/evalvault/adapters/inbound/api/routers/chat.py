from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["chat"])

logger = logging.getLogger(__name__)

MCP_URL = os.getenv("EVALVAULT_MCP_URL", "http://localhost:8000/api/v1/mcp")
MCP_TOKEN = os.getenv("EVALVAULT_MCP_TOKEN", "mcp-local-dev-token")

USER_GUIDE_PATH = Path(os.getenv("EVALVAULT_RAG_USER_GUIDE", "docs/guides/USER_GUIDE.md"))
RAG_INDEX_DIR = Path(os.getenv("EVALVAULT_RAG_INDEX_DIR", "data/rag"))
RAG_INDEX_PATH = RAG_INDEX_DIR / "user_guide_bm25.json"

_RAG_RETRIEVER = None
_RAG_DOCS_COUNT = 0
_RAG_TEXTS: list[str] = []
_RAG_INITIALIZED = False


@dataclass(frozen=True)
class _RagHit:
    document: str
    score: float
    doc_id: int


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[ChatMessage] | None = None


class AiChatMessage(BaseModel):
    role: str
    content: str | None = None
    parts: list[dict[str, Any]] | None = None


class AiChatRequest(BaseModel):
    messages: list[AiChatMessage] = Field(default_factory=list)
    run_id: str | None = None
    category: str | None = None


def _extract_run_ids(text: str) -> list[str]:
    return re.findall(r"run_[A-Za-z0-9_-]+", text)


def _ollama_chat_options(model_name: str) -> dict[str, Any] | None:
    lower = model_name.lower()
    if lower.startswith("qwen3"):
        return {
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "repeat_penalty": 1,
            "stop": ["<|im_start|>", "<|im_end|>"],
        }
    return None


def _is_verb_only(text: str) -> bool:
    if not text:
        return False
    compact = re.sub(r"\s+", "", text.strip())
    if not compact:
        return False
    tokens = re.findall(r"[A-Za-z0-9가-힣]+", compact)
    if len(tokens) > 2:
        return False
    verb_markers = ["해줘", "해주세요", "해봐", "해봐요", "해줘요", "해줘라"]
    verb_stems = ["설명", "요약", "분석", "비교", "개선", "정리", "추천", "진단", "해석", "검증"]
    if any(compact.endswith(marker) for marker in verb_markers):
        return any(stem in compact for stem in verb_stems)
    return compact in verb_stems


def _with_context(user_text: str, run_id: str | None, category: str | None) -> str:
    parts = []
    if run_id:
        parts.append(f"선택된 run_id: {run_id}")
    if category:
        parts.append(f"질문 분류: {category}")
    if not parts:
        return user_text
    return "\n".join(parts) + f"\n사용자 요청: {user_text}"


def _format_tool_result(result: Any) -> str:
    if isinstance(result, dict):
        if "result" in result:
            return str(result["result"])
        if "error" in result:
            return f"오류: {result['error']}"
    return str(result)


def _summarize_runs(payload: dict[str, Any]) -> str:
    runs = payload.get("runs") or []
    if not runs:
        return "실행 기록이 없습니다."
    lines = ["최근 실행 목록:"]
    for run in runs[:10]:
        lines.append(
            "- {run_id} | {dataset} | {model} | pass={pass_rate:.2f}".format(
                run_id=run.get("run_id"),
                dataset=run.get("dataset_name"),
                model=run.get("model_name"),
                pass_rate=run.get("pass_rate", 0.0),
            )
        )
    return "\n".join(lines)


def _summarize_run_summary(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    if not summary:
        return "요약 정보를 찾지 못했습니다."
    return (
        "요약: {run_id}\n"
        "- dataset: {dataset}\n"
        "- model: {model}\n"
        "- pass_rate: {pass_rate:.2f}\n"
        "- total: {total} / passed: {passed}\n"
        "- metrics: {metrics}".format(
            run_id=summary.get("run_id"),
            dataset=summary.get("dataset_name"),
            model=summary.get("model_name"),
            pass_rate=summary.get("pass_rate", 0.0),
            total=summary.get("total_test_cases"),
            passed=summary.get("passed_test_cases"),
            metrics=", ".join(summary.get("metrics_evaluated", []) or []),
        )
    )


def _summarize_compare(payload: dict[str, Any]) -> str:
    baseline = payload.get("baseline_run_id")
    candidate = payload.get("candidate_run_id")
    delta = payload.get("metrics_delta") or {}
    avg = delta.get("avg") or {}
    lines = [
        f"비교 결과: {baseline} vs {candidate}",
        "평균 변화:",
    ]
    for metric, value in avg.items():
        lines.append(f"- {metric}: {value:+.4f}")
    notes = delta.get("notes") or []
    if notes:
        lines.append("노트: " + "; ".join(notes))
    return "\n".join(lines)


def _summarize_artifacts(payload: dict[str, Any]) -> str:
    artifacts = payload.get("artifacts") or {}
    if not artifacts:
        return "아티팩트 경로를 찾지 못했습니다."
    return (
        "아티팩트:\n"
        f"- kind: {artifacts.get('kind')}\n"
        f"- report: {artifacts.get('report_path')}\n"
        f"- output: {artifacts.get('output_path')}\n"
        f"- dir: {artifacts.get('artifacts_dir')}"
    )


def _summarize_result(tool_name: str, payload: dict[str, Any]) -> str:
    if tool_name == "list_runs":
        return _summarize_runs(payload)
    if tool_name == "get_run_summary":
        return _summarize_run_summary(payload)
    if tool_name == "analyze_compare":
        return _summarize_compare(payload)
    if tool_name == "get_artifacts":
        return _summarize_artifacts(payload)
    return str(payload)


def _load_user_guide_text() -> str | None:
    if not USER_GUIDE_PATH.exists():
        logger.warning("USER_GUIDE.md not found at %s", USER_GUIDE_PATH)
        return None
    try:
        content = USER_GUIDE_PATH.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Failed to read USER_GUIDE.md: %s", exc)
        return None
    if not content.strip():
        return None
    return content


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _chunk_user_guide(content: str, chunk_limit: int) -> list[str]:
    try:
        from evalvault.adapters.outbound.nlp.korean.document_chunker import ParagraphChunker
        from evalvault.adapters.outbound.nlp.korean.kiwi_tokenizer import KiwiTokenizer

        tokenizer = KiwiTokenizer()
        chunker = ParagraphChunker(tokenizer=tokenizer, chunk_size=450, overlap_tokens=80)
        chunks = [
            chunk.text
            for chunk in chunker.chunk_with_metadata(content, source=str(USER_GUIDE_PATH))
        ]
        if chunk_limit > 0:
            return chunks[:chunk_limit]
        return chunks
    except Exception as exc:
        logger.warning("Failed to chunk USER_GUIDE.md, using fallback split: %s", exc)
        paragraphs = [block.strip() for block in content.split("\n\n") if block.strip()]
        if chunk_limit > 0:
            return paragraphs[:chunk_limit]
        return paragraphs


def _build_bm25_tokens(texts: list[str]) -> list[list[str]]:
    try:
        from evalvault.adapters.outbound.nlp.korean.kiwi_tokenizer import KiwiTokenizer

        tokenizer = KiwiTokenizer()
        tokens = []
        for text in texts:
            doc_tokens = tokenizer.tokenize(text)
            if not doc_tokens:
                doc_tokens = re.findall(r"[A-Za-z0-9가-힣]+", text)
            tokens.append(doc_tokens)
        return tokens
    except Exception as exc:
        logger.warning("Failed to tokenize with Kiwi, using regex: %s", exc)
        return [re.findall(r"[A-Za-z0-9가-힣]+", text) for text in texts]


def _load_bm25_index() -> dict[str, Any] | None:
    if not RAG_INDEX_PATH.exists():
        return None
    try:
        payload = json.loads(RAG_INDEX_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to read BM25 index: %s", exc)
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _save_bm25_index(payload: dict[str, Any]) -> None:
    RAG_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    RAG_INDEX_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_bm25_index(content: str, chunk_limit: int) -> dict[str, Any] | None:
    chunks = _chunk_user_guide(content, chunk_limit)
    if not chunks:
        return None
    tokens = _build_bm25_tokens(chunks)
    return {
        "version": 1,
        "source": str(USER_GUIDE_PATH),
        "source_hash": _hash_text(content),
        "chunk_limit": chunk_limit,
        "created_at": datetime.now(UTC).isoformat(),
        "documents": chunks,
        "tokens": tokens,
    }


async def _get_rag_retriever() -> tuple[Any | None, int]:
    global _RAG_RETRIEVER
    global _RAG_DOCS_COUNT
    global _RAG_TEXTS
    global _RAG_INITIALIZED

    if _RAG_RETRIEVER is not None:
        return _RAG_RETRIEVER, _RAG_DOCS_COUNT

    user_guide_limit = int(os.getenv("EVALVAULT_RAG_USER_GUIDE_LIMIT", "80"))
    content = _load_user_guide_text()
    if content is None:
        return None, 0
    source_hash = _hash_text(content)

    index_payload = _load_bm25_index()
    if index_payload is None or index_payload.get("source_hash") != source_hash:
        index_payload = _build_bm25_index(content, user_guide_limit)
        if index_payload is None:
            return None, 0
        _save_bm25_index(index_payload)

    documents = index_payload.get("documents")
    tokens = index_payload.get("tokens")
    if not isinstance(documents, list) or not isinstance(tokens, list):
        return None, 0

    _RAG_TEXTS = documents
    _RAG_DOCS_COUNT = len(documents)
    _RAG_INITIALIZED = True

    if not _RAG_TEXTS:
        return None, 0

    from evalvault.adapters.outbound.nlp.korean.toolkit import KoreanNLPToolkit

    use_hybrid = os.getenv("EVALVAULT_RAG_USE_HYBRID", "true").lower() == "true"
    embedding_profile = os.getenv("EVALVAULT_RAG_EMBEDDING_PROFILE", "dev")
    vector_store = os.getenv("EVALVAULT_RAG_VECTOR_STORE", "pgvector").lower()
    pgvector_index = os.getenv("EVALVAULT_RAG_PGVECTOR_INDEX", "hnsw").lower()
    pgvector_index_lists = int(os.getenv("EVALVAULT_RAG_PGVECTOR_INDEX_LISTS", "100"))
    pgvector_hnsw_m = int(os.getenv("EVALVAULT_RAG_PGVECTOR_HNSW_M", "16"))
    pgvector_hnsw_ef = int(os.getenv("EVALVAULT_RAG_PGVECTOR_HNSW_EF_CONSTRUCTION", "64"))

    def _build_conn_string() -> str | None:
        try:
            from evalvault.config.settings import Settings

            settings = Settings()
            if settings.postgres_connection_string:
                return settings.postgres_connection_string
            if settings.postgres_host:
                return "host={host} port={port} dbname={dbname} user={user} password={password}".format(
                    host=settings.postgres_host,
                    port=settings.postgres_port,
                    dbname=settings.postgres_database,
                    user=settings.postgres_user or "postgres",
                    password=settings.postgres_password or "",
                )
        except Exception as exc:
            logger.warning("Failed to build Postgres connection string: %s", exc)
        return None

    ollama_adapter = None
    dense_retriever = None
    embedding_func = None
    if embedding_profile:
        try:
            from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter
            from evalvault.adapters.outbound.nlp.korean.dense_retriever import KoreanDenseRetriever
            from evalvault.config.settings import Settings

            settings = Settings()
            ollama_adapter = OllamaAdapter(settings)
            dense_retriever = KoreanDenseRetriever(
                profile=embedding_profile,
                ollama_adapter=ollama_adapter,
            )
            embedding_func = dense_retriever.get_embedding_func()
        except Exception as exc:  # pragma: no cover - runtime dependency
            logger.warning("Failed to initialize dense retriever: %s", exc)

    if vector_store == "pgvector" and embedding_func is not None:
        conn_string = _build_conn_string()
        if conn_string:
            try:
                from evalvault.adapters.outbound.nlp.korean.bm25_retriever import (
                    KoreanBM25Retriever,
                )
                from evalvault.adapters.outbound.nlp.korean.kiwi_tokenizer import KiwiTokenizer
                from evalvault.adapters.outbound.retriever.pgvector_store import PgvectorStore

                store = PgvectorStore(
                    conn_string,
                    index_type=pgvector_index,
                    index_lists=pgvector_index_lists,
                    hnsw_m=pgvector_hnsw_m,
                    hnsw_ef_construction=pgvector_hnsw_ef,
                )
                embedding_dim = (
                    dense_retriever.dimension if dense_retriever else len(embedding_func(["x"])[0])
                )
                store.ensure_schema(dimension=embedding_dim)
                source_hash = _hash_text(content)
                existing_hash, existing_count = store.get_source_state(source="user_guide")
                if existing_hash != source_hash or existing_count != len(_RAG_TEXTS):
                    embeddings = embedding_func(list(_RAG_TEXTS))
                    store.replace_documents(
                        source="user_guide",
                        source_hash=source_hash,
                        documents=list(_RAG_TEXTS),
                        embeddings=embeddings,
                    )

                tokenizer = KiwiTokenizer()
                bm25_retriever = KoreanBM25Retriever(tokenizer=tokenizer)
                bm25_retriever.index(list(_RAG_TEXTS))
                if tokens and len(tokens) == len(_RAG_TEXTS):
                    bm25_retriever._tokenized_docs = tokens

                if use_hybrid:
                    retriever = _PgvectorHybridRetriever(
                        bm25_retriever=bm25_retriever,
                        store=store,
                        embedding_func=embedding_func,
                        documents=list(_RAG_TEXTS),
                    )
                else:
                    retriever = _PgvectorDenseRetriever(
                        store=store,
                        embedding_func=embedding_func,
                        documents=list(_RAG_TEXTS),
                    )

                _RAG_RETRIEVER = retriever
                return retriever, _RAG_DOCS_COUNT
            except Exception as exc:
                logger.warning("pgvector retriever setup failed: %s", exc)

    toolkit = KoreanNLPToolkit()
    retriever = toolkit.build_retriever(
        list(_RAG_TEXTS),
        use_hybrid=use_hybrid,
        ollama_adapter=ollama_adapter,
        embedding_profile=embedding_profile,
        verbose=True,
    )
    if retriever is None:
        return None, 0

    _RAG_RETRIEVER = retriever
    return retriever, _RAG_DOCS_COUNT


async def warm_rag_index() -> None:
    try:
        await _get_rag_retriever()
    except Exception as exc:
        logger.warning("RAG preload failed: %s", exc)


async def _direct_chat_answer(
    user_text: str, run_id: str | None = None, category: str | None = None
) -> str | None:
    user_text = _with_context(user_text, run_id, category)
    model_name = os.getenv("OLLAMA_CHAT_MODEL", "qwen3:14b")
    options = _ollama_chat_options(model_name)
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant for EvalVault. "
                    "Interpret verb-only requests as questions about the selected run/category. "
                    "If essential details are missing, ask a concise follow-up question in Korean."
                ),
            },
            {"role": "user", "content": user_text},
        ],
        "stream": False,
    }
    if options:
        payload["options"] = options

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    return data.get("message", {}).get("content", "").strip() or None


def _simple_retrieve(texts: list[str], query: str, top_k: int) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9가-힣]+", query.lower())
    if not tokens:
        return []
    scored: list[tuple[int, str]] = []
    for text in texts:
        hay = text.lower()
        score = sum(hay.count(token) for token in tokens)
        if score:
            scored.append((score, text))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [text for _, text in scored[:top_k]]


def _rrf_fuse(
    *,
    bm25_results: list[Any],
    dense_results: list[Any],
    documents: list[str],
    top_k: int,
    bm25_weight: float = 0.4,
    dense_weight: float = 0.6,
    rrf_k: int = 60,
) -> list[_RagHit]:
    scores: dict[int, float] = {}

    for rank, result in enumerate(bm25_results, 1):
        doc_id = int(result.doc_id)
        scores[doc_id] = scores.get(doc_id, 0.0) + (bm25_weight / (rrf_k + rank))

    for rank, result in enumerate(dense_results, 1):
        doc_id = int(result.doc_id)
        scores[doc_id] = scores.get(doc_id, 0.0) + (dense_weight / (rrf_k + rank))

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    hits: list[_RagHit] = []
    for doc_id, score in ranked[:top_k]:
        if 0 <= doc_id < len(documents):
            hits.append(_RagHit(document=documents[doc_id], score=score, doc_id=doc_id))
    return hits


class _PgvectorDenseRetriever:
    def __init__(self, store: Any, embedding_func: Any, documents: list[str]) -> None:
        self._store = store
        self._embedding_func = embedding_func
        self._documents = documents

    def search(self, query: str, top_k: int = 5) -> list[_RagHit]:
        query_embedding = self._embedding_func([query])[0]
        results = self._store.search(
            source="user_guide", query_embedding=query_embedding, top_k=top_k
        )
        hits: list[_RagHit] = []
        for result in results:
            if 0 <= result.doc_id < len(self._documents):
                hits.append(
                    _RagHit(
                        document=self._documents[result.doc_id],
                        score=float(result.score),
                        doc_id=result.doc_id,
                    )
                )
        return hits


class _PgvectorHybridRetriever:
    def __init__(
        self,
        *,
        bm25_retriever: Any,
        store: Any,
        embedding_func: Any,
        documents: list[str],
    ) -> None:
        self._bm25 = bm25_retriever
        self._store = store
        self._embedding_func = embedding_func
        self._documents = documents

    def search(self, query: str, top_k: int = 5) -> list[_RagHit]:
        bm25_results = self._bm25.search(query, top_k=len(self._documents))
        query_embedding = self._embedding_func([query])[0]
        dense_results = self._store.search(
            source="user_guide", query_embedding=query_embedding, top_k=len(self._documents)
        )
        dense_results = sorted(dense_results, key=lambda item: item.score)
        return _rrf_fuse(
            bm25_results=bm25_results,
            dense_results=dense_results,
            documents=self._documents,
            top_k=top_k,
        )


def _read_text_limited(path: Path, limit: int = 4000) -> str | None:
    try:
        if not path.exists():
            return None
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        logger.warning("Failed to read %s: %s", path, exc)
        return None
    content = content.strip()
    if not content:
        return None
    if len(content) > limit:
        return content[:limit] + "..."
    return content


async def _build_run_context(run_id: str) -> list[str]:
    contexts: list[str] = []
    try:
        summary_result = await _call_mcp_tool("get_run_summary", {"run_id": run_id})
        payload = _extract_json_content(summary_result)
        if isinstance(payload, dict):
            contexts.append("[RUN 요약]\n" + _summarize_run_summary(payload))
    except Exception as exc:
        logger.warning("Failed to fetch run summary: %s", exc)

    try:
        artifacts_result = await _call_mcp_tool(
            "get_artifacts", {"run_id": run_id, "kind": "analysis"}
        )
        payload = _extract_json_content(artifacts_result)
        if isinstance(payload, dict):
            contexts.append("[RUN 아티팩트]\n" + _summarize_artifacts(payload))
            artifacts = payload.get("artifacts") or {}
            report_path = artifacts.get("report_path")
            if isinstance(report_path, str) and report_path:
                report_text = _read_text_limited(Path(report_path))
                if report_text:
                    contexts.append("[REPORT 발췌]\n" + report_text)
    except Exception as exc:
        logger.warning("Failed to fetch run artifacts: %s", exc)

    return contexts


async def _rag_answer(
    user_text: str, run_id: str | None = None, category: str | None = None
) -> str | None:
    contexts: list[str] = []
    rag_llm_enabled = os.getenv("EVALVAULT_RAG_LLM_ENABLED", "true").lower() == "true"
    run_context_enabled = os.getenv("EVALVAULT_CHAT_RUN_CONTEXT_ENABLED", "true").lower() == "true"

    if run_id and rag_llm_enabled and run_context_enabled:
        contexts.extend(await _build_run_context(run_id))

    if not rag_llm_enabled and contexts:
        return "\n\n".join(contexts[:3])

    if not rag_llm_enabled:
        content = _load_user_guide_text()
        if content:
            chunks = [chunk.strip() for chunk in content.split("\n\n") if chunk.strip()]
            contexts.extend(_simple_retrieve(chunks, user_text, top_k=5))
        return "\n\n".join(contexts[:3]) if contexts else None

    retriever, _ = await _get_rag_retriever()

    if retriever is not None:
        results = retriever.search(user_text, top_k=5)
        for item in results:
            context = getattr(item, "document", None)
            if context:
                contexts.append(context)

    if not contexts and _RAG_TEXTS:
        contexts = _simple_retrieve(_RAG_TEXTS, user_text, top_k=5)

    if not contexts:
        return None

    if not rag_llm_enabled:
        return "\n\n".join(contexts[:3])

    prompt = (
        "다음은 EvalVault 코드/문서에서 검색된 컨텍스트입니다.\n"
        "컨텍스트만 근거로 사용해 한국어로 답하세요.\n"
        "질문이 동사만 있는 경우에도 선택된 run_id/분류를 기준으로 해석하세요.\n"
        "정보가 부족하면 먼저 필요한 정보를 질문하세요.\n\n"
        "[컨텍스트]\n"
        + "\n\n---\n\n".join(contexts[:3])
        + "\n\n[질문]\n"
        + _with_context(user_text, run_id, category)
        + "\n\n[답변]"
    )

    model_name = os.getenv("OLLAMA_CHAT_MODEL", "qwen3:14b")
    options = _ollama_chat_options(model_name)
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for EvalVault."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }
    if options:
        payload["options"] = options

    fallback = "\n\n".join(contexts[:3])
    chat_timeout = int(os.getenv("OLLAMA_CHAT_TIMEOUT_SECONDS", "180"))
    try:
        async with httpx.AsyncClient(timeout=chat_timeout) as client:
            response = await client.post(
                f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.ReadTimeout:
        logger.warning("Ollama chat timed out; returning retrieved contexts")
        return fallback or None
    except httpx.HTTPError as exc:
        logger.warning("Ollama chat failed: %s", exc)
        return fallback or None

    return data.get("message", {}).get("content", "").strip() or fallback or None


async def _call_mcp_tool(tool_name: str, tool_args: dict[str, Any]) -> Any:
    headers = {
        "Authorization": f"Bearer {MCP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": tool_args},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(MCP_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    return data


async def _resolve_tool_with_llm(
    user_text: str, run_id: str | None = None, category: str | None = None
) -> dict[str, Any] | None:
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    router_model = os.getenv("OLLAMA_ROUTER_MODEL", "gemma3:1b")

    system_prompt = (
        "You are a router for EvalVault. "
        "Return JSON only with keys: action, tool, arguments."
        "Action must be one of: tool, rag, direct."
        "Tools: list_runs, get_run_summary, run_evaluation, analyze_compare, get_artifacts."
        "Rules:"
        "- Assume verb-only requests refer to the selected run_id/category when provided."
        "- If essential info is missing (e.g., run_id), return action direct with a follow-up question."
        "- If user asks about datasets, prefer tool list_datasets."
        "- If question is about EvalVault docs/usage, prefer rag."
        "- If greeting or general chat, use direct."
        "- For tool list_runs: arguments {limit:int}"
        "- For tool get_run_summary: {run_id:string}"
        "- For tool analyze_compare: {run_id_a:string, run_id_b:string}"
        "- For tool run_evaluation: {dataset_path:string, metrics:[string], profile:string, auto_analyze:bool}"
        "- For tool get_artifacts: {run_id:string, kind:'analysis'|'comparison'}"
        "- For tool list_datasets: {limit:int}"
    )

    payload = {
        "model": router_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": _with_context(user_text, run_id, category)},
        ],
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{ollama_url}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()

    content = data.get("message", {}).get("content", "").strip()
    if not content:
        return None

    try:
        return json.loads(content)
    except Exception:
        return None


def _extract_json_content(result: Any) -> dict[str, Any] | None:
    if isinstance(result, dict):
        structured = result.get("structuredContent")
        if isinstance(structured, dict):
            return structured
    else:
        if hasattr(result, "structuredContent"):
            payload = result.structuredContent
            if isinstance(payload, dict):
                return payload

    if not isinstance(result, dict) and hasattr(result, "content"):
        content = result.content
    elif isinstance(result, dict):
        content = result.get("content")
    else:
        content = None

    if not isinstance(content, list):
        return None

    for item in content:
        if isinstance(item, dict):
            item_type = item.get("type")
            if item_type == "json":
                payload = item.get("json")
                if isinstance(payload, dict):
                    return payload
            if item_type == "text":
                text = item.get("text")
                if isinstance(text, str):
                    try:
                        parsed = json.loads(text)
                    except Exception:
                        return None
                    if isinstance(parsed, dict):
                        return parsed
    return None


def _chunk_text(text: str, size: int = 42) -> list[str]:
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


def _extract_text_from_parts(parts: list[dict[str, Any]] | None) -> str | None:
    if not parts:
        return None
    chunks: list[str] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        if part.get("type") == "text":
            text = part.get("text")
            if isinstance(text, str) and text:
                chunks.append(text)
    if not chunks:
        return None
    content = "".join(chunks).strip()
    return content or None


def _extract_last_user_message(messages: list[AiChatMessage]) -> str | None:
    for message in reversed(messages):
        if message.role != "user":
            continue
        if message.content and message.content.strip():
            return message.content.strip()
        content = _extract_text_from_parts(message.parts)
        if content:
            return content
    return None


def _ai_sse_event(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _ai_sse_done() -> str:
    return "data: [DONE]\n\n"


def _ai_sse_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "x-vercel-ai-ui-message-stream": "v1",
    }


async def _ai_chat_stream(
    user_text: str, run_id: str | None = None, category: str | None = None
) -> AsyncGenerator[str, None]:
    message_id = f"msg_{int(time.time() * 1000)}"
    text_id = f"text_{message_id}"
    yield _ai_sse_event({"type": "start", "messageId": message_id})
    yield _ai_sse_event({"type": "text-start", "id": text_id})

    async for item in _chat_stream(user_text, run_id=run_id, category=category):
        raw = item.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            continue

        event_type = payload.get("type")
        if event_type == "delta":
            content = payload.get("content")
            if isinstance(content, str) and content:
                yield _ai_sse_event({"type": "text-delta", "id": text_id, "delta": content})
            continue
        if event_type == "status":
            message = payload.get("message")
            if isinstance(message, str) and message:
                yield _ai_sse_event(
                    {"type": "data-status", "data": {"message": message}, "transient": True}
                )
            continue
        if event_type == "error":
            message = payload.get("message")
            if not isinstance(message, str) or not message:
                message = "채팅 요청에 실패했습니다."
            yield _ai_sse_event({"type": "error", "errorText": message})
            yield _ai_sse_event({"type": "finish"})
            yield _ai_sse_done()
            return
        if event_type == "final":
            yield _ai_sse_event({"type": "text-end", "id": text_id})
            yield _ai_sse_event({"type": "finish"})
            yield _ai_sse_done()
            return

    yield _ai_sse_event({"type": "finish"})
    yield _ai_sse_done()


def _event(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False) + "\n"


async def _emit_answer(answer: str) -> AsyncGenerator[str, None]:
    for chunk in _chunk_text(answer):
        yield _event({"type": "delta", "content": chunk})
        await asyncio.sleep(0)
    yield _event({"type": "final", "content": answer})


async def _chat_stream(
    user_text: str, run_id: str | None = None, category: str | None = None
) -> AsyncGenerator[str, None]:
    started_at = time.perf_counter()
    simple_mode = os.getenv("EVALVAULT_CHAT_SIMPLE_MODE", "false").lower() == "true"
    run_context_enabled = os.getenv("EVALVAULT_CHAT_RUN_CONTEXT_ENABLED", "true").lower() == "true"
    if simple_mode:
        yield _event({"type": "status", "message": "간단 채팅 처리 중..."})
        answer = await _direct_chat_answer(user_text)
        if answer:
            async for item in _emit_answer(answer):
                yield item
        else:
            yield _event({"type": "final", "content": "답변을 생성하지 못했습니다."})
        return
    if category in {"result_interpretation", "improvement_direction"} and not run_id:
        yield _event(
            {
                "type": "final",
                "content": "선택한 분류는 run_id가 필요합니다. run_id를 선택한 뒤 다시 질문해주세요.",
            }
        )
        return

    if len(user_text) <= 4:
        if run_id or category:
            user_text = f"{user_text}"
        else:
            yield _event(
                {
                    "type": "final",
                    "content": "무엇을 설명할까요? run_id와 질문 분류를 선택한 뒤 다시 요청해주세요.",
                }
            )
            return

    if len(user_text) <= 6 and not _is_verb_only(user_text):
        yield _event({"type": "status", "message": "짧은 질문 처리 중..."})
        answer = await _direct_chat_answer(user_text, run_id=run_id, category=category)
        if answer:
            async for item in _emit_answer(answer):
                yield item
        else:
            yield _event({"type": "final", "content": "답변을 생성하지 못했습니다."})
        return

    if (
        _is_verb_only(user_text)
        and category in {"result_interpretation", "improvement_direction"}
        and run_id
        and run_context_enabled
    ):
        yield _event({"type": "status", "message": "선택한 run 요약 중..."})
        try:
            result = await asyncio.wait_for(
                _call_mcp_tool("get_run_summary", {"run_id": run_id}), timeout=12
            )
        except TimeoutError:
            yield _event(
                {
                    "type": "error",
                    "message": "run 요약 응답이 지연됩니다. 잠시 후 다시 시도해주세요.",
                }
            )
            return
        except Exception as exc:
            yield _event({"type": "error", "message": f"run 요약 실패: {exc}"})
            return

        payload = _extract_json_content(result)
        if isinstance(payload, dict):
            summary = _summarize_result("get_run_summary", payload)
            if category == "improvement_direction":
                summary += "\n\n개선 방향을 구체화하려면 목표 메트릭이나 기준을 알려주세요."
            else:
                summary += "\n\n특정 메트릭/케이스가 있으면 알려주세요."
            async for item in _emit_answer(summary):
                yield item
            return

    yield _event({"type": "status", "message": "요청 분류 중..."})
    try:
        router = await asyncio.wait_for(
            _resolve_tool_with_llm(user_text, run_id=run_id, category=category),
            timeout=30,
        )
    except TimeoutError:
        router = None
    except Exception:
        router = None

    if not isinstance(router, dict):
        router = None

    if router is None:
        yield _event({"type": "status", "message": "문서 검색 중..."})
        try:
            rag_answer = await asyncio.wait_for(
                _rag_answer(user_text, run_id=run_id, category=category), timeout=90
            )
        except TimeoutError:
            yield _event({"type": "error", "message": "문서 검색이 지연됩니다. 다시 시도해주세요."})
            return
        if rag_answer:
            async for item in _emit_answer(rag_answer):
                yield item
            return
        answer = await _direct_chat_answer(user_text, run_id=run_id, category=category)
        if answer:
            async for item in _emit_answer(answer):
                yield item
            return
        yield _event({"type": "final", "content": "요청을 해석하지 못했습니다. 다시 질문해주세요."})
        return

    action = router.get("action")
    tool_name = router.get("tool")
    tool_args = router.get("arguments", {})

    if action == "direct":
        answer = await _direct_chat_answer(user_text, run_id=run_id, category=category)
        if answer:
            async for item in _emit_answer(answer):
                yield item
        else:
            yield _event({"type": "final", "content": "답변을 생성하지 못했습니다."})
        return

    if action == "rag":
        yield _event({"type": "status", "message": "문서 검색 중..."})
        try:
            rag_answer = await asyncio.wait_for(
                _rag_answer(user_text, run_id=run_id, category=category), timeout=90
            )
        except TimeoutError:
            yield _event({"type": "error", "message": "문서 검색이 지연됩니다. 다시 시도해주세요."})
            return
        if rag_answer:
            async for item in _emit_answer(rag_answer):
                yield item
        else:
            yield _event({"type": "final", "content": "관련 문서를 찾지 못했습니다."})
        return

    if action != "tool":
        yield _event({"type": "final", "content": "요청을 해석하지 못했습니다. 다시 질문해주세요."})
        return

    if not tool_name:
        yield _event({"type": "final", "content": "도구 이름을 찾지 못했습니다."})
        return

    if tool_name == "get_run_summary" and not (tool_args.get("run_id") or run_id):
        yield _event({"type": "final", "content": "run_id를 선택하거나 입력해주세요."})
        return
    if tool_name == "get_artifacts" and not (tool_args.get("run_id") or run_id):
        yield _event({"type": "final", "content": "아티팩트 조회를 위해 run_id가 필요합니다."})
        return
    if not run_context_enabled and tool_name in {"get_run_summary", "get_artifacts"}:
        yield _event(
            {
                "type": "final",
                "content": "run 요약/아티팩트 조회가 비활성화되어 있습니다.",
            }
        )
        return
    if tool_name == "analyze_compare" and (
        not tool_args.get("run_id_a") or not tool_args.get("run_id_b")
    ):
        yield _event(
            {
                "type": "final",
                "content": "비교 분석에는 run_id 두 개가 필요합니다. 비교할 run을 알려주세요.",
            }
        )
        return

    yield _event({"type": "status", "message": "도구 실행 중..."})
    try:
        enhanced_tool_args = dict(tool_args)
        if run_id:
            enhanced_tool_args["run_id"] = run_id
        if category:
            enhanced_tool_args["category"] = category
        result = await asyncio.wait_for(_call_mcp_tool(tool_name, enhanced_tool_args), timeout=12)
    except TimeoutError:
        yield _event(
            {"type": "error", "message": "응답 지연(12s 초과). MCP 서버 상태를 확인해주세요."}
        )
        return
    except Exception as exc:
        yield _event({"type": "error", "message": f"도구 호출 실패: {exc}"})
        return

    payload = _extract_json_content(result)
    if isinstance(payload, dict):
        summary = _summarize_result(tool_name, payload)
        async for item in _emit_answer(summary):
            yield item
        return

    if hasattr(result, "content"):
        text = _format_tool_result(result.content)
    else:
        text = f"도구 실행 결과: {_format_tool_result(result)}"
    async for item in _emit_answer(text):
        yield item

    elapsed_ms = (time.perf_counter() - started_at) * 1000
    yield _event({"type": "status", "message": f"처리 완료 ({elapsed_ms:.0f}ms)"})


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    user_text = request.message.strip()
    if not user_text:
        return StreamingResponse(
            iter([_event({"type": "error", "message": "질문을 입력해주세요."})]),
            media_type="application/x-ndjson",
        )

    async def event_generator():
        async for item in _chat_stream(user_text):
            yield item

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@router.post("/ai-stream")
async def ai_chat_stream(request: AiChatRequest):
    user_text = _extract_last_user_message(request.messages)
    run_id = request.run_id
    category = request.category
    if not user_text:

        async def error_generator():
            yield _ai_sse_event({"type": "error", "errorText": "질문을 입력해주세요."})
            yield _ai_sse_event({"type": "finish"})
            yield _ai_sse_done()

        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            headers=_ai_sse_headers(),
        )

    async def event_generator():
        async for item in _ai_chat_stream(user_text, run_id=run_id, category=category):
            yield item

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=_ai_sse_headers(),
    )
