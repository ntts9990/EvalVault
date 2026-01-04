"""Retrieval metric utilities for benchmark evaluations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import log2


def resolve_doc_id(
    raw_doc_id: str | int | None, doc_ids: Sequence[str], fallback_index: int
) -> str:
    """Resolve a retrieved doc_id to canonical document identifiers."""

    if isinstance(raw_doc_id, int) and 0 <= raw_doc_id < len(doc_ids):
        return doc_ids[raw_doc_id]
    if raw_doc_id is not None:
        return str(raw_doc_id)
    return f"doc_{fallback_index}"


def compute_retrieval_metrics(
    retrieved_doc_ids: Sequence[str],
    relevant_doc_ids: Sequence[str],
    *,
    recall_k: int,
    ndcg_k: int | None = None,
) -> dict[str, float]:
    """Compute Precision@K, Recall@K, MRR, and nDCG@K for a single query."""

    normalized_retrieved = [str(doc_id) for doc_id in retrieved_doc_ids]
    relevant_set = {str(doc_id) for doc_id in relevant_doc_ids}

    recall_k = _normalize_k(recall_k, normalized_retrieved)
    ndcg_k = _normalize_k(ndcg_k or recall_k, normalized_retrieved)

    retrieved_top_k = normalized_retrieved[:recall_k]
    relevant_found = len(set(retrieved_top_k) & relevant_set)
    retrieved_count = len(retrieved_top_k)
    precision = relevant_found / retrieved_count if retrieved_count else 0.0
    recall = relevant_found / len(relevant_set) if relevant_set else 0.0

    mrr = 0.0
    for rank, doc_id in enumerate(retrieved_top_k, start=1):
        if doc_id in relevant_set:
            mrr = 1.0 / rank
            break

    ndcg = _ndcg_at_k(normalized_retrieved, relevant_set, ndcg_k)

    return {
        f"precision_at_{recall_k}": precision,
        f"recall_at_{recall_k}": recall,
        "mrr": mrr,
        f"ndcg_at_{ndcg_k}": ndcg,
    }


def average_retrieval_metrics(metrics_list: Sequence[Mapping[str, float]]) -> dict[str, float]:
    """Average retrieval metrics across multiple queries."""

    if not metrics_list:
        return {}

    totals: dict[str, float] = {}
    for metrics in metrics_list:
        for key, value in metrics.items():
            totals[key] = totals.get(key, 0.0) + float(value)

    count = float(len(metrics_list))
    return {key: value / count for key, value in totals.items()}


def _normalize_k(value: int | None, retrieved_doc_ids: Sequence[str]) -> int:
    if value is None or value <= 0:
        return len(retrieved_doc_ids)
    return value


def _ndcg_at_k(
    retrieved_doc_ids: Sequence[str],
    relevant_set: set[str],
    k: int,
) -> float:
    if not relevant_set or k <= 0:
        return 0.0

    limit = min(k, len(retrieved_doc_ids))
    if limit <= 0:
        return 0.0

    dcg = 0.0
    for idx in range(limit):
        if retrieved_doc_ids[idx] in relevant_set:
            dcg += 1.0 / log2(idx + 2)

    ideal_hits = min(k, len(relevant_set))
    idcg = sum(1.0 / log2(idx + 2) for idx in range(ideal_hits))
    if idcg <= 0.0:
        return 0.0

    return dcg / idcg
