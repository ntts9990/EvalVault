from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
import typer
from rich.console import Console

from evalvault.adapters.inbound.cli.utils import console as cli_console
from evalvault.adapters.inbound.cli.utils import errors, formatters, options, presets, validators


def test_format_status_and_score() -> None:
    assert formatters.format_status(True) == "[green]PASS[/green]"
    assert formatters.format_status(False, success_text="OK", failure_text="NO") == "[red]NO[/red]"

    assert formatters.format_score(None) == "-"
    assert formatters.format_score(0.125, True, precision=2) == "[green]0.12[/green]"
    assert formatters.format_score(0.9876, False, precision=3) == "[red]0.988[/red]"
    assert formatters.format_score(0.5, None, precision=1) == "[cyan]0.5[/cyan]"


def test_format_diff() -> None:
    assert formatters.format_diff(None) == "-"
    assert formatters.format_diff(0.1234, precision=2) == "[green]+0.12[/green]"
    assert formatters.format_diff(-0.5, precision=1) == "[red]-0.5[/red]"


def test_presets_lookup_and_help() -> None:
    assert presets.get_preset(None) is None
    assert presets.get_preset("") is None
    assert presets.get_preset(cast(str, 123)) is None

    quick = presets.get_preset("Quick")
    assert quick is not None
    assert quick.name == "quick"
    assert "faithfulness" in quick.metrics

    assert presets.list_presets() == sorted(presets.PRESETS.keys())
    help_text = presets.format_preset_help()
    assert "Available presets:" in help_text
    for name in presets.list_presets():
        assert name in help_text


def test_options_factories_and_normalize() -> None:
    assert options._normalize_path(None) is None
    path_value = Path("example.db")
    assert options._normalize_path(path_value) is path_value
    assert options._normalize_path("example.db") == Path("example.db")

    profile = options.profile_option()
    assert profile.default is None
    assert "--profile" in profile.param_decls

    db_option = options.db_option()
    settings = options.Settings()
    assert db_option.default is None
    assert db_option.show_default is False

    db_none = options.db_option(default=None)
    assert db_none.default is None
    assert db_none.show_default is False

    memory_db = options.memory_db_option()
    if settings.db_backend == "sqlite":
        assert memory_db.default == Path(settings.evalvault_memory_db_path)
        assert memory_db.show_default is True
    else:
        assert memory_db.default is None
        assert memory_db.show_default is False


def test_parse_csv_option() -> None:
    assert validators.parse_csv_option(None) == []
    assert validators.parse_csv_option("") == []
    assert validators.parse_csv_option(" a, b ,, c ") == ["a", "b", "c"]


def test_validate_choices_invalid() -> None:
    console = Console(record=True)
    with pytest.raises(typer.Exit):
        validators.validate_choices(
            ["bad", "ok"],
            ["ok"],
            console,
            value_label="metric",
        )
    output = console.export_text()
    assert "Invalid metrics" in output
    assert "Available metrics" in output


def test_validate_choices_valid() -> None:
    console = Console(record=True)
    validators.validate_choices(["ok"], ["ok", "other"], console, value_label="metric")
    assert console.export_text().strip() == ""


def test_validate_choice_invalid() -> None:
    console = Console(record=True)
    with pytest.raises(typer.Exit):
        validators.validate_choice("bad", ["ok"], console, value_label="metric")
    output = console.export_text()
    assert "Invalid metric" in output
    assert "Available metrics" in output


def test_validate_choice_valid() -> None:
    console = Console(record=True)
    validators.validate_choice("ok", ["ok"], console, value_label="metric")
    assert console.export_text().strip() == ""


def test_console_error_and_warning_output() -> None:
    console = Console(record=True)
    cli_console.print_cli_error(console, "Boom", fixes=["Do this"], details="details")
    output = console.export_text()
    assert "Boom" in output
    assert "How to fix" in output
    assert "Do this" in output
    assert "details" in output

    console = Console(record=True)
    cli_console.print_cli_warning(console, "Heads up", tips=["Try this"])
    output = console.export_text()
    assert "Heads up" in output
    assert "Tips" in output
    assert "Try this" in output


