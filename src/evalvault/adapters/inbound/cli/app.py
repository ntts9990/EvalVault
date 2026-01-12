"""CLI interface for EvalVault using Typer."""

# Fix SSL certificate issues on macOS with uv-managed Python
try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:  # pragma: no cover - optional dependency
    pass

from importlib.metadata import version as get_version

import typer
from rich import print as rprint
from rich.console import Console

from evalvault.domain.metrics.registry import list_metric_names

from .commands import attach_sub_apps, register_all_commands


def _get_package_version() -> str:
    """Get package version from metadata, fallback to 'dev' if not installed."""
    try:
        return get_version("evalvault")
    except Exception:  # pragma: no cover
        return "dev"


app = typer.Typer(
    name="evalvault",
    help="RAG evaluation system using Ragas with Langfuse tracing.",
    add_completion=False,
)
console = Console()

AVAILABLE_METRICS = list_metric_names()

register_all_commands(app, console, available_metrics=AVAILABLE_METRICS)
attach_sub_apps(app, console)


def version_callback(value: bool):
    """Print version and exit."""

    if value:
        pkg_version = _get_package_version()
        rprint(f"[bold]EvalVault[/bold] version [cyan]{pkg_version}[/cyan]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """EvalVault - RAG evaluation system."""


if __name__ == "__main__":  # pragma: no cover
    app()
