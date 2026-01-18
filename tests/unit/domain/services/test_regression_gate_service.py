"""Regression gate service tests."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.entities.analysis import ComparisonResult
from evalvault.domain.services.regression_gate_service import RegressionGateService


def _build_run(run_id: str, score: float) -> EvaluationRun:
    results = [
        TestCaseResult(
            test_case_id="tc-1",
            metrics=[MetricScore(name="faithfulness", score=score, threshold=0.7)],
        )
    ]
    return EvaluationRun(
        run_id=run_id,
        dataset_name="demo",
        model_name="gpt-5-nano",
        started_at=datetime.now(),
        results=results,
        metrics_evaluated=["faithfulness"],
    )


def test_regression_gate_detects_regression() -> None:
    baseline = _build_run("baseline", 0.9)
    candidate = _build_run("candidate", 0.7)
    comparison = ComparisonResult.from_values(
        run_id_a=baseline.run_id,
        run_id_b=candidate.run_id,
        metric="faithfulness",
        mean_a=0.9,
        mean_b=0.7,
        p_value=0.01,
        effect_size=-0.8,
    )

    storage = MagicMock()
    storage.get_run.side_effect = [candidate, baseline]
    analysis = MagicMock()
    analysis.compare_runs.return_value = [comparison]

    service = RegressionGateService(storage=storage, analysis_adapter=analysis)
    report = service.run_gate("candidate", "baseline", fail_on_regression=0.05)

    assert report.regression_detected is True
    assert report.status == "failed"
    assert report.results[0].regression is True


def test_regression_gate_requires_shared_metrics() -> None:
    baseline = _build_run("baseline", 0.9)
    candidate = _build_run("candidate", 0.8)

    storage = MagicMock()
    storage.get_run.side_effect = [candidate, baseline]
    analysis = MagicMock()
    analysis.compare_runs.return_value = []

    service = RegressionGateService(storage=storage, analysis_adapter=analysis)

    with pytest.raises(ValueError, match="No comparable metrics"):
        service.run_gate("candidate", "baseline")
