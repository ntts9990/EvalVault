"""Shared validation helpers for CLI commands."""

from __future__ import annotations

from collections.abc import Sequence

import typer
from rich.console import Console


def parse_csv_option(value: str | None) -> list[str]:
    """Parse a comma-separated CLI option."""

    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def validate_choices(
    items: Sequence[str],
    allowed: Sequence[str],
    console: Console,
    *,
    value_label: str = "value",
    available_label: str | None = None,
) -> None:
    """Validate that every item is part of the allowed collection."""

    if not items:
        return

    allowed_set = set(allowed)
    invalid = [item for item in items if item not in allowed_set]
    if invalid:
        label = available_label or value_label
        console.print(
            f"[red]Error:[/red] Invalid {value_label}s: {', '.join(sorted(set(invalid)))}"
        )
        console.print(f"Available {label}s: {', '.join(allowed)}")
        raise typer.Exit(1)


def validate_choice(
    value: str,
    allowed: Sequence[str],
    console: Console,
    *,
    value_label: str = "value",
) -> None:
    """Validate a single choice."""

    if value in allowed:
        return

    console.print(f"[red]Error:[/red] Invalid {value_label}: {value}")
    console.print(f"Available {value_label}s: {', '.join(allowed)}")
    raise typer.Exit(1)
