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

from .commands.agent import register_agent_commands
from .commands.analyze import register_analyze_commands
from .commands.benchmark import create_benchmark_app
from .commands.config import register_config_commands
from .commands.domain import create_domain_app
from .commands.experiment import register_experiment_commands
from .commands.gate import register_gate_commands
from .commands.generate import register_generate_commands
from .commands.history import register_history_commands
from .commands.kg import create_kg_app
from .commands.langfuse import register_langfuse_commands
from .commands.pipeline import register_pipeline_commands
from .commands.run import register_run_commands
from .commands.web import register_web_command

app = typer.Typer(
    name="evalvault",
    help="RAG evaluation system using Ragas with Langfuse tracing.",
    add_completion=False,
)
console = Console()

AVAILABLE_METRICS = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "factual_correctness",
    "semantic_similarity",
    "insurance_term_accuracy",
]

register_run_commands(app, console, AVAILABLE_METRICS)
register_pipeline_commands(app, console)
register_history_commands(app, console)
register_analyze_commands(app, console)
register_generate_commands(app, console)
register_gate_commands(app, console)
register_agent_commands(app, console)
register_experiment_commands(app, console)
register_config_commands(app, console)
register_langfuse_commands(app, console)
register_web_command(app, console)

kg_app = create_kg_app(console)
app.add_typer(kg_app, name="kg")
domain_app = create_domain_app(console)
app.add_typer(domain_app, name="domain")
benchmark_app = create_benchmark_app(console)
app.add_typer(benchmark_app, name="benchmark")


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
