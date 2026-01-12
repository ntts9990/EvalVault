"""Ports for improvement analysis components."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.improvement import FailureSample, PatternEvidence


@runtime_checkable
class ActionDefinitionProtocol(Protocol):
    """Action definition contract used by ImprovementGuideService."""

    title: str
    description: str
    implementation_hint: str
    expected_improvement: float
    expected_improvement_range: tuple[float, float]
    effort: str


@runtime_checkable
class PatternDefinitionProtocol(Protocol):
    """Pattern definition contract."""

    pattern_type: str
    component: str
    priority: str
    detection_rules: Sequence[Any]
    actions: Sequence[ActionDefinitionProtocol]


@runtime_checkable
class MetricPlaybookProtocol(Protocol):
    """Metric-scoped playbook definition."""

    default_threshold: float
    patterns: Sequence[PatternDefinitionProtocol]


class PlaybookPort(Protocol):
    """Playbook interface."""

    def get_metric_playbook(self, metric: str) -> MetricPlaybookProtocol | None:
        """Return playbook configuration for the given metric."""


class PatternDetectorPort(Protocol):
    """Pattern detector interface."""

    def detect_patterns(
        self,
        run: EvaluationRun,
        metrics: Sequence[str] | None = None,
    ) -> Mapping[str, list[PatternEvidence]]:
        """Detect problematic patterns for the evaluation run."""
        ...


@runtime_checkable
class ClaimImprovementProtocol(Protocol):
    """Return type for LLM batch analysis."""

    overall_assessment: str | None
    confidence: float | None
    prioritized_improvements: Sequence[Mapping[str, Any]]


class InsightGeneratorPort(Protocol):
    """LLM insight generator interface."""

    def enrich_failure_sample(self, failure: FailureSample) -> FailureSample:
        """Enrich a single failure sample using LLM analysis."""
        ...

    def analyze_batch_failures(
        self,
        failures: Sequence[FailureSample],
        metric_name: str,
        avg_score: float,
        threshold: float,
    ) -> ClaimImprovementProtocol:
        """Produce aggregated insights for multiple failures."""
        ...
