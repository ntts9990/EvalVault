"""Regression gate service for CLI automation."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from evalvault.domain.entities.analysis import ComparisonResult, EffectSizeLevel
from evalvault.ports.outbound.analysis_port import AnalysisPort
from evalvault.ports.outbound.storage_port import StoragePort

logger = logging.getLogger(__name__)

TestType = str


@dataclass(frozen=True)
class RegressionMetricResult:
    metric: str

    baseline_score: float
    candidate_score: float
    diff: float
    diff_percent: float
    p_value: float
    effect_size: float
    effect_level: EffectSizeLevel
    is_significant: bool
    regression: bool

    @classmethod
    def from_comparison(
        cls,
        comparison: ComparisonResult,
        *,
        fail_on_regression: float,
    ) -> RegressionMetricResult:
        regression = comparison.diff < -fail_on_regression
        return cls(
            metric=comparison.metric,
            baseline_score=comparison.mean_a,
            candidate_score=comparison.mean_b,
            diff=comparison.diff,
            diff_percent=comparison.diff_percent,
            p_value=comparison.p_value,
            effect_size=comparison.effect_size,
            effect_level=comparison.effect_level,
            is_significant=comparison.is_significant,
            regression=regression,
        )

    def to_dict(self) -> dict[str, float | str | bool]:
        return {
            "metric": self.metric,
            "baseline_score": self.baseline_score,
            "candidate_score": self.candidate_score,
            "diff": self.diff,
            "diff_percent": self.diff_percent,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "effect_level": self.effect_level.value,
            "is_significant": self.is_significant,
            "regression": self.regression,
        }


@dataclass(frozen=True)
class RegressionGateReport:
    candidate_run_id: str
    baseline_run_id: str
    results: list[RegressionMetricResult]
    regression_detected: bool
    fail_on_regression: float
    test_type: TestType
    metrics: list[str]
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    parallel: bool
    concurrency: int | None

    @property
    def status(self) -> str:
        return "failed" if self.regression_detected else "passed"

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_run_id": self.candidate_run_id,
            "baseline_run_id": self.baseline_run_id,
            "status": self.status,
            "regression_detected": self.regression_detected,
            "fail_on_regression": self.fail_on_regression,
            "test": self.test_type,
            "metrics": list(self.metrics),
            "results": [result.to_dict() for result in self.results],
            "parallel": self.parallel,
            "concurrency": self.concurrency,
        }


class RegressionGateService:
    def __init__(self, storage: StoragePort, analysis_adapter: AnalysisPort) -> None:
        self._storage = storage
        self._analysis = analysis_adapter

    def run_gate(
        self,
        candidate_run_id: str,
        baseline_run_id: str,
        *,
        metrics: list[str] | None = None,
        test_type: TestType = "t-test",
        fail_on_regression: float = 0.05,
        parallel: bool = True,
        concurrency: int | None = None,
    ) -> RegressionGateReport:
        start_time = time.monotonic()
        started_at = datetime.now(UTC)
        logger.info(
            "Regression gate start: candidate=%s baseline=%s",
            candidate_run_id,
            baseline_run_id,
        )
        try:
            candidate = self._storage.get_run(candidate_run_id)
            baseline = self._storage.get_run(baseline_run_id)

            requested_metrics = [m for m in (metrics or []) if m]
            if requested_metrics:
                metric_list = requested_metrics
            else:
                metric_list = sorted(
                    set(candidate.metrics_evaluated) & set(baseline.metrics_evaluated)
                )

            if not metric_list:
                raise ValueError("No shared metrics available for regression gate.")

            comparisons = self._analysis.compare_runs(
                baseline,
                candidate,
                metrics=metric_list,
                test_type=test_type,
            )
            if not comparisons:
                raise ValueError("No comparable metrics found for regression gate.")

            comparison_map = {result.metric: result for result in comparisons}
            missing = [metric for metric in metric_list if metric not in comparison_map]
            if missing:
                raise ValueError("Missing comparison results for metrics: " + ", ".join(missing))

            ordered = [comparison_map[metric] for metric in metric_list]
            results = [
                RegressionMetricResult.from_comparison(
                    comparison,
                    fail_on_regression=fail_on_regression,
                )
                for comparison in ordered
            ]
            regression_detected = any(result.regression for result in results)
            finished_at = datetime.now(UTC)
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(
                "Regression gate complete: candidate=%s baseline=%s regressions=%s",
                candidate_run_id,
                baseline_run_id,
                regression_detected,
            )
            return RegressionGateReport(
                candidate_run_id=candidate_run_id,
                baseline_run_id=baseline_run_id,
                results=results,
                regression_detected=regression_detected,
                fail_on_regression=fail_on_regression,
                test_type=test_type,
                metrics=metric_list,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                parallel=parallel,
                concurrency=concurrency,
            )
        except Exception:
            logger.exception(
                "Regression gate failed: candidate=%s baseline=%s",
                candidate_run_id,
                baseline_run_id,
            )
            raise


__all__ = [
    "RegressionGateReport",
    "RegressionGateService",
    "RegressionMetricResult",
]
