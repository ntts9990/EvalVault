"""CLI interface for EvalVault using Typer."""

# Fix SSL certificate issues on macOS with uv-managed Python
try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass  # truststore not installed, use default SSL

import base64
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from evalvault.config.settings import Settings, apply_profile

from .commands.agent import register_agent_commands
from .commands.analyze import register_analyze_commands
from .commands.benchmark import create_benchmark_app
from .commands.domain import create_domain_app
from .commands.experiment import register_experiment_commands
from .commands.gate import register_gate_commands
from .commands.generate import register_generate_commands
from .commands.history import register_history_commands
from .commands.kg import create_kg_app
from .commands.pipeline import register_pipeline_commands
from .commands.run import register_run_commands

app = typer.Typer(
    name="evalvault",
    help="RAG evaluation system using Ragas with Langfuse tracing.",
    add_completion=False,
)
console = Console()

# Available metrics
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
):
    """EvalVault - RAG evaluation system."""
    pass


@app.command()
def metrics():
    """List available evaluation metrics."""
    console.print("\n[bold]Available Metrics[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Description")
    table.add_column("Requires Ground Truth", justify="center")

    table.add_row(
        "faithfulness",
        "Measures factual accuracy of the answer based on contexts",
        "[red]No[/red]",
    )
    table.add_row(
        "answer_relevancy",
        "Measures how relevant the answer is to the question",
        "[red]No[/red]",
    )
    table.add_row(
        "context_precision",
        "Measures ranking quality of retrieved contexts",
        "[green]Yes[/green]",
    )
    table.add_row(
        "context_recall",
        "Measures if all relevant info is in retrieved contexts",
        "[green]Yes[/green]",
    )
    table.add_row(
        "insurance_term_accuracy",
        "Measures if insurance terms in answer are grounded in contexts",
        "[red]No[/red]",
    )

    console.print(table)
    console.print("\n[dim]Use --metrics flag with 'run' command to specify metrics.[/dim]")
    console.print(
        "[dim]Example: evalvault run data.csv --metrics faithfulness,answer_relevancy[/dim]\n"
    )


@app.command("langfuse-dashboard")
def langfuse_dashboard(
    limit: int = typer.Option(5, help="표시할 Langfuse trace 개수"),
    event_type: str = typer.Option("ragas_evaluation", help="필터링할 event_type"),
):
    """Langfuse에서 평가/그래프 trace를 조회해 요약."""
    settings = Settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        console.print("[red]Langfuse credentials not configured.[/red]")
        raise typer.Exit(1)

    try:
        traces = _fetch_langfuse_traces(
            host=settings.langfuse_host,
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            event_type=event_type,
            limit=limit,
        )
    except HTTPError as exc:
        console.print(
            f"[yellow]Langfuse public API not available (HTTP {exc.code}). "
            "Skipping dashboard output.[/yellow]"
        )
        return
    except Exception as exc:
        console.print(f"[red]Failed to fetch Langfuse traces:[/red] {exc}")
        raise typer.Exit(1)

    if not traces:
        console.print("[yellow]No traces found for the given event_type.[/yellow]")
        return

    table = Table(
        title=f"Langfuse Traces ({event_type})", show_header=True, header_style="bold cyan"
    )
    table.add_column("Trace ID")
    table.add_column("Dataset")
    table.add_column("Model")
    table.add_column("Pass Rate", justify="right")
    table.add_column("Total Cases", justify="right")
    table.add_column("Created At")

    for trace in traces:
        metadata = trace.get("metadata", {})
        dataset_name = metadata.get("dataset_name") or metadata.get("source", "N/A")
        model_name = metadata.get("model_name", "N/A")
        pass_rate = metadata.get("pass_rate")
        total_cases = metadata.get("total_test_cases") or metadata.get("documents_processed")
        created_at = trace.get("createdAt") or trace.get("created_at", "")
        table.add_row(
            trace.get("id", "unknown"),
            str(dataset_name),
            str(model_name),
            f"{pass_rate:.2f}" if isinstance(pass_rate, int | float) else "N/A",
            str(total_cases) if total_cases is not None else "N/A",
            created_at,
        )

    console.print(table)


def _fetch_langfuse_traces(
    host: str,
    public_key: str,
    secret_key: str,
    event_type: str,
    limit: int,
) -> list[dict]:
    """Langfuse Public API를 호출해 trace 리스트를 가져온다."""
    base = host.rstrip("/")
    url = f"{base}/api/public/traces/search"
    payload = {
        "query": {"metadata.event_type": {"equals": event_type}},
        "limit": limit,
        "orderBy": {"createdAt": "desc"},
    }
    auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode("utf-8")
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth}",
        },
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("data", data if isinstance(data, list) else [])