def test_progress_spinner_runs() -> None:
    console = Console(record=True)
    with cli_console.progress_spinner(console, "Starting") as update:
        update("Working")


def test_handle_missing_api_key_calls_print(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_print(
        console: Console,
        message: str,
        *,
        fixes: list[str] | None = None,
        details: str | None = None,
    ) -> None:
        captured["console"] = console
        captured["message"] = message
        captured["fixes"] = fixes or []
        captured["details"] = details

    monkeypatch.setattr(errors, "print_cli_error", fake_print)
    console = Console()
    errors.handle_missing_api_key(console, provider="anthropic")
    assert captured["console"] is console
    assert captured["message"] == "ANTHROPIC_API_KEY is not set"
    assert captured["details"] is None
    fixes = cast(list[str], captured["fixes"])
    assert fixes[0].startswith("Add ANTHROPIC_API_KEY")


def test_handle_invalid_dataset_calls_print(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_print(
        console: Console,
        message: str,
        *,
        fixes: list[str] | None = None,
        details: str | None = None,
    ) -> None:
        captured["message"] = message
        captured["fixes"] = fixes or []
        captured["details"] = details

    monkeypatch.setattr(errors, "print_cli_error", fake_print)
    error = ValueError("bad dataset")
    errors.handle_invalid_dataset(Console(), Path("data/sample.csv"), error)
    assert captured["message"] == "Failed to load dataset: sample.csv"
    assert captured["details"] == "bad dataset"
    fixes = cast(list[str], captured["fixes"])
    assert "Extension: .csv" in "\n".join(fixes)


@pytest.mark.parametrize(
    ("error", "expected_fix"),
    [
        (RuntimeError("api_key missing"), "Check your API key configuration:"),
        (RuntimeError("rate limit hit"), "Rate limit exceeded. Try these options:"),
        (RuntimeError("timeout happened"), "Request timed out. Try these solutions:"),
        (RuntimeError("boom"), "Troubleshooting steps:"),
    ],
)
def test_handle_evaluation_error_fix_selection(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected_fix: str,
) -> None:
    captured: dict[str, object] = {}

    def fake_print(
        console: Console,
        message: str,
        *,
        fixes: list[str] | None = None,
        details: str | None = None,
    ) -> None:
        captured["message"] = message
        captured["fixes"] = fixes or []
        captured["details"] = details

    monkeypatch.setattr(errors, "print_cli_error", fake_print)
    errors.handle_evaluation_error(Console(), error)
    assert captured["message"] == "Evaluation failed"
    fixes = cast(list[str], captured["fixes"])
    assert fixes[0] == expected_fix
    assert captured["details"] == str(error)


def test_handle_evaluation_error_verbose(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_print(
        console: Console,
        message: str,
        *,
        fixes: list[str] | None = None,
        details: str | None = None,
    ) -> None:
        captured["details"] = details

    monkeypatch.setattr(errors, "print_cli_error", fake_print)
    errors.handle_evaluation_error(Console(), RuntimeError("boom"), verbose=True)
    assert captured["details"] == "RuntimeError: boom"


def test_handle_storage_error_calls_print(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_print(
        console: Console,
        message: str,
        *,
        fixes: list[str] | None = None,
        details: str | None = None,
    ) -> None:
        captured["message"] = message
        captured["fixes"] = fixes or []
        captured["details"] = details

    monkeypatch.setattr(errors, "print_cli_error", fake_print)
    errors.handle_storage_error(Console(), Path("results/output.json"), OSError("disk full"))
    assert captured["message"] == "Failed to save to: output.json"
    assert captured["details"] == "disk full"
    fixes = cast(list[str], captured["fixes"])
    # Use str(Path(...)) for cross-platform path comparison
    expected_path = str(Path("results/output.json"))
    assert f"Path: {expected_path}" in "\n".join(fixes)
