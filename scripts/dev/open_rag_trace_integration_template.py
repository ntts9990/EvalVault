#!/usr/bin/env python3
"""Template: attach Open RAG Trace to an internal RAG pipeline."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from evalvault.adapters.outbound.tracer import (
    OpenRagTraceAdapter,
    build_eval_attributes,
    build_input_output_attributes,
    build_llm_attributes,
    build_rerank_attributes,
    build_retrieval_attributes,
    install_open_rag_log_handler,
    serialize_json,
)

logger = logging.getLogger("rag-internal")


def setup_tracing() -> OpenRagTraceAdapter:
    """Initialize tracing + log bridge.

    Notes:
    - Configure OTel exporter in your service bootstrap.
    - Without OTel SDK/exporter, the adapter becomes no-op.
    """

    adapter = OpenRagTraceAdapter()
    install_open_rag_log_handler(logger)
    logger.setLevel(logging.INFO)
    return adapter


def _doc_ids(documents: Sequence[Mapping[str, Any]]) -> list[str]:
    doc_ids: list[str] = []
    for document in documents:
        doc_id = document.get("doc_id")
        if doc_id is not None:
            doc_ids.append(str(doc_id))
    return doc_ids


def _reference_preview(documents: Sequence[Mapping[str, Any]], limit: int = 3) -> str:
    entries: list[str] = []
    for document in documents[:limit]:
        doc_id = document.get("doc_id")
        if doc_id is None:
            continue
        score = document.get("score")
        if score is None:
            entries.append(str(doc_id))
        else:
            entries.append(f"{doc_id}({score})")
    if len(documents) > limit:
        entries.append(f"+{len(documents) - limit} more")
    return ", ".join(entries)


def retrieve(adapter: OpenRagTraceAdapter, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    attrs = build_retrieval_attributes(query, top_k=top_k)
    attrs.update(build_input_output_attributes(input_value=query))

    with adapter.span("retrieve_documents", "retrieve", attrs) as span:
        logger.info("retrieval start", extra={"query": query, "top_k": top_k})
        documents = []  # TODO: replace with actual retrieval
        span.set_attribute("retrieval.documents_json", serialize_json(documents))
        span.set_attribute("output.value", _doc_ids(documents))
        span.set_attribute("custom.retrieval.doc_count", len(documents))
        logger.info("retrieval complete", extra={"count": len(documents)})
        return documents


def rerank(
    adapter: OpenRagTraceAdapter,
    query: str,
    documents: Iterable[dict[str, Any]],
    model_name: str = "rerank-model",
) -> list[dict[str, Any]]:
    attrs = build_rerank_attributes(model_name=model_name)
    attrs.update(build_input_output_attributes(input_value=query))

    with adapter.span("rerank_documents", "rerank", attrs) as span:
        logger.info("rerank start", extra={"model": model_name})
        reranked = list(documents)  # TODO: replace with actual rerank
        span.set_attribute("custom.rerank.documents_json", serialize_json(reranked))
        span.set_attribute("output.value", _doc_ids(reranked))
        span.set_attribute("custom.rerank.doc_count", len(reranked))
        logger.info("rerank complete", extra={"count": len(reranked)})
        return reranked


def generate(
    adapter: OpenRagTraceAdapter,
    prompt: str,
    model_name: str = "gpt-4o-mini",
) -> str:
    attrs = build_llm_attributes(model_name=model_name, temperature=0.2)
    attrs.update(build_input_output_attributes(input_value=prompt))

    with adapter.span("generate_answer", "llm", attrs) as span:
        logger.info("llm start", extra={"model": model_name})
        answer = "TODO: replace with actual generation"
        span.set_attribute("output.value", answer)
        logger.info("llm complete")
        return answer


def evaluate(
    adapter: OpenRagTraceAdapter,
    answer: str,
    reference_documents: Sequence[Mapping[str, Any]],
) -> float:
    attrs = build_eval_attributes("faithfulness")
    attrs.update(build_input_output_attributes(input_value=answer))
    attrs["custom.reference_count"] = len(reference_documents)
    doc_ids = _doc_ids(reference_documents)
    if doc_ids:
        attrs["custom.reference_doc_ids"] = doc_ids
    preview = _reference_preview(reference_documents)
    if preview:
        attrs["custom.reference_preview"] = preview
    attrs["custom.reference_json"] = serialize_json(reference_documents)

    with adapter.span("evaluate_answer", "eval", attrs) as span:
        score = 0.0  # TODO: replace with actual scoring
        span.set_attribute("eval.score", score)
        span.set_attribute("eval.passed", score >= 0.8)
        span.set_attribute("output.value", score)
        logger.info("eval complete", extra={"score": score})
        return score


__all__ = [
    "setup_tracing",
    "retrieve",
    "rerank",
    "generate",
    "evaluate",
]
