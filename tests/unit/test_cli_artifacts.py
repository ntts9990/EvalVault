from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app


def test_artifacts_lint_writes_output(tmp_path: Path, monkeypatch) -> None:
    output_path = tmp_path / "lint.json"
    mock_summary = MagicMock(
        status="ok",
        issues=[],
        artifacts_dir=tmp_path,
        index_path=tmp_path / "index.json",
        started_at=MagicMock(isoformat=lambda: "2026-01-18T00:00:00Z"),
        finished_at=MagicMock(isoformat=lambda: "2026-01-18T00:00:01Z"),
        duration_ms=1000,
        strict=False,
    )

    def _mock_lint(self, artifacts_dir, strict=False):
        return mock_summary

    monkeypatch.setattr(
        "evalvault.domain.services.artifact_lint_service.ArtifactLintService.lint",
        _mock_lint,
    )

    runner = CliRunner()
    result = runner.invoke(app, ["artifacts", "lint", str(tmp_path), "--output", str(output_path)])

    assert result.exit_code == 0
    assert output_path.exists()
    assert "artifacts.lint" in output_path.read_text(encoding="utf-8")
