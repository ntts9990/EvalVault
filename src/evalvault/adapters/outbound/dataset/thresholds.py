"""Helpers for dataset-level threshold columns."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any

THRESHOLD_COLUMN_MAP: dict[str, str] = {
    "threshold_faithfulness": "faithfulness",
    "threshold_answer_relevancy": "answer_relevancy",
    "threshold_context_precision": "context_precision",
    "threshold_context_recall": "context_recall",
    "threshold_factual_correctness": "factual_correctness",
    "threshold_semantic_similarity": "semantic_similarity",
}

THRESHOLD_COLUMNS = tuple(THRESHOLD_COLUMN_MAP.keys())


def is_empty_threshold_value(value: Any) -> bool:
    """Return True when the threshold value is empty/blank."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return isinstance(value, float) and math.isnan(value)


def coerce_threshold_value(value: Any, metric: str) -> float | None:
    """Normalize a threshold value to float, or return None when empty."""
    if is_empty_threshold_value(value):
        return None
    try:
        threshold = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid threshold value for '{metric}': must be a number") from exc
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"Invalid threshold value for '{metric}': must be between 0.0 and 1.0")
    return threshold


def extract_thresholds_from_rows(
    rows: Iterable[Mapping[str, Any]],
    max_rows: int = 50,
) -> dict[str, float]:
    """Extract dataset thresholds from row dictionaries."""
    thresholds: dict[str, float] = {}
    row_count = 0

    for row in rows:
        row_count += 1
        for column, metric in THRESHOLD_COLUMN_MAP.items():
            if metric in thresholds:
                continue
            if column not in row:
                continue
            value = coerce_threshold_value(row.get(column), metric)
            if value is None:
                continue
            thresholds[metric] = value
        if len(thresholds) == len(THRESHOLD_COLUMN_MAP):
            break
        if row_count >= max_rows:
            break

    return thresholds
