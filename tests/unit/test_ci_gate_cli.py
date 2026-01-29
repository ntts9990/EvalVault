"""CLI tests for ci-gate command."""

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app
from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.entities.analysis import EffectSizeLevel
from evalvault.domain.services.regression_gate_service import (
    RegressionGateReport,
    RegressionMetricResult,
)

runner = CliRunner()

REGRESS_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.regress"


def _build_run(
    run_id: str, scores: dict[str, float], thresholds: dict[str, float]
) -> EvaluationRun:
    metrics = [
        MetricScore(name=metric, score=score, threshold=thresholds.get(metric, 0.7))
        for metric, score in scores.items()
    ]
    return EvaluationRun(
        run_id=run_id,
        dataset_name="demo",
        model_name="gpt-5-mini",
        started_at=datetime.now(),
        results=[TestCaseResult(test_case_id="tc-1", metrics=metrics)],
        metrics_evaluated=list(scores.keys()),
        thresholds=thresholds,
    )


def _make_report(results: list[RegressionMetricResult]) -> RegressionGateReport:
    regression_detected = any(result.regression for result in results)
    return RegressionGateReport(
        candidate_run_id="current",
        baseline_run_id="baseline",
        results=results,
        regression_detected=regression_detected,
        fail_on_regression=0.05,
        test_type="t-test",
        metrics=[result.metric for result in results],
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        duration_ms=10,
        parallel=True,
        concurrency=8,
    )


def _make_metric_result(
    metric: str, baseline: float, current: float, regression: bool
) -> RegressionMetricResult:
    diff = current - baseline
    diff_percent = (diff / baseline * 100) if baseline else 0.0
    return RegressionMetricResult(
        metric=metric,
        baseline_score=baseline,
        candidate_score=current,
        diff=diff,
        diff_percent=diff_percent,
        p_value=0.02,
        effect_size=0.1,
        effect_level=EffectSizeLevel.SMALL,
        is_significant=True,
        regression=regression,
    )


def test_ci_gate_help() -> None:
    result = runner.invoke(app, ["ci-gate", "--help"])
    assert result.exit_code == 0


