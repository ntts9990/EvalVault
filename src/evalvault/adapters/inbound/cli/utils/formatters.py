"""Shared formatting helpers for CLI output."""

from __future__ import annotations


def format_status(passed: bool, success_text: str = "PASS", failure_text: str = "FAIL") -> str:
    """Return a colorized status string."""

    return f"[green]{success_text}[/green]" if passed else f"[red]{failure_text}[/red]"


def format_score(value: float | None, passed: bool | None = None, precision: int = 3) -> str:
    """Return a formatted metric score."""

    if value is None:
        return "-"

    if passed is True:
        color = "green"
    elif passed is False:
        color = "red"
    else:
        color = "cyan"
    return f"[{color}]{value:.{precision}f}[/{color}]"


def format_diff(value: float | None, precision: int = 3) -> str:
    """Format a signed difference with color coding."""

    if value is None:
        return "-"
    color = "green" if value >= 0 else "red"
    return f"[{color}]{value:+.{precision}f}[/{color}]"
