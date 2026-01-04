"""Utilities for converting Phoenix embedding exports into Domain Memory facts."""

from __future__ import annotations

from statistics import mean
from typing import Any

from evalvault.domain.entities.memory import FactType, FactualFact


def _as_float(value: Any) -> float | None:
    try:
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str) and value.strip():
            return float(value.strip())
    except ValueError:
        return None
    return None


def _collect_text(samples: list[dict[str, Any]], key: str, max_items: int) -> list[str]:
    collected: list[str] = []
    for sample in samples:
        value = sample.get(key)
        if not isinstance(value, str):
            continue
        value = value.strip()
        if value:
            collected.append(value)
            if len(collected) >= max_items:
                break
    return collected


def build_cluster_facts(  # noqa: PLR0913
    rows: list[dict[str, Any]],
    *,
    domain: str,
    language: str,
    cluster_key: str = "cluster_id",
    min_cluster_size: int = 5,
    sample_size: int = 3,
    fact_type: FactType = "inferred",
    verification_score: float = 0.4,
) -> list[FactualFact]:
    """Create Domain Memory facts by grouping Phoenix rows by cluster."""

    clusters: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        cluster_id = row.get(cluster_key, "unassigned")
        clusters.setdefault(str(cluster_id), []).append(row)

    facts: list[FactualFact] = []
    for cluster_id, members in clusters.items():
        if len(members) < max(1, min_cluster_size):
            continue
        sample = members[: max(1, sample_size)]
        question_snippets = _collect_text(sample, "question", max_items=sample_size)
        context_snippets = _collect_text(sample, "contexts", max_items=sample_size)

        centroid_values_x = [
            value
            for value in (_as_float(row.get("umap_x")) for row in members)
            if value is not None
        ]
        centroid_values_y = [
            value
            for value in (_as_float(row.get("umap_y")) for row in members)
            if value is not None
        ]
        centroid_x = mean(centroid_values_x) if centroid_values_x else None
        centroid_y = mean(centroid_values_y) if centroid_values_y else None
        centroid = None
        if centroid_x is not None and centroid_y is not None:
            centroid = f"centroid=({centroid_x:.2f}, {centroid_y:.2f})"

        parts: list[str] = [f"size={len(members)}"]
        if question_snippets:
            parts.append("Q: " + " | ".join(question_snippets))
        if context_snippets:
            parts.append("CTX: " + " | ".join(context_snippets))
        if centroid:
            parts.append(centroid)

        source_ids = [
            str(sample.get("example_id") or sample.get("id"))
            for sample in sample
            if sample.get("example_id") or sample.get("id")
        ]

        fact = FactualFact(
            subject=f"Phoenix cluster {cluster_id}",
            predicate="embedding_pattern",
            object="; ".join(parts)[:500],
            domain=domain,
            language=language,
            fact_type=fact_type,
            verification_score=verification_score,
            verification_count=len(members),
            source_document_ids=source_ids,
        )
        facts.append(fact)

    return facts


__all__ = ["build_cluster_facts"]
