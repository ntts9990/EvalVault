"""Stage metric based improvement guide builder."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from evalvault.domain.entities.improvement import (
    EffortLevel,
    EvidenceSource,
    ImprovementAction,
    ImprovementEvidence,
    ImprovementPriority,
    PatternEvidence,
    PatternType,
    RAGComponent,
    RAGImprovementGuide,
)
from evalvault.domain.entities.stage import StageMetric


class StageMetricGuideService:
    """Generate improvement guides from stage metrics."""

    def __init__(self, *, action_overrides: Mapping[str, Mapping[str, Any]] | None = None):
        self._action_overrides = _normalize_action_overrides(action_overrides)

    def build_guides(self, metrics: Iterable[StageMetric]) -> list[RAGImprovementGuide]:
        failing = [metric for metric in metrics if metric.passed is False]
        if not failing:
            return []

        grouped = self._group_by_component(failing)
        guides: list[RAGImprovementGuide] = []

        for component, items in grouped.items():
            guides.append(self._build_guide(component, items))

        return guides

    def _group_by_component(
        self, metrics: Iterable[StageMetric]
    ) -> dict[RAGComponent, list[StageMetric]]:
        grouped: dict[RAGComponent, list[StageMetric]] = defaultdict(list)
        for metric in metrics:
            component = _resolve_component(metric.metric_name)
            grouped[component].append(metric)
        return grouped

    def _build_guide(
        self,
        component: RAGComponent,
        metrics: list[StageMetric],
    ) -> RAGImprovementGuide:
        patterns = [self._build_pattern(metric) for metric in metrics]
        actions = self._build_actions(metrics)
        priority = self._resolve_priority(metrics)

        evidence = ImprovementEvidence(
            target_metric=metrics[0].metric_name,
            detected_patterns=patterns,
            total_failures=len(metrics),
            avg_score_failures=sum(metric.score for metric in metrics) / len(metrics),
            avg_score_passes=0.0,
            analysis_methods=[EvidenceSource.RULE_BASED],
        )

        return RAGImprovementGuide(
            component=component,
            target_metrics=[metric.metric_name for metric in metrics],
            priority=priority,
            actions=actions,
            evidence=evidence,
            metadata={"source": "stage_metrics"},
        )

    def _build_pattern(self, metric: StageMetric) -> PatternEvidence:
        threshold_used = {}
        if metric.threshold is not None:
            threshold_used = {"metric": metric.metric_name, "threshold": metric.threshold}
        return PatternEvidence(
            pattern_type=PatternType.STAGE_METRIC_BELOW_THRESHOLD,
            affected_count=1,
            total_count=1,
            mean_score_affected=metric.score,
            threshold_used=threshold_used,
            source=EvidenceSource.RULE_BASED,
        )

    def _build_actions(self, metrics: list[StageMetric]) -> list[ImprovementAction]:
        actions: list[ImprovementAction] = []
        for metric in metrics:
            override = self._action_overrides.get(metric.metric_name)
            if override:
                action = _action_from_override(metric, override)
            else:
                action = _action_for_metric(metric)
            if action:
                actions.append(action)
        return actions or [_fallback_action(metrics)]

    def _resolve_priority(self, metrics: list[StageMetric]) -> ImprovementPriority:
        gap = max(
            (
                (metric.threshold - metric.score)
                for metric in metrics
                if metric.threshold is not None
            ),
            default=0.0,
        )
        if gap >= 0.3:
            return ImprovementPriority.P0_CRITICAL
        if gap >= 0.15:
            return ImprovementPriority.P1_HIGH
        return ImprovementPriority.P2_MEDIUM


def _resolve_component(metric_name: str) -> RAGComponent:
    if metric_name.startswith("retrieval."):
        return RAGComponent.RETRIEVER
    if metric_name.startswith("rerank."):
        return RAGComponent.RERANKER
    if metric_name.startswith("output."):
        return RAGComponent.GENERATOR
    if metric_name.startswith("system_prompt."):
        return RAGComponent.PROMPT
    if metric_name.startswith("input."):
        return RAGComponent.QUERY_PROCESSOR
    return RAGComponent.QUERY_PROCESSOR


def _action_for_metric(metric: StageMetric) -> ImprovementAction | None:
    if metric.metric_name == "retrieval.recall_at_k":
        return ImprovementAction(
            title="Improve retrieval recall",
            description="Recall@K is below threshold. Review query rewrite/expansion and top_k.",
            implementation_hint="Enable rewrite/expansion; consider hybrid search or higher top_k.",
            expected_improvement=0.08,
            expected_improvement_range=(0.04, 0.12),
            effort=EffortLevel.MEDIUM,
            priority_score=_priority_score(metric),
        )
    if metric.metric_name == "retrieval.precision_at_k":
        return ImprovementAction(
            title="Improve retrieval precision",
            description="Precision@K is low. Filter or rerank to keep relevant documents.",
            implementation_hint="Strengthen rerank/filter; remove duplicates.",
            expected_improvement=0.06,
            expected_improvement_range=(0.03, 0.1),
            effort=EffortLevel.MEDIUM,
            priority_score=_priority_score(metric),
        )
    if metric.metric_name == "rerank.score_gap":
        return ImprovementAction(
            title="Improve rerank score separation",
            description="Score gap is small. Tune or replace the reranker.",
            implementation_hint="Tune cross-encoder; expand training data.",
            expected_improvement=0.05,
            expected_improvement_range=(0.02, 0.08),
            effort=EffortLevel.MEDIUM,
            priority_score=_priority_score(metric),
        )
    return None


def _action_from_override(
    metric: StageMetric,
    payload: Mapping[str, Any],
) -> ImprovementAction:
    expected_improvement = _coerce_float(payload.get("expected_improvement"), default=0.05)
    improvement_range = _coerce_range(payload.get("expected_improvement_range"))
    effort = _coerce_effort(payload.get("effort"))
    return ImprovementAction(
        title=str(payload.get("title") or f"{metric.metric_name} 개선"),
        description=str(payload.get("description") or ""),
        implementation_hint=str(payload.get("implementation_hint") or ""),
        expected_improvement=expected_improvement,
        expected_improvement_range=improvement_range,
        effort=effort,
        priority_score=_priority_score(metric),
    )


def _fallback_action(metrics: list[StageMetric]) -> ImprovementAction:
    metric_names = ", ".join(metric.metric_name for metric in metrics)
    return ImprovementAction(
        title="Review stage metrics",
        description=f"Stage metrics below threshold: {metric_names}",
        implementation_hint="Inspect parameters or models for the affected stage.",
        expected_improvement=0.03,
        expected_improvement_range=(0.01, 0.05),
        effort=EffortLevel.LOW,
        priority_score=max(_priority_score(metric) for metric in metrics),
    )


def _priority_score(metric: StageMetric) -> float:
    if metric.threshold is None:
        return 0.0
    gap = metric.threshold - metric.score
    return max(gap, 0.0)


def _normalize_action_overrides(
    overrides: Mapping[str, Mapping[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    if not overrides:
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for key, value in overrides.items():
        if isinstance(value, Mapping):
            normalized[str(key)] = dict(value)
    return normalized


def _coerce_float(value: Any, *, default: float) -> float:
    if value is None:
        return default
    return float(value)


def _coerce_range(value: Any) -> tuple[float, float]:
    if not value:
        return (0.0, 0.0)
    if isinstance(value, list | tuple) and len(value) >= 2:
        return (float(value[0]), float(value[1]))
    return (0.0, 0.0)


def _coerce_effort(value: Any) -> EffortLevel:
    if isinstance(value, EffortLevel):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "high":
            return EffortLevel.HIGH
        if normalized == "medium":
            return EffortLevel.MEDIUM
        if normalized == "low":
            return EffortLevel.LOW
    return EffortLevel.MEDIUM
