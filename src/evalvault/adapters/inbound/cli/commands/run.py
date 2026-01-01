"""`evalvault run` 명령 전용 Typer 등록 모듈."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from evalvault.adapters.outbound.dataset import get_loader
from evalvault.adapters.outbound.llm import get_llm_adapter
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.adapters.outbound.tracker.langfuse_adapter import LangfuseAdapter
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.services.evaluator import RagasEvaluator

from ..utils.formatters import format_score, format_status
from ..utils.options import db_option, profile_option
from ..utils.validators import parse_csv_option, validate_choices


def register_run_commands(
    app: typer.Typer,
    console: Console,
    available_metrics: Sequence[str],
) -> None:
    """Attach the legacy `run` command to the given Typer app."""

    @app.command()
    def run(  # noqa: PLR0913 - CLI arguments intentionally flat
        dataset: Path = typer.Argument(
            ...,
            help="Path to dataset file (CSV, Excel, or JSON).",
            exists=True,
            readable=True,
        ),
        metrics: str = typer.Option(
            "faithfulness,answer_relevancy",
            "--metrics",
            "-m",
            help="Comma-separated list of metrics to evaluate.",
        ),
        profile: str | None = profile_option(
            help_text="Model profile (dev, prod, openai). Overrides .env setting.",
        ),
        model: str | None = typer.Option(
            None,
            "--model",
            help="Model to use for evaluation (overrides profile).",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file for results (JSON format).",
        ),
        langfuse: bool = typer.Option(
            False,
            "--langfuse",
            "-l",
            help="Log results to Langfuse.",
        ),
        db_path: Path | None = db_option(
            default=None,
            help_text="Path to SQLite database file for storing results.",
        ),
        verbose: bool = typer.Option(
            False,
            "--verbose",
            help="Show detailed output.",
        ),
        parallel: bool = typer.Option(
            False,
            "--parallel",
            help="Enable parallel evaluation for faster processing.",
        ),
        batch_size: int = typer.Option(
            5,
            "--batch-size",
            help="Batch size for parallel evaluation (default: 5).",
        ),
    ) -> None:
        """Run RAG evaluation on a dataset."""
        metric_list = parse_csv_option(metrics)
        validate_choices(metric_list, available_metrics, console, value_label="metric")

        settings = Settings()

        # Apply profile (CLI > .env > default)
        profile_name = profile or settings.evalvault_profile
        if profile_name:
            settings = apply_profile(settings, profile_name)

        # Override model if specified
        if model:
            if settings.llm_provider == "ollama":
                settings.ollama_model = model
            else:
                settings.openai_model = model

        if settings.llm_provider == "openai" and not settings.openai_api_key:
            console.print("[red]Error:[/red] OPENAI_API_KEY not set.")
            console.print("Set it in your .env file or use --profile dev for Ollama.")
            raise typer.Exit(1)

        display_model = (
            f"ollama/{settings.ollama_model}"
            if settings.llm_provider == "ollama"
            else settings.openai_model
        )

        console.print("\n[bold]EvalVault[/bold] - RAG Evaluation")
        console.print(f"Dataset: [cyan]{dataset}[/cyan]")
        console.print(f"Metrics: [cyan]{', '.join(metric_list)}[/cyan]")
        console.print(f"Provider: [cyan]{settings.llm_provider}[/cyan]")
        console.print(f"Model: [cyan]{display_model}[/cyan]")
        if profile_name:
            console.print(f"Profile: [cyan]{profile_name}[/cyan]")
        console.print()

        # Load dataset
        with console.status("[bold green]Loading dataset..."):
            try:
                loader = get_loader(dataset)
                ds = loader.load(dataset)
                console.print(f"[green]Loaded {len(ds)} test cases[/green]")
            except Exception as exc:  # pragma: no cover - user feedback path
                console.print(f"[red]Error loading dataset:[/red] {exc}")
                raise typer.Exit(1) from exc

        evaluator = RagasEvaluator()

        if ds.thresholds:
            console.print("[dim]Thresholds from dataset:[/dim]")
            for metric, threshold in ds.thresholds.items():
                console.print(f"  [dim]{metric}: {threshold}[/dim]")
            console.print()

        status_msg = "[bold green]Running evaluation..."
        if parallel:
            status_msg = f"[bold green]Running parallel evaluation (batch_size={batch_size})..."
        with console.status(status_msg):
            try:
                result = asyncio.run(
                    evaluator.evaluate(
                        dataset=ds,
                        metrics=metric_list,
                        llm=get_llm_adapter(settings),
                        thresholds=None,
                        parallel=parallel,
                        batch_size=batch_size,
                    )
                )
            except Exception as exc:  # pragma: no cover - surfaced to CLI
                console.print(f"[red]Error during evaluation:[/red] {exc}")
                raise typer.Exit(1) from exc

        _display_results(result, console, verbose)

        if langfuse:
            _log_to_langfuse(settings, result, console)
        if db_path:
            _save_to_db(db_path, result, console)
        if output:
            _save_results(output, result, console)

    def _display_results(result, console: Console, verbose: bool = False) -> None:
        """Display evaluation results in a formatted table."""
        duration = result.duration_seconds
        duration_str = f"{duration:.2f}s" if duration is not None else "N/A"

        summary = f"""
