from __future__ import annotations

from datetime import datetime

from evalvault.domain.entities import (
    EvaluationRun,
    MetricScore,
    SatisfactionFeedback,
    TestCaseResult,
)
from evalvault.domain.services.judge_calibration_service import JudgeCalibrationService


def _build_run() -> EvaluationRun:
    now = datetime.now()
    return EvaluationRun(
        run_id="run-1",
        dataset_name="ds",
        dataset_version="1",
        model_name="model",
        started_at=now,
        finished_at=now,
        metrics_evaluated=["faithfulness"],
        thresholds={"faithfulness": 0.7},
        results=[
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[MetricScore(name="faithfulness", score=0.2, threshold=0.7)],
            ),
            TestCaseResult(
                test_case_id="tc-2",
                metrics=[MetricScore(name="faithfulness", score=0.8, threshold=0.7)],
            ),
            TestCaseResult(
                test_case_id="tc-3",
                metrics=[MetricScore(name="faithfulness", score=0.6, threshold=0.7)],
            ),
        ],
    )


def test_calibrate_with_feedback_labels() -> None:
    run = _build_run()
    feedbacks = [
        SatisfactionFeedback(
            feedback_id="f1",
            run_id=run.run_id,
            test_case_id="tc-1",
            satisfaction_score=0.3,
            created_at=datetime.now(),
        ),
        SatisfactionFeedback(
            feedback_id="f2",
            run_id=run.run_id,
            test_case_id="tc-2",
            satisfaction_score=0.9,
            created_at=datetime.now(),
        ),
    ]

    service = JudgeCalibrationService()
    result = service.calibrate(
        run,
        feedbacks,
        labels_source="feedback",
        method="temperature",
        metrics=["faithfulness"],
        holdout_ratio=0.5,
        seed=42,
    )

    assert result.summary.run_id == run.run_id
    assert result.summary.labels_source == "feedback"
    assert result.metrics[0].metric == "faithfulness"
    assert result.metrics[0].label_count == 2
    assert result.metrics[0].sample_count == 3
    assert result.case_results["faithfulness"]


def test_calibrate_missing_labels_marks_gate_failed() -> None:
    run = _build_run()
    service = JudgeCalibrationService()
    result = service.calibrate(
        run,
        [],
        labels_source="feedback",
        method="temperature",
        metrics=["faithfulness"],
        holdout_ratio=0.5,
        seed=7,
    )

    assert result.summary.gate_passed is False
    assert result.metrics[0].gate_passed is False
    assert result.metrics[0].warning
