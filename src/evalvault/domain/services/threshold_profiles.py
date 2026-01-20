"""Threshold profile helpers for evaluation metrics."""

from __future__ import annotations

from collections.abc import Mapping

SUMMARY_RECOMMENDED_THRESHOLDS = {
    "summary_faithfulness": 0.90,
    "summary_score": 0.85,
    "entity_preservation": 0.90,
    "summary_accuracy": 0.90,
    "summary_risk_coverage": 0.90,
    "summary_non_definitive": 0.80,
    "summary_needs_followup": 0.80,
}
QA_RECOMMENDED_THRESHOLDS = {
    "faithfulness": 0.70,
    "answer_relevancy": 0.70,
    "context_precision": 0.60,
    "context_recall": 0.60,
    "factual_correctness": 0.70,
    "semantic_similarity": 0.70,
}
THRESHOLD_PROFILES = {
    "summary": SUMMARY_RECOMMENDED_THRESHOLDS,
    "qa": QA_RECOMMENDED_THRESHOLDS,
}


def apply_threshold_profile(
    metrics: list[str],
    thresholds: Mapping[str, float],
    profile: str | None,
) -> dict[str, float]:
    """Apply a threshold profile to matching metrics."""

    if not profile:
        return dict(thresholds)
    normalized = str(profile).strip().lower()
    profile_thresholds = THRESHOLD_PROFILES.get(normalized)
    if profile_thresholds is None:
        available = ", ".join(sorted(THRESHOLD_PROFILES))
        raise ValueError(f"Unknown threshold profile '{profile}'. Available: {available}")

    resolved = dict(thresholds)
    for metric, value in profile_thresholds.items():
        if metric in metrics:
            resolved[metric] = value
    return resolved
