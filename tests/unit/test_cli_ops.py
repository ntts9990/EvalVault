from __future__ import annotations

from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app


def test_ops_snapshot_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["ops", "snapshot", "--help"])

    assert result.exit_code == 0
    assert "--run-id" in result.stdout
    assert "--output" in result.stdout
