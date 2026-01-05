"""Common Typer option factories for CLI commands."""

from __future__ import annotations

from pathlib import Path

import typer

from evalvault.config.settings import Settings


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
    default: str | Path | None = None,
    help_text: str = "Path to SQLite database file.",
) -> Path | None:
    """Shared --db / -D option definition."""

    resolved_default = default if default is not None else Settings().evalvault_db_path
    normalized_default = _normalize_path(resolved_default)
    return typer.Option(
        normalized_default,
        "--db",
        "-D",
        help=help_text,
        show_default=normalized_default is not None,
    )


def memory_db_option(
    *,
    default: str | Path | None = Path("evalvault_memory.db"),
    help_text: str = "Path to Domain Memory SQLite database.",
) -> Path:
    """Shared option factory for the domain memory database path."""

    normalized_default = _normalize_path(default) or Path("evalvault_memory.db")
    return typer.Option(
        normalized_default,
        "--memory-db",
        "-M",
        help=help_text,
        show_default=True,
    )


def _normalize_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    if isinstance(value, Path):
        return value
    return Path(value)
