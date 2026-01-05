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
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return to_serializable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: to_serializable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_serializable(item) for item in value]
    return value


def group_scores_by_metric(run: EvaluationRun) -> dict[str, list[float]]:
    """Collect metric scores from an EvaluationRun."""
    metric_map: dict[str, list[float]] = defaultdict(list)
    for result in run.results:
        for metric in result.metrics:
            metric_map[metric.name].append(metric.score)
    return dict(metric_map)