@patch(f"{REGRESS_COMMAND_MODULE}.RegressionGateService")
@patch(f"{REGRESS_COMMAND_MODULE}.build_storage_adapter")
def test_ci_gate_json_output_success(mock_storage_cls, mock_service_cls, tmp_path) -> None:
    current_run = _build_run("current", {"faithfulness": 0.82}, {"faithfulness": 0.7})
    baseline_run = _build_run("baseline", {"faithfulness": 0.8}, {"faithfulness": 0.7})
    mock_storage = MagicMock()
    mock_storage.get_run.side_effect = [current_run, baseline_run]
    mock_storage_cls.return_value = mock_storage

    report = _make_report([_make_metric_result("faithfulness", 0.8, 0.82, False)])
    mock_service = MagicMock()
    mock_service.run_gate.return_value = report
    mock_service_cls.return_value = mock_service

    result = runner.invoke(
        app,
        [
            "ci-gate",
            "baseline",
            "current",
            "--format",
            "json",
            "--db",
            str(tmp_path / "test.db"),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["gate_passed"] is True
    assert payload["regression_rate"] == 0.0


@patch(f"{REGRESS_COMMAND_MODULE}.RegressionGateService")
@patch(f"{REGRESS_COMMAND_MODULE}.build_storage_adapter")
def test_ci_gate_markdown_output(mock_storage_cls, mock_service_cls, tmp_path) -> None:
    current_run = _build_run("current", {"faithfulness": 0.82}, {"faithfulness": 0.7})
    baseline_run = _build_run("baseline", {"faithfulness": 0.8}, {"faithfulness": 0.7})
    mock_storage = MagicMock()
    mock_storage.get_run.side_effect = [current_run, baseline_run]
    mock_storage_cls.return_value = mock_storage

    report = _make_report([_make_metric_result("faithfulness", 0.8, 0.82, False)])
    mock_service = MagicMock()
    mock_service.run_gate.return_value = report
    mock_service_cls.return_value = mock_service

    result = runner.invoke(
        app,
        [
            "ci-gate",
            "baseline",
            "current",
            "--format",
            "github",
            "--db",
            str(tmp_path / "test.db"),
        ],
    )
    assert result.exit_code == 0
    assert "## RAG Regression Gate Results" in result.stdout


@patch(f"{REGRESS_COMMAND_MODULE}.RegressionGateService")
@patch(f"{REGRESS_COMMAND_MODULE}.build_storage_adapter")
def test_ci_gate_pr_comment_output(mock_storage_cls, mock_service_cls, tmp_path) -> None:
    current_run = _build_run("current", {"faithfulness": 0.82}, {"faithfulness": 0.7})
    baseline_run = _build_run("baseline", {"faithfulness": 0.8}, {"faithfulness": 0.7})
    mock_storage = MagicMock()
    mock_storage.get_run.side_effect = [current_run, baseline_run]
    mock_storage_cls.return_value = mock_storage

    report = _make_report([_make_metric_result("faithfulness", 0.8, 0.82, False)])
    mock_service = MagicMock()
    mock_service.run_gate.return_value = report
    mock_service_cls.return_value = mock_service

    result = runner.invoke(
        app,
        [
            "ci-gate",
            "baseline",
            "current",
            "--format",
            "pr-comment",
            "--db",
            str(tmp_path / "test.db"),
        ],
    )

    assert result.exit_code == 0
    assert "## EvalVault CI Gate" in result.stdout


@patch(f"{REGRESS_COMMAND_MODULE}.RegressionGateService")
@patch(f"{REGRESS_COMMAND_MODULE}.build_storage_adapter")
def test_ci_gate_gitlab_output(mock_storage_cls, mock_service_cls, tmp_path) -> None:
    current_run = _build_run("current", {"faithfulness": 0.82}, {"faithfulness": 0.7})
    baseline_run = _build_run("baseline", {"faithfulness": 0.8}, {"faithfulness": 0.7})
    mock_storage = MagicMock()
    mock_storage.get_run.side_effect = [current_run, baseline_run]
    mock_storage_cls.return_value = mock_storage

    report = _make_report([_make_metric_result("faithfulness", 0.8, 0.82, False)])
    mock_service = MagicMock()
    mock_service.run_gate.return_value = report
    mock_service_cls.return_value = mock_service

    result = runner.invoke(
        app,
        [
            "ci-gate",
            "baseline",
            "current",
            "--format",
            "gitlab",
            "--db",
            str(tmp_path / "test.db"),
        ],
    )
    assert result.exit_code == 0
    assert "## RAG Regression Gate Results" in result.stdout


@patch(f"{REGRESS_COMMAND_MODULE}.RegressionGateService")
@patch(f"{REGRESS_COMMAND_MODULE}.build_storage_adapter")
def test_ci_gate_regression_exit_code(mock_storage_cls, mock_service_cls, tmp_path) -> None:
    current_run = _build_run("current", {"faithfulness": 0.7}, {"faithfulness": 0.7})
    baseline_run = _build_run("baseline", {"faithfulness": 0.9}, {"faithfulness": 0.7})
    mock_storage = MagicMock()
    mock_storage.get_run.side_effect = [current_run, baseline_run]
    mock_storage_cls.return_value = mock_storage

    report = _make_report([_make_metric_result("faithfulness", 0.9, 0.7, True)])
    mock_service = MagicMock()
    mock_service.run_gate.return_value = report
    mock_service_cls.return_value = mock_service

    result = runner.invoke(
        app,
        [
            "ci-gate",
            "baseline",
            "current",
            "--format",
            "json",
            "--db",
            str(tmp_path / "test.db"),
        ],
    )
    assert result.exit_code == 2


@patch(f"{REGRESS_COMMAND_MODULE}.RegressionGateService")
@patch(f"{REGRESS_COMMAND_MODULE}.build_storage_adapter")
def test_ci_gate_regression_no_fail_when_disabled(
    mock_storage_cls,
    mock_service_cls,
    tmp_path,
) -> None:
    current_run = _build_run("current", {"faithfulness": 0.7}, {"faithfulness": 0.7})
    baseline_run = _build_run("baseline", {"faithfulness": 0.9}, {"faithfulness": 0.7})
    mock_storage = MagicMock()
    mock_storage.get_run.side_effect = [current_run, baseline_run]
    mock_storage_cls.return_value = mock_storage

    report = _make_report([_make_metric_result("faithfulness", 0.9, 0.7, True)])
    mock_service = MagicMock()
    mock_service.run_gate.return_value = report
    mock_service_cls.return_value = mock_service

    result = runner.invoke(
        app,
        [
            "ci-gate",
            "baseline",
            "current",
            "--format",
            "json",
            "--no-fail-on-regression",
            "--db",
            str(tmp_path / "test.db"),
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["gate_passed"] is False


@patch(f"{REGRESS_COMMAND_MODULE}.RegressionGateService")
@patch(f"{REGRESS_COMMAND_MODULE}.build_storage_adapter")
def test_ci_gate_threshold_failure_exit_code(mock_storage_cls, mock_service_cls, tmp_path) -> None:
    current_run = _build_run("current", {"faithfulness": 0.6}, {"faithfulness": 0.7})
    baseline_run = _build_run("baseline", {"faithfulness": 0.9}, {"faithfulness": 0.7})
    mock_storage = MagicMock()
    mock_storage.get_run.side_effect = [current_run, baseline_run]
    mock_storage_cls.return_value = mock_storage

    report = _make_report([_make_metric_result("faithfulness", 0.9, 0.6, False)])
    mock_service = MagicMock()
    mock_service.run_gate.return_value = report
    mock_service_cls.return_value = mock_service

    result = runner.invoke(
        app,
        [
            "ci-gate",
            "baseline",
            "current",
            "--format",
            "json",
            "--db",
            str(tmp_path / "test.db"),
        ],
    )
    assert result.exit_code == 1


def test_ci_gate_missing_db_path() -> None:
    result = runner.invoke(app, ["ci-gate", "baseline", "current"])
    assert result.exit_code == 1
    assert "Database path" in result.stdout


def test_ci_gate_invalid_format() -> None:
    result = runner.invoke(
        app,
        ["ci-gate", "baseline", "current", "--format", "nope", "--db", "data/db/evalvault.db"],
    )
    assert result.exit_code == 1


@patch(f"{REGRESS_COMMAND_MODULE}.RegressionGateService")
@patch(f"{REGRESS_COMMAND_MODULE}.build_storage_adapter")
def test_ci_gate_regression_rate_calculation(
    mock_storage_cls,
    mock_service_cls,
    tmp_path,
) -> None:
    current_run = _build_run(
        "current",
        {"faithfulness": 0.7, "answer_relevancy": 0.8},
        {"faithfulness": 0.7, "answer_relevancy": 0.7},
    )
    baseline_run = _build_run(
        "baseline",
        {"faithfulness": 0.9, "answer_relevancy": 0.8},
        {"faithfulness": 0.7, "answer_relevancy": 0.7},
    )
    mock_storage = MagicMock()
    mock_storage.get_run.side_effect = [current_run, baseline_run]
    mock_storage_cls.return_value = mock_storage

    results = [
        _make_metric_result("faithfulness", 0.9, 0.7, True),
        _make_metric_result("answer_relevancy", 0.8, 0.8, False),
    ]
    report = _make_report(results)
    mock_service = MagicMock()
    mock_service.run_gate.return_value = report
    mock_service_cls.return_value = mock_service

    result = runner.invoke(
        app,
        [
            "ci-gate",
            "baseline",
            "current",
            "--format",
            "json",
            "--regression-threshold",
            "0.49",
            "--db",
            str(tmp_path / "test.db"),
        ],
    )

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["regression_rate"] == 0.5
