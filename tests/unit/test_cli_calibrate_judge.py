from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app
from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.entities.judge_calibration import (
    JudgeCalibrationCase,
    JudgeCalibrationMetric,
    JudgeCalibrationResult,
    JudgeCalibrationSummary,
)

runner = CliRunner()


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
                metrics=[MetricScore(name="faithfulness", score=0.5, threshold=0.7)],
            ),
        ],
    )


def _build_result(run_id: str) -> JudgeCalibrationResult:
    summary = JudgeCalibrationSummary(
        run_id=run_id,
        labels_source="feedback",
        method="temperature",
        metrics=["faithfulness"],
        holdout_ratio=0.2,
        seed=42,
        total_labels=1,
        total_samples=1,
        gate_passed=True,
        gate_threshold=0.6,
        notes=[],
    )
    metric = JudgeCalibrationMetric(
        metric="faithfulness",
        method="temperature",
        sample_count=1,
        label_count=1,
        mae=0.1,
        pearson=0.9,
        spearman=0.8,
        temperature=1.2,
        parameters={"temperature": 1.2},
        gate_passed=True,
        warning=None,
    )
    case = JudgeCalibrationCase(
        test_case_id="tc-1",
        raw_score=0.5,
        calibrated_score=0.6,
        label=0.7,
        label_source="feedback",
    )
    return JudgeCalibrationResult(
        summary=summary,
        metrics=[metric],
        case_results={"faithfulness": [case]},
        warnings=[],
    )


@patch("evalvault.adapters.inbound.cli.commands.calibrate_judge.JudgeCalibrationService")
@patch("evalvault.adapters.inbound.cli.commands.calibrate_judge.build_storage_adapter")
def test_cli_calibrate_judge_success(mock_storage_cls, mock_service_cls, tmp_path) -> None:
    run = _build_run()
    storage = MagicMock()
    storage.get_run.return_value = run
    storage.list_feedback.return_value = [MagicMock()]
    mock_storage_cls.return_value = storage

    service = MagicMock()
    service.calibrate.return_value = _build_result(run.run_id)
    mock_service_cls.return_value = service

    output_path = tmp_path / "out.json"
    result = runner.invoke(
        app,
        [
            "calibrate-judge",
            run.run_id,
            "--output",
            str(output_path),
            "--labels-source",
            "feedback",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert output_path.exists()
    service.calibrate.assert_called_once()
    storage.update_run_metadata.assert_not_called()
