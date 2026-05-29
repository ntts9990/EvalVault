"""Regression gate service for CLI automation."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from evalvault.domain.entities.analysis import ComparisonResult, EffectSizeLevel
from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult
from evalvault.ports.outbound.analysis_port import AnalysisPort
from evalvault.ports.outbound.storage_port import StoragePort

logger = logging.getLogger(__name__)

TestType = Literal["t-test", "mann-whitney"]

# Fixed precision for serialized numeric fields. Chosen so cross-platform /
# cross-scipy-version float noise collapses to a single representation while
# preserving gate-relevant precision (scores are 0..1, diffs small).
CANONICAL_FLOAT_DECIMALS = 6
REGRESSION_GATE_HASH_SCHEMA_VERSION = "evalvault.regression-gate.hashes.v1"


def canonical_float(value: float, ndigits: int = CANONICAL_FLOAT_DECIMALS) -> float:
    """Canonicalize a float for deterministic JSON serialization / hash anchoring.

    Rounds to a fixed number of decimals so cross-platform ~ULP float noise
    collapses to one representation, and normalizes ``-0.0`` to ``0.0``.
    Non-finite values pass through unchanged. This affects only the serialized
    representation — never the values used to compute verdicts.
    """
    if not math.isfinite(value):
        return value
    return round(float(value), ndigits) + 0.0


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
        # Numeric fields are canonicalized for deterministic serialization
        # (hash anchoring). Booleans/enums/verdicts are unchanged.
        return {
            "metric": self.metric,
            "baseline_score": canonical_float(self.baseline_score),
            "candidate_score": canonical_float(self.candidate_score),
            "diff": canonical_float(self.diff),
            "diff_percent": canonical_float(self.diff_percent),
            "p_value": canonical_float(self.p_value),
            "effect_size": canonical_float(self.effect_size),
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
    source_artifact_hash: str
    baseline_run_hash: str
    candidate_run_hash: str
    comparison_results_hash: str
    evidence_hash: str

    @property
    def status(self) -> str:
        return "failed" if self.regression_detected else "passed"

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_run_id": self.candidate_run_id,
            "baseline_run_id": self.baseline_run_id,
            "status": self.status,
            "source_artifact_hash": self.source_artifact_hash,
            "regression_detected": self.regression_detected,
            "fail_on_regression": self.fail_on_regression,
            "test": self.test_type,
            "metrics": list(self.metrics),
            "results": [result.to_dict() for result in self.results],
            "evidence": {
                "schema_version": REGRESSION_GATE_HASH_SCHEMA_VERSION,
                "source_artifact_hash": self.source_artifact_hash,
                "baseline_run_hash": self.baseline_run_hash,
                "candidate_run_hash": self.candidate_run_hash,
                "comparison_results_hash": self.comparison_results_hash,
                "evidence_hash": self.evidence_hash,
                "hash_algorithm": "sha256",
                "canonicalization": "json-sort-keys-fixed-float-v1",
            },
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
            hash_bundle = build_regression_gate_hashes(
                baseline=baseline,
                candidate=candidate,
                results=results,
                metrics=metric_list,
                test_type=test_type,
                fail_on_regression=fail_on_regression,
            )
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
                source_artifact_hash=hash_bundle["source_artifact_hash"],
                baseline_run_hash=hash_bundle["baseline_run_hash"],
                candidate_run_hash=hash_bundle["candidate_run_hash"],
                comparison_results_hash=hash_bundle["comparison_results_hash"],
                evidence_hash=hash_bundle["evidence_hash"],
            )
        except Exception:
            logger.exception(
                "Regression gate failed: candidate=%s baseline=%s",
                candidate_run_id,
                baseline_run_id,
            )
            raise


def build_regression_gate_hashes(
    *,
    baseline: EvaluationRun,
    candidate: EvaluationRun,
    results: list[RegressionMetricResult],
    metrics: list[str],
    test_type: TestType,
    fail_on_regression: float,
) -> dict[str, str]:
    """Build deterministic source/evidence hashes for a regression report."""

    baseline_run_hash = _content_hash(_run_source_payload(baseline))
    candidate_run_hash = _content_hash(_run_source_payload(candidate))
    source_artifact_hash = _content_hash(
        {
            "schema_version": REGRESSION_GATE_HASH_SCHEMA_VERSION,
            "kind": "regression-source",
            "baseline_run_hash": baseline_run_hash,
            "candidate_run_hash": candidate_run_hash,
            "metrics": list(metrics),
            "test": test_type,
            "fail_on_regression": canonical_float(fail_on_regression),
        }
    )
    comparison_results_hash = _content_hash(
        {
            "schema_version": REGRESSION_GATE_HASH_SCHEMA_VERSION,
            "kind": "regression-comparison-results",
            "metrics": list(metrics),
            "results": [result.to_dict() for result in results],
        }
    )
    evidence_hash = _content_hash(
        {
            "schema_version": REGRESSION_GATE_HASH_SCHEMA_VERSION,
            "kind": "regression-evidence",
            "source_artifact_hash": source_artifact_hash,
            "comparison_results_hash": comparison_results_hash,
        }
    )
    return {
        "source_artifact_hash": source_artifact_hash,
        "baseline_run_hash": baseline_run_hash,
        "candidate_run_hash": candidate_run_hash,
        "comparison_results_hash": comparison_results_hash,
        "evidence_hash": evidence_hash,
    }


def _run_source_payload(run: EvaluationRun) -> dict[str, Any]:
    return {
        "schema_version": REGRESSION_GATE_HASH_SCHEMA_VERSION,
        "kind": "evaluation-run-source",
        "run_id": run.run_id,
        "project_id": run.project_id,
        "dataset_name": run.dataset_name,
        "dataset_version": run.dataset_version,
        "model_name": run.model_name,
        "metrics_evaluated": sorted(run.metrics_evaluated),
        "thresholds": _canonical_mapping(run.thresholds),
        "results": [_test_case_source_payload(result) for result in sorted(run.results, key=_test_case_key)],
    }


def _test_case_source_payload(result: TestCaseResult) -> dict[str, Any]:
    return {
        "test_case_id": result.test_case_id,
        "metrics": [_metric_source_payload(metric) for metric in sorted(result.metrics, key=lambda item: item.name)],
    }


def _metric_source_payload(metric: MetricScore) -> dict[str, Any]:
    return {
        "name": metric.name,
        "score": canonical_float(metric.score),
        "threshold": canonical_float(metric.threshold),
        "passed": metric.passed,
    }


def _test_case_key(result: TestCaseResult) -> str:
    return result.test_case_id


def _canonical_mapping(mapping: dict[str, float]) -> dict[str, float]:
    return {key: canonical_float(mapping[key]) for key in sorted(mapping)}


def _content_hash(payload: Any) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = [
    "REGRESSION_GATE_HASH_SCHEMA_VERSION",
    "build_regression_gate_hashes",
    "RegressionGateReport",
    "RegressionGateService",
    "RegressionMetricResult",
]
