"""CLI interface for EvalVault using Typer."""

# Fix SSL certificate issues on macOS with uv-managed Python
try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:  # pragma: no cover - optional dependency
    pass

import typer
from rich import print as rprint
from rich.console import Console

from .commands import attach_sub_apps, register_all_commands

app = typer.Typer(
    name="evalvault",
    help="RAG evaluation system using Ragas with Langfuse tracing.",
    add_completion=False,
)
console = Console()

AVAILABLE_METRICS: list[str] = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "factual_correctness",
    "semantic_similarity",
    "insurance_term_accuracy",
]

register_all_commands(app, console, available_metrics=AVAILABLE_METRICS)
attach_sub_apps(app, console)


def version_callback(value: bool):
    """Print version and exit."""

    if value:
        rprint("[bold]EvalVault[/bold] version [cyan]0.1.0[/cyan]")
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
