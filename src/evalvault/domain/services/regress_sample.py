"""Built-in, deterministic regression-gate sample scenarios.

These scenarios seed a pair of :class:`EvaluationRun` objects with fixed
per-test-case scores so the *real* :class:`RegressionGateService` path produces a
byte-stable T2 regress envelope. They exist so downstream consumers - notably
solution-platform's ``platform.adapters.evalvault_regress_adapter`` - can obtain
EvalVault-owned evidence from the real regress path instead of relying on a
hand-authored static fixture.

The module is intentionally pure (no I/O, no storage, no network): it only
describes the runs. Seeding a temp SQLite DB and invoking the gate is the CLI
layer's job (see ``evalvault regress-sample``).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult

REGRESS_SAMPLE_CATALOG_SCHEMA_VERSION = "evalvault.regress-sample-catalog.v1"


@dataclass(frozen=True)
class RegressSampleScenario:
    """A deterministic baseline/candidate pair for the regression gate.

    The per-case scores are chosen so the baseline/candidate metric *means* are
    exact decimals (no float surprises) and the gate verdict is stable.
    """

    name: str
    metric: str
    threshold: float
    dataset_name: str
    model_name: str
    baseline_run_id: str
    candidate_run_id: str
    baseline_scores: tuple[float, ...]
    candidate_scores: tuple[float, ...]
    fail_on_regression: float = 0.05
    test_type: str = "t-test"
    # Optional, forecast-only evidence-quality diagnostics. When set, the CLI
    # layer attaches it to the envelope as ``data.evidence_diagnostics``. Absent
    # (None) for every non-forecast scenario, so their envelopes stay byte-stable.
    evidence_diagnostics: dict[str, bool | float | int | str] | None = None

    @property
    def expected_t2_status(self) -> str:
        """Expected status for catalog metadata; release decisions live downstream."""
        baseline_mean = sum(self.baseline_scores) / len(self.baseline_scores)
        candidate_mean = sum(self.candidate_scores) / len(self.candidate_scores)
        return "failed" if baseline_mean - candidate_mean > self.fail_on_regression else "passed"

    def build_runs(self) -> tuple[EvaluationRun, EvaluationRun]:
        """Build the (baseline, candidate) runs for this scenario."""
        return (
            self._build_run(self.baseline_run_id, self.baseline_scores),
            self._build_run(self.candidate_run_id, self.candidate_scores),
        )

    def _build_run(self, run_id: str, scores: tuple[float, ...]) -> EvaluationRun:
        results = [
            TestCaseResult(
                test_case_id=f"tc-{index:02d}",
                metrics=[
                    MetricScore(name=self.metric, score=score, threshold=self.threshold)
                ],
            )
            for index, score in enumerate(scores, start=1)
        ]
        return EvaluationRun(
            run_id=run_id,
            dataset_name=self.dataset_name,
            model_name=self.model_name,
            results=results,
            metrics_evaluated=[self.metric],
            thresholds={self.metric: self.threshold},
        )


# "quality-steady": a healthy candidate that drifts a hair below baseline but
# well within the 0.05 regression budget.
#   baseline mean = 0.91     (mean of 0.905 / 0.915)
#   candidate mean = 0.9025  (mean of 0.8975 / 0.9075)
#   diff = -0.0075, diff_percent = -0.824176 -> regression=False -> status "passed"
# The tight +/-0.005 spread keeps the t-test comfortably significant (large effect)
# without flirting with the p<0.05 boundary, so the verdict is robust to scipy
# version jitter. Mirrors the scenario solution-platform consumes
# (baseline-quality-steady / candidate-quality-steady / metric "quality_score").
_QUALITY_STEADY = RegressSampleScenario(
    name="quality-steady",
    metric="quality_score",
    threshold=0.8,
    dataset_name="regression-gate-quality-steady",
    model_name="fixture-model",
    baseline_run_id="baseline-quality-steady",
    candidate_run_id="candidate-quality-steady",
    baseline_scores=(0.905, 0.915) * 5,
    candidate_scores=(0.8975, 0.9075) * 5,
)


# --- Scientific-forecasting track samples (Phase 1-5A, Tier A) -------------
# These mirror the calibration / overconfidence / leakage forecast scenarios the
# platform demo consumes. EvalVault stays strictly T2: scenario names, run IDs,
# and dataset names deliberately avoid release vocabulary (promote/hold/rollback)
# so the emitted envelope is clean under the consumer's T2 assertion. The verdict
# is "passed"/"failed" only; the platform decides the release outcome downstream.
# Each pair uses exact-mean alternating scores (same tight-spread pattern as
# quality-steady) so means are exact decimals and the t-test is robustly
# significant without flirting with the p<0.05 boundary.

# Well-calibrated, low-risk forecast: candidate drifts -0.02, inside the 0.05
# budget -> regression=False -> status "passed".
_FORECAST_CALIBRATED = RegressSampleScenario(
    name="forecast-calibrated",
    metric="forecast_calibration_score",
    threshold=0.75,
    dataset_name="regression-gate-forecast-calibrated",
    model_name="fixture-model",
    baseline_run_id="baseline-forecast-calibrated",
    candidate_run_id="candidate-forecast-calibrated",
    baseline_scores=(0.815, 0.825) * 5,
    candidate_scores=(0.795, 0.805) * 5,
    fail_on_regression=0.05,
    evidence_diagnostics={
        "calibration_sample_count": 10,
        "calibration_score_evidence": "paired_baseline_candidate_scores",
        "schema_version": "evalvault.evidence-diagnostics.v1",
    },
)

# Overconfident forecast: candidate drops -0.10, beyond the 0.06 budget ->
# regression=True -> status "failed" (platform gates this to a human-review hold).
_FORECAST_OVERCONFIDENT = RegressSampleScenario(
    name="forecast-overconfident",
    metric="forecast_calibration_score",
    threshold=0.65,
    dataset_name="regression-gate-forecast-overconfident",
    model_name="fixture-model",
    baseline_run_id="baseline-forecast-overconfident",
    candidate_run_id="candidate-forecast-overconfident",
    baseline_scores=(0.795, 0.805) * 5,
    candidate_scores=(0.695, 0.705) * 5,
    fail_on_regression=0.06,
    evidence_diagnostics={
        "calibration_gap": 0.10,
        "forecast_calibration_signal": "overconfident",
        "schema_version": "evalvault.evidence-diagnostics.v1",
    },
)

# Post-cutoff leakage: leakage-resistance collapses -0.19, far beyond the 0.06
# budget -> regression=True -> status "failed". Criticality is the platform's to
# assert from the change-spec; EvalVault only reports the T2 regression verdict.
_FORECAST_LEAKAGE = RegressSampleScenario(
    name="forecast-leakage",
    metric="leakage_resistance_score",
    threshold=0.70,
    dataset_name="regression-gate-forecast-leakage",
    model_name="fixture-model",
    baseline_run_id="baseline-forecast-leakage",
    candidate_run_id="candidate-forecast-leakage",
    baseline_scores=(0.945, 0.955) * 5,
    candidate_scores=(0.755, 0.765) * 5,
    fail_on_regression=0.06,
    evidence_diagnostics={
        "leakage_risk": "post_cutoff_signal_detected",
        "post_cutoff_evidence": "candidate_knowledge_after_cutoff",
        "schema_version": "evalvault.evidence-diagnostics.v1",
    },
)


# Insufficient evidence: the candidate drops -0.06 (beyond the 0.05 budget) ->
# regression=True -> status "failed", AND there were zero cutoff-eligible
# resolution pairs to score the forecast against. The zero-pair facts ride along
# as forecast-only ``data.evidence_diagnostics`` (the platform reads these to
# drive its conservative no-eligible-pairs path). Strict T2: the marker carries
# no release vocabulary (no promote/hold/rollback).
_FORECAST_INSUFFICIENT_EVIDENCE = RegressSampleScenario(
    name="forecast-insufficient-evidence",
    metric="forecast_resolution_coverage",
    threshold=0.70,
    dataset_name="regression-gate-forecast-insufficient-evidence",
    model_name="fixture-model",
    baseline_run_id="baseline-forecast-insufficient-evidence",
    candidate_run_id="candidate-forecast-insufficient-evidence",
    baseline_scores=(0.795, 0.805) * 5,
    candidate_scores=(0.735, 0.745) * 5,
    fail_on_regression=0.05,
    evidence_diagnostics={
        "eligible_pair_count": 0,
        "sample_coverage": 0,
        "resolution_card_count": 0,
        "schema_version": "evalvault.evidence-diagnostics.v1",
    },
)


# Company-RAG permission leakage: the assistant cites a document the user has no
# permission to see (an exec salary table), so permission-containment collapses
# -0.19, far beyond the 0.06 budget -> regression=True -> status "failed". Mirrors
# the platform's company-rag-rollback keystone (the representative live scenario).
# Strict T2: scenario/run/dataset names carry no release vocabulary; the platform
# asserts the fail-closed rollback downstream from the permission-leakage diagnostic
# (same shape as forecast-leakage's leakage_risk marker).
_COMPANY_RAG_LEAKAGE = RegressSampleScenario(
    name="company-rag-leakage",
    metric="permission_containment_score",
    threshold=0.70,
    dataset_name="regression-gate-company-rag-leakage",
    model_name="fixture-model",
    baseline_run_id="baseline-company-rag-leakage",
    candidate_run_id="candidate-company-rag-leakage",
    baseline_scores=(0.945, 0.955) * 5,
    candidate_scores=(0.755, 0.765) * 5,
    fail_on_regression=0.06,
    evidence_diagnostics={
        "leakage_risk": "unauthorized_document_cited",
        "permission_boundary_evidence": "exec_salary_table_in_citations",
        "schema_version": "evalvault.evidence-diagnostics.v1",
    },
)


REGRESS_SAMPLE_SCENARIOS: dict[str, RegressSampleScenario] = {
    scenario.name: scenario
    for scenario in (
        _QUALITY_STEADY,
        _FORECAST_CALIBRATED,
        _FORECAST_OVERCONFIDENT,
        _FORECAST_LEAKAGE,
        _FORECAST_INSUFFICIENT_EVIDENCE,
        _COMPANY_RAG_LEAKAGE,
    )
}

def build_regress_sample_catalog() -> dict[str, Any]:
    """Return the deterministic machine-readable catalog for built-in samples."""
    samples = [
        {
            "evalvault_sample_id": scenario.name,
            "required_t2_metric": scenario.metric,
            "metrics": [scenario.metric],
            "expected_t2_status": scenario.expected_t2_status,
            "dataset_name": scenario.dataset_name,
            "baseline_run_id": scenario.baseline_run_id,
            "candidate_run_id": scenario.candidate_run_id,
            "fail_on_regression": scenario.fail_on_regression,
            "test": scenario.test_type,
            "diagnostics_available": scenario.evidence_diagnostics is not None,
            "diagnostic_fields": sorted(
                key
                for key in (scenario.evidence_diagnostics or {})
                if key != "schema_version"
            ),
        }
        for scenario in (REGRESS_SAMPLE_SCENARIOS[name] for name in sorted(REGRESS_SAMPLE_SCENARIOS))
    ]
    payload: dict[str, Any] = {
        "schema_version": REGRESS_SAMPLE_CATALOG_SCHEMA_VERSION,
        "generated_at": "2026-05-30T00:00:00Z",
        "status_vocabulary": ["passed", "failed"],
        "sample_count": len(samples),
        "samples": samples,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    payload["catalog_hash"] = "sha256:" + hashlib.sha256(canonical).hexdigest()
    return payload

__all__ = [
    "REGRESS_SAMPLE_CATALOG_SCHEMA_VERSION",
    "REGRESS_SAMPLE_SCENARIOS",
    "RegressSampleScenario",
    "build_regress_sample_catalog",
]
