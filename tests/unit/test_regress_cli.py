"""CLI tests for regress command."""

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app
from evalvault.domain.entities.analysis import EffectSizeLevel
from evalvault.domain.services.regression_gate_service import (
    RegressionGateReport,
    RegressionMetricResult,
)

runner = CliRunner()

REGRESS_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.regress"


def _make_report(regression: bool) -> RegressionGateReport:
    result = RegressionMetricResult(
        metric="faithfulness",
        baseline_score=0.9,
        candidate_score=0.8,
        diff=-0.1,
        diff_percent=-11.1,
        p_value=0.02,
        effect_size=-0.7,
        effect_level=EffectSizeLevel.MEDIUM,
        is_significant=True,
        regression=regression,
    )
    return RegressionGateReport(
        candidate_run_id="candidate",
        baseline_run_id="baseline",
        results=[result],
        regression_detected=regression,
        fail_on_regression=0.05,
        test_type="t-test",
        metrics=["faithfulness"],
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        duration_ms=10,
        parallel=True,
        concurrency=8,
    )


def test_regress_help() -> None:
    result = runner.invoke(app, ["regress", "--help"])
    assert result.exit_code == 0
    assert "baseline" in result.stdout.lower()


@patch(f"{REGRESS_COMMAND_MODULE}.RegressionGateService")
@patch(f"{REGRESS_COMMAND_MODULE}.build_storage_adapter")
def test_regress_json_output(mock_storage_cls, mock_service_cls, tmp_path) -> None:
    mock_storage_cls.return_value = MagicMock()
    mock_service = MagicMock()
    mock_service.run_gate.return_value = _make_report(regression=False)
    mock_service_cls.return_value = mock_service

    result = runner.invoke(
        app,
        [
            "regress",
            "candidate",
            "--baseline",
            "baseline",
            "--format",
            "json",
            "--db",
            str(tmp_path / "test.db"),
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "regress"
    assert payload["status"] == "ok"
    assert payload["data"]["regression_detected"] is False


@patch(f"{REGRESS_COMMAND_MODULE}.RegressionGateService")
@patch(f"{REGRESS_COMMAND_MODULE}.build_storage_adapter")
def test_regress_regression_detected(mock_storage_cls, mock_service_cls, tmp_path) -> None:
    mock_storage_cls.return_value = MagicMock()
    mock_service = MagicMock()
    mock_service.run_gate.return_value = _make_report(regression=True)
    mock_service_cls.return_value = mock_service

    result = runner.invoke(
        app,
        [
            "regress",
            "candidate",
            "--baseline",
            "baseline",
            "--db",
            str(tmp_path / "test.db"),
        ],
    )
    assert result.exit_code == 2
    assert "regression" in result.stdout.lower()
