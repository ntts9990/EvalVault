"""Utilities for applying retrievers to datasets."""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from datetime import date
from typing import Any

from evalvault.domain.entities import Dataset, TestCase
from evalvault.domain.services.document_versioning import (
    VersionedChunk,
    parse_contract_date,
    select_chunks_for_contract_date,
)
from evalvault.ports.outbound.korean_nlp_port import RetrieverPort, RetrieverResultProtocol


def apply_retriever_to_dataset(
    *,
    dataset: Dataset,
    retriever: RetrieverPort,
    top_k: int,
    doc_ids: Sequence[str] | None,
) -> dict[str, dict[str, Any]]:
    """Populate empty contexts via retriever and return retrieval metadata."""

    retrieval_metadata: dict[str, dict[str, Any]] = {}
    resolved_doc_ids = list(doc_ids or [])

    for test_case in dataset.test_cases:
        if _has_contexts(test_case.contexts):
            continue
        started_at = time.perf_counter()
        results = retriever.search(test_case.question, top_k=top_k)
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        contexts, doc_id_list, scores = _normalize_retrieval_results(
            results,
            doc_ids=resolved_doc_ids,
        )
        if contexts:
            test_case.contexts.extend(contexts)
        metadata: dict[str, Any] = {
            "doc_ids": doc_id_list,
            "top_k": top_k,
            "retrieval_time_ms": elapsed_ms,
        }
        if scores:
            metadata["scores"] = scores
        metadata.update(_extract_graph_attributes(results))
        graphrag_details = _build_graphrag_details(
            results,
            doc_ids=resolved_doc_ids,
            max_docs=top_k,
        )
        if graphrag_details:
            metadata["retriever"] = "graphrag"
            metadata["graphrag"] = graphrag_details
        retrieval_metadata[test_case.id] = metadata

    return retrieval_metadata


def _has_contexts(contexts: Sequence[str]) -> bool:
    return any(ctx.strip() for ctx in contexts)


def _normalize_retrieval_results(
    results: Sequence[RetrieverResultProtocol],
    *,
    doc_ids: Sequence[str],
) -> tuple[list[str], list[str], list[float]]:
    contexts: list[str] = []
    resolved_doc_ids: list[str] = []
    scores: list[float] = []
    all_scored = True

    for idx, result in enumerate(results, start=1):
        document = _extract_document(result)
        if not document:
            continue
        contexts.append(document)

        resolved_doc_ids.append(_resolve_doc_id(result, doc_ids, idx))

        score = _extract_score(result)
        if score is None:
            all_scored = False
        else:
            scores.append(score)

    if not all_scored:
        scores = []

    return contexts, resolved_doc_ids, scores


def _extract_document(result: RetrieverResultProtocol) -> str | None:
    document = getattr(result, "document", None)
    if isinstance(document, str):
        return document
    content = getattr(result, "content", None)
    if isinstance(content, str):
        return content
    return None


def _extract_score(result: RetrieverResultProtocol) -> float | None:
    score = getattr(result, "score", None)
    if score is None:
        return None
    try:
        return float(score)
    except (TypeError, ValueError):
        return None


def _resolve_doc_id(
    result: RetrieverResultProtocol,
    doc_ids: Sequence[str],
    fallback_index: int,
) -> str:
    raw_doc_id = getattr(result, "doc_id", None)
    if isinstance(raw_doc_id, int) and 0 <= raw_doc_id < len(doc_ids):
        return str(doc_ids[raw_doc_id])
    if raw_doc_id is not None:
        return str(raw_doc_id)
    return f"doc_{fallback_index}"


def _extract_graph_attributes(
    results: Sequence[RetrieverResultProtocol],
) -> dict[str, Any]:
    nodes: set[str] = set()
    edges: set[str] = set()
    community_ids: set[str] = set()

    for result in results:
        metadata = getattr(result, "metadata", None)
        if not isinstance(metadata, dict):
            continue

        kg_meta = metadata.get("kg")
        if isinstance(kg_meta, dict):
            for entity in kg_meta.get("entities", []) or []:
                nodes.add(str(entity))
            for relation in kg_meta.get("relations", []) or []:
                edges.add(str(relation))
            community_id = kg_meta.get("community_id")
            if community_id is not None:
                community_ids.add(str(community_id))

        community_id = metadata.get("community_id")
        if community_id is not None:
            community_ids.add(str(community_id))

    if not (nodes or edges or community_ids):
        return {}

    attributes: dict[str, Any] = {
        "graph_nodes": len(nodes),
        "graph_edges": len(edges),
        "subgraph_size": len(nodes) + len(edges),
        "community_id": _compact_values(community_ids) if community_ids else None,
    }
    return attributes


