"""Helpers for pipeline analysis modules."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult


def get_upstream_output(inputs: dict[str, Any], *keys: str) -> Any:
    """Return the first matching upstream output by key."""
    for key in keys:
        if key in inputs:
            return inputs.get(key)
    return None


def safe_mean(values: Iterable[float]) -> float:
    """Compute a safe mean for possibly empty iterables."""
    values_list = list(values)
    if not values_list:
        return 0.0
    return sum(values_list) / len(values_list)


def average_scores(metrics: dict[str, list[float]]) -> dict[str, float]:
    """Compute per-metric averages."""
    return {name: safe_mean(values) for name, values in metrics.items()}


def overall_score(metrics: dict[str, list[float]]) -> float:
    """Compute overall average score across metrics."""
    return safe_mean(average_scores(metrics).values())


def truncate_text(text: str | None, max_len: int = 80) -> str:
    """Truncate text for previews."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def build_check(name: str, passed: bool, detail: str | None = None) -> dict[str, Any]:
    """Build a standardized quality check result."""
    payload: dict[str, Any] = {
        "name": name,
        "status": "pass" if passed else "fail",
    }
    if detail:
        payload["detail"] = detail
    return payload


def build_run_from_metrics(
    metrics: dict[str, list[float]],
    *,
    dataset_name: str = "sample",
    model_name: str = "sample",
) -> EvaluationRun:
    """Build a minimal EvaluationRun from metric score arrays."""
    run = EvaluationRun(
        run_id=str(uuid4()),
        dataset_name=dataset_name,
        model_name=model_name,
        metrics_evaluated=list(metrics.keys()),
    )

    max_len = max((len(values) for values in metrics.values()), default=0)
    for idx in range(max_len):
        metric_scores: list[MetricScore] = []
        for metric_name, values in metrics.items():
            if idx < len(values):
                metric_scores.append(MetricScore(name=metric_name, score=values[idx]))
        if metric_scores:
            run.results.append(TestCaseResult(test_case_id=f"sample-{idx}", metrics=metric_scores))

    return run


def to_serializable(value: Any) -> Any:
    """Convert nested structures into JSON-serializable data."""
    if value is None:
        return None
    try:  # Avoid hard dependency on numpy when not installed
        import numpy as np  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        np = None
    if np is not None:
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return to_serializable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: to_serializable(val) for key, val in value.items()}
    if isinstance(value, list | tuple | set):
        return [to_serializable(item) for item in value]
    return value


def group_scores_by_metric(run: EvaluationRun) -> dict[str, list[float]]:
    """Collect metric scores from an EvaluationRun."""
    metric_map: dict[str, list[float]] = defaultdict(list)
    for result in run.results:
        for metric in result.metrics:
            metric_map[metric.name].append(metric.score)
    return dict(metric_map)


def build_retrieval_corpus(
    run: EvaluationRun,
    *,
    max_documents: int = 1000,
) -> tuple[list[str], dict[str, int]]:
    """Build a unique context corpus from run results."""
    documents: list[str] = []
    index_map: dict[str, int] = {}

    for result in run.results:
        for context in result.contexts or []:
            text = context.strip()
            if not text or text in index_map:
                continue
            index_map[text] = len(documents)
            documents.append(text)
            if len(documents) >= max_documents:
                return documents, index_map
    return documents, index_map


def build_query_set(
    run: EvaluationRun,
    *,
    index_map: dict[str, int],
    max_queries: int = 200,
) -> list[dict[str, Any]]:
    """Build query records with relevant doc ids."""
    queries: list[dict[str, Any]] = []
    for result in run.results:
        if not result.question:
            continue
        relevant_ids = []
        for context in result.contexts or []:
            text = context.strip()
            if text in index_map:
                relevant_ids.append(index_map[text])
        queries.append(
            {
                "query_id": result.test_case_id,
                "query": result.question,
                "relevant_doc_ids": list(dict.fromkeys(relevant_ids)),
            }
        )
        if len(queries) >= max_queries:
            break
    return queries


def recall_at_k(
    retrieved_ids: Iterable[int],
    relevant_ids: Iterable[int],
    *,
    k: int,
) -> float:
    """Compute recall@k for retrieved document ids."""
    retrieved_list = list(retrieved_ids)[:k]
    relevant_set = set(relevant_ids)
    if not relevant_set:
        return 0.0
    hits = len(set(retrieved_list) & relevant_set)
    return hits / len(relevant_set)
