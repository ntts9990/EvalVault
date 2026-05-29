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

from dataclasses import dataclass

from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult


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


REGRESS_SAMPLE_SCENARIOS: dict[str, RegressSampleScenario] = {
    _QUALITY_STEADY.name: _QUALITY_STEADY,
}


__all__ = ["REGRESS_SAMPLE_SCENARIOS", "RegressSampleScenario"]