@app.command()
def config():
    """Show current configuration."""
    settings = Settings()

    # Apply profile if set
    profile_name = settings.evalvault_profile
    if profile_name:
        settings = apply_profile(settings, profile_name)

    console.print("\n[bold]Current Configuration[/bold]\n")

    # Profile section
    console.print("[bold cyan]Profile[/bold cyan]")
    table_profile = Table(show_header=False, box=None, padding=(0, 2))
    table_profile.add_column("Setting", style="bold")
    table_profile.add_column("Value")

    table_profile.add_row(
        "Active Profile",
        f"[cyan]{profile_name}[/cyan]" if profile_name else "[dim]None (using defaults)[/dim]",
    )
    table_profile.add_row("LLM Provider", settings.llm_provider)

    console.print(table_profile)
    console.print()

    # Provider-specific settings
    console.print("[bold cyan]LLM Settings[/bold cyan]")
    table_llm = Table(show_header=False, box=None, padding=(0, 2))
    table_llm.add_column("Setting", style="bold")
    table_llm.add_column("Value")

    if settings.llm_provider == "ollama":
        table_llm.add_row("Ollama Model", settings.ollama_model)
        table_llm.add_row("Ollama Embedding", settings.ollama_embedding_model)
        table_llm.add_row("Ollama URL", settings.ollama_base_url)
        table_llm.add_row("Ollama Timeout", f"{settings.ollama_timeout}s")
        if settings.ollama_think_level:
            table_llm.add_row("Think Level", settings.ollama_think_level)
    else:
        api_key_status = "[green]Set[/green]" if settings.openai_api_key else "[red]Not set[/red]"
        table_llm.add_row("OpenAI API Key", api_key_status)
        table_llm.add_row("OpenAI Model", settings.openai_model)
        table_llm.add_row("OpenAI Embedding", settings.openai_embedding_model)
        table_llm.add_row(
            "OpenAI Base URL",
            settings.openai_base_url or "[dim]Default[/dim]",
        )

    console.print(table_llm)
    console.print()

    # Langfuse settings
    console.print("[bold cyan]Tracking[/bold cyan]")
    table_tracking = Table(show_header=False, box=None, padding=(0, 2))
    table_tracking.add_column("Setting", style="bold")
    table_tracking.add_column("Value")

    langfuse_status = (
        "[green]Configured[/green]"
        if settings.langfuse_public_key and settings.langfuse_secret_key
        else "[yellow]Not configured[/yellow]"
    )
    table_tracking.add_row("Langfuse", langfuse_status)
    table_tracking.add_row("Langfuse Host", settings.langfuse_host)

    console.print(table_tracking)
    console.print()

    # Available profiles
    console.print("[bold cyan]Available Profiles[/bold cyan]")
    try:
        from evalvault.config.model_config import get_model_config

        model_config = get_model_config()
        table_profiles = Table(show_header=True, header_style="bold")
        table_profiles.add_column("Profile")
        table_profiles.add_column("LLM")
        table_profiles.add_column("Embedding")
        table_profiles.add_column("Description")

        for name, prof in model_config.profiles.items():
            is_active = name == profile_name
            prefix = "[cyan]* " if is_active else "  "
            suffix = "[/cyan]" if is_active else ""
            table_profiles.add_row(
                f"{prefix}{name}{suffix}",
                prof.llm.model,
                prof.embedding.model,
                prof.description,
            )

        console.print(table_profiles)
    except FileNotFoundError:
        console.print("[yellow]  config/models.yaml not found[/yellow]")

    console.print()
    console.print("[dim]Tip: Use --profile to override, e.g.:[/dim]")
    console.print("[dim]  evalvault run data.json --profile prod --metrics faithfulness[/dim]\n")


# ============================================================================
# Analysis Commands
# ============================================================================


# ============================================================================
# Web UI Command
# ============================================================================


@app.command()
def web(
    port: int = typer.Option(
        8501,
        "--port",
        "-p",
        help="Port to run the web server on.",
    ),
    host: str = typer.Option(
        "localhost",
        "--host",
        "-h",
        help="Host to bind the web server to.",
    ),
    db_path: Path = typer.Option(
        "evalvault.db",
        "--db",
        help="Path to SQLite database file.",
    ),
):
    """Launch the EvalVault Web UI (Streamlit dashboard).

    Examples:
        evalvault web
        evalvault web --port 8502
        evalvault web --host 0.0.0.0 --port 8080
    """
    import subprocess
    import sys

    console.print("\n[bold]EvalVault Web UI[/bold]\n")
    console.print(f"Starting server at [cyan]http://{host}:{port}[/cyan]")
    console.print(f"Database: [dim]{db_path}[/dim]")
    console.print("\n[dim]Press Ctrl+C to stop the server.[/dim]\n")

    try:
        # Get the path to the Streamlit app
        from evalvault.adapters.inbound.web import app as web_app_module

        app_path = Path(web_app_module.__file__).parent / "app.py"

        # Run Streamlit
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(app_path),
                "--server.port",
                str(port),
                "--server.address",
                host,
                "--",
                "--db",
                str(db_path),
            ],
            check=True,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped.[/yellow]")
    except ImportError:
        console.print("[red]Error:[/red] Streamlit not installed.")
        console.print("Install with: [cyan]uv add streamlit[/cyan]")
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error starting web server:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