[bold]Evaluation Summary[/bold]
  Run ID: {result.run_id}
  Dataset: {result.dataset_name} v{result.dataset_version}
  Model: {result.model_name}
  Duration: {duration_str}

[bold]Results[/bold]
  Total Test Cases: {result.total_test_cases}
  Passed: [green]{result.passed_test_cases}[/green]
  Failed: [red]{result.total_test_cases - result.passed_test_cases}[/red]
  Pass Rate: {"[green]" if result.pass_rate >= 0.7 else "[red]"}{result.pass_rate:.1%}[/]
"""
        console.print(Panel(summary, title="Evaluation Results", border_style="blue"))

        table = Table(title="Metric Scores", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="bold")
        table.add_column("Average Score", justify="right")
        table.add_column("Threshold", justify="right")
        table.add_column("Status", justify="center")

        for metric in result.metrics_evaluated:
            avg_score = result.get_avg_score(metric)
            threshold = result.thresholds.get(metric, 0.7)
            passed = avg_score >= threshold
            table.add_row(
                metric,
                format_score(avg_score, passed),
                f"{threshold:.2f}",
                format_status(passed),
            )

        console.print(table)

        if verbose:
            console.print("\n[bold]Detailed Results[/bold]\n")
            for tc_result in result.results:
                status = format_status(tc_result.all_passed)
                console.print(f"  {tc_result.test_case_id}: {status}")
                for metric in tc_result.metrics:
                    m_status = format_status(metric.passed, success_text="+", failure_text="-")
                    score = format_score(metric.score, metric.passed)
                    console.print(
                        f"    {m_status} {metric.name}: {score} (threshold: {metric.threshold})"
                    )

    def _log_to_langfuse(settings: Settings, result, console: Console) -> None:
        """Log evaluation results to Langfuse."""
        if not settings.langfuse_public_key or not settings.langfuse_secret_key:
            console.print(
                "[yellow]Warning:[/yellow] Langfuse credentials not configured. Skipping Langfuse logging."
            )
            return

        with console.status("[bold green]Logging to Langfuse..."):
            try:
                tracker = LangfuseAdapter(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
                trace_id = tracker.log_evaluation_run(result)
                console.print(f"[green]Logged to Langfuse[/green] (trace_id: {trace_id})")
            except Exception as exc:  # pragma: no cover - telemetry best-effort
                console.print(f"[yellow]Warning:[/yellow] Failed to log to Langfuse: {exc}")

    def _save_to_db(db_path: Path, result, console: Console) -> None:
        """Persist evaluation run to SQLite database."""
        with console.status(f"[bold green]Saving to database {db_path}..."):
            try:
                storage = SQLiteStorageAdapter(db_path=db_path)
                storage.save_run(result)
                console.print(f"[green]Results saved to database: {db_path}[/green]")
                console.print(f"[dim]Run ID: {result.run_id}[/dim]")
            except Exception as exc:  # pragma: no cover - persistence errors
                console.print(f"[red]Error saving to database:[/red] {exc}")

    def _save_results(output: Path, result, console: Console) -> None:
        """Write evaluation summary to disk."""
        with console.status(f"[bold green]Saving to {output}..."):
            try:
                data = result.to_summary_dict()
                data["results"] = [
                    {
                        "test_case_id": r.test_case_id,
                        "all_passed": r.all_passed,
                        "metrics": [
                            {
                                "name": m.name,
                                "score": m.score,
                                "threshold": m.threshold,
                                "passed": m.passed,
                            }
                            for m in r.metrics
                        ],
                    }
                    for r in result.results
                ]

                with open(output, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)

                console.print(f"[green]Results saved to {output}[/green]")
            except Exception as exc:  # pragma: no cover - filesystem errors
                console.print(f"[red]Error saving results:[/red] {exc}")


__all__ = ["register_run_commands"]
