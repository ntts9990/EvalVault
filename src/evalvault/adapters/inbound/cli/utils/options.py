"""Common Typer option factories for CLI commands."""

from __future__ import annotations

from pathlib import Path

import typer


def profile_option(
    *,
    help_text: str = "Profile name (e.g., dev, prod).",
    default: str | None = None,
) -> str | None:
    """Shared --profile / -p option definition."""

    return typer.Option(
        default,
        "--profile",
        "-p",
        help=help_text,
    )


def db_option(
    *,
    default: str | Path | None = Path("evalvault.db"),
    help_text: str = "Path to SQLite database file.",
) -> Path | None:
    """Shared --db / -D option definition."""

    normalized_default = _normalize_path(default)
    return typer.Option(
        normalized_default,
        "--db",
        "-D",
        help=help_text,
        show_default=normalized_default is not None,
    )


def _normalize_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    if isinstance(value, Path):
        return value
    return Path(value)
