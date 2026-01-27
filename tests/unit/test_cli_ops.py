from __future__ import annotations

import re

from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app


def strip_ansi(text: str) -> str:
    ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_pattern.sub("", text)


def test_ops_snapshot_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["ops", "snapshot", "--help"])

    assert result.exit_code == 0
    stdout = strip_ansi(result.stdout)
    assert "--run-id" in stdout
    assert "--output" in stdout