def _compact_values(values: set[str]) -> str | list[str]:
    if len(values) == 1:
        return next(iter(values))
    return sorted(values)


def _build_graphrag_details(
    results: Sequence[RetrieverResultProtocol],
    *,
    doc_ids: Sequence[str],
    max_docs: int,
    max_entities: int = 20,
    max_relations: int = 20,
) -> dict[str, Any] | None:
    details: list[dict[str, Any]] = []
    for rank, result in enumerate(results, start=1):
        metadata = getattr(result, "metadata", None)
        if not isinstance(metadata, dict):
            continue

        kg_meta = metadata.get("kg") if isinstance(metadata.get("kg"), dict) else None
        bm25_meta = metadata.get("bm25") if isinstance(metadata.get("bm25"), dict) else None
        dense_meta = metadata.get("dense") if isinstance(metadata.get("dense"), dict) else None
        community_id = metadata.get("community_id")

        if not (kg_meta or bm25_meta or dense_meta or community_id is not None):
            continue

        doc_id = _resolve_doc_id(result, doc_ids, rank)
        entry: dict[str, Any] = {
            "doc_id": doc_id,
            "rank": rank,
        }
        score = _extract_score(result)
        if score is not None:
            entry["score"] = score

        sources: dict[str, Any] = {}
        if kg_meta:
            sources["kg"] = {
                "entity_score": _coerce_float_or_none(kg_meta.get("entity_score")),
                "relation_score": _coerce_float_or_none(kg_meta.get("relation_score")),
                "entities": _limit_strings(kg_meta.get("entities"), max_entities),
                "relations": _limit_strings(kg_meta.get("relations"), max_relations),
                "community_id": _coerce_text_or_list(kg_meta.get("community_id")),
            }
        if bm25_meta:
            sources["bm25"] = _build_rank_score(bm25_meta)
        if dense_meta:
            sources["dense"] = _build_rank_score(dense_meta)
        if community_id is not None:
            sources["community_id"] = _coerce_text_or_list(community_id)
        if sources:
            entry["sources"] = sources

        details.append(entry)
        if len(details) >= max_docs:
            break

    if not details:
        return None

    return {
        "docs": details,
        "max_docs": max_docs,
        "max_entities": max_entities,
        "max_relations": max_relations,
    }


def _build_rank_score(payload: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    rank = _coerce_int_optional(payload.get("rank"))
    if rank is not None:
        out["rank"] = rank
    score = _coerce_float_or_none(payload.get("score"))
    if score is not None:
        out["score"] = score
    return out


def _coerce_float_or_none(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int_optional(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_text_or_list(value: Any) -> str | list[str] | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return str(value)


def _limit_strings(value: Any, limit: int) -> list[str]:
    if not value:
        return []
    items = list(value) if isinstance(value, (list, tuple, set)) else [value]
    return [str(item) for item in items[:limit]]


def apply_versioned_retriever_to_dataset(
    *,
    dataset: Dataset,
    versioned_chunks: Sequence[VersionedChunk],
    build_retriever: Callable[[Sequence[str]], RetrieverPort],
    top_k: int,
) -> dict[str, dict[str, Any]]:
    cases_by_contract: dict[date | None, list[TestCase]] = {}
    for test_case in dataset.test_cases:
        if _has_contexts(test_case.contexts):
            continue
        contract = None
        if isinstance(test_case.metadata, dict):
            contract = parse_contract_date(test_case.metadata.get("contract_date"))
        cases_by_contract.setdefault(contract, []).append(test_case)

    if not cases_by_contract:
        return {}

    retrieval_metadata: dict[str, dict[str, Any]] = {}
    chunk_list = list(versioned_chunks)

    for contract, cases in cases_by_contract.items():
        selected = select_chunks_for_contract_date(chunk_list, contract)
        documents = [chunk.content for chunk in selected]
        doc_ids = [chunk.doc_id for chunk in selected]

        retriever = build_retriever(documents)
        subset = Dataset(
            name=dataset.name,
            version=dataset.version,
            test_cases=cases,
            metadata=dict(dataset.metadata or {}),
            source_file=dataset.source_file,
            thresholds=dict(dataset.thresholds or {}),
        )
        retrieval_metadata.update(
            apply_retriever_to_dataset(
                dataset=subset,
                retriever=retriever,
                top_k=top_k,
                doc_ids=doc_ids,
            )
        )

    return retrieval_metadata
