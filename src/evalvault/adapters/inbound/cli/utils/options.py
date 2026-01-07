"""Common Typer option factories for CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from evalvault.config.settings import Settings

# Sentinel value to detect when default is not provided
_UNSET: Any = object()


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
    default: str | Path | None = _UNSET,
    help_text: str = "Path to SQLite database file.",
) -> Path | None:
    """Shared --db / -D option definition."""

    resolved_default = Settings().evalvault_db_path if default is _UNSET else default
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
    default: str | Path | None = _UNSET,
    help_text: str = "Path to Domain Memory SQLite database.",
) -> Path | None:
    """Shared option factory for the domain memory database path."""

    resolved_default = Settings().evalvault_memory_db_path if default is _UNSET else default
    normalized_default = _normalize_path(resolved_default)
    return typer.Option(
        normalized_default,
        "--memory-db",
        "-M",
        help=help_text,
        show_default=normalized_default is not None,
    )


def _normalize_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    if isinstance(value, Path):
        return value
    return Path(value)
