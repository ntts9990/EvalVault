"""Common console helpers for CLI UX (errors, warnings, progress bars)."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn


def print_cli_error(
    console: Console,
    message: str,
    *,
    fixes: Iterable[str] | None = None,
    details: str | None = None,
) -> None:
    """Render a consistent error panel with optional fix list."""

    body = message
    if fixes:
        fix_lines = "\n".join(f"- {fix}" for fix in fixes)
        body += f"\n\n[bold]How to fix[/bold]\n{fix_lines}"
    if details:
        body += f"\n\n[dim]{details}[/dim]"
    console.print(Panel(body, title="Error", border_style="red"))


def print_cli_warning(
    console: Console,
    message: str,
    *,
    tips: Iterable[str] | None = None,
) -> None:
    """Render a warning panel for user-facing hints."""

    body = message
    if tips:
        tip_lines = "\n".join(f"- {tip}" for tip in tips)
        body += f"\n\n[bold]Tips[/bold]\n{tip_lines}"
    console.print(Panel(body, title="Warning", border_style="yellow"))


@contextmanager
def progress_spinner(console: Console, initial_message: str) -> Iterator[Callable[[str], None]]:
    """Show a spinner progress indicator and yield an updater callback."""

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        task_id = progress.add_task(initial_message, total=None)

        def update(description: str) -> None:
            progress.update(task_id, description=description)

        yield update
