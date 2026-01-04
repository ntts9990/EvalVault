"""Tests for init CLI command."""

import pytest
from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


class TestInitCommand:
    """Tests for 'evalvault init' command."""

    def test_init_creates_env_and_sample(self, runner, tmp_path, monkeypatch):
        """Test that init creates default files."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init", "--output-dir", str(tmp_path)])

        assert result.exit_code == 0
        assert (tmp_path / ".env").exists()
        assert (tmp_path / "sample_dataset.json").exists()

    def test_init_output_dir(self, runner, tmp_path, monkeypatch):
        """Test init writes into the provided output directory."""
        monkeypatch.chdir(tmp_path)
        output_dir = tmp_path / "project"

        result = runner.invoke(app, ["init", "--output-dir", str(output_dir)])

        assert result.exit_code == 0
        assert (output_dir / ".env").exists()
        assert (output_dir / "sample_dataset.json").exists()

    def test_init_skip_env(self, runner, tmp_path, monkeypatch):
        """Test init with --skip-env option."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            app,
            ["init", "--output-dir", str(tmp_path), "--skip-env"],
        )

        assert result.exit_code == 0
        assert not (tmp_path / ".env").exists()
        assert (tmp_path / "sample_dataset.json").exists()

    def test_init_skip_sample(self, runner, tmp_path, monkeypatch):
        """Test init with --skip-sample option."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            app,
            ["init", "--output-dir", str(tmp_path), "--skip-sample"],
        )

        assert result.exit_code == 0
        assert (tmp_path / ".env").exists()
        assert not (tmp_path / "sample_dataset.json").exists()

    def test_init_help(self, runner):
        """Test init help output."""
        result = runner.invoke(app, ["init", "--help"])

        assert result.exit_code == 0
        assert "init" in result.stdout.lower()
        assert "help" in result.stdout.lower() or "usage" in result.stdout.lower()
