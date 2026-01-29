"""History/compare/export commands for the EvalVault CLI."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.phoenix_support import PhoenixExperimentResolver
from evalvault.config.settings import Settings

from ..utils.options import db_option

RUN_MODE_CHOICES = ("simple", "full")


def register_history_commands(app: typer.Typer, console: Console) -> None:
    """Attach history/compare/export commands to the root Typer app."""

    @app.command()
    def history(
        limit: int = typer.Option(
            10,
            "--limit",
            "-n",
            help="Maximum number of runs to show (default: 10).",
        ),
        dataset: str | None = typer.Option(
            None,
            "--dataset",
            "-d",
            help="Filter by dataset name.",
        ),
        model: str | None = typer.Option(
            None,
            "--model",
            "-m",
            help="Filter by model name.",
        ),
        mode: str | None = typer.Option(
            None,
            "--mode",
            help="Filter by run mode: 'simple' or 'full'.",
        ),
        db_path: Path | None = db_option(help_text="Path to database file."),
    ) -> None:
        """Show evaluation run history.

        Display past evaluation runs with pass rates, test case counts, and
        optional Phoenix experiment metrics.

        \b
        Examples:
          # Show last 10 runs
          evalvault history

          # Show last 20 runs
          evalvault history -n 20

          # Filter by dataset name
          evalvault history -d insurance-qa

          # Filter by model
          evalvault history -m gpt-4

          # Filter by run mode
          evalvault history --mode simple

          # Use a custom database
          evalvault history --db custom.db

        \b
        See also:
          evalvault export   — Export run details to JSON
          evalvault run      — Create new evaluation runs
        """
        console.print("\n[bold]Evaluation History[/bold]\n")
        normalized_mode: str | None = None
        if mode:
            normalized_mode = mode.lower()
            if normalized_mode not in RUN_MODE_CHOICES:
                console.print(
                    "[red]Error:[/red] --mode must be one of: " + ", ".join(RUN_MODE_CHOICES)
                )
                raise typer.Exit(2)
        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        runs = storage.list_runs(limit=limit, dataset_name=dataset, model_name=model)
        if normalized_mode:
            runs = [
                run
                for run in runs
                if (getattr(run, "tracker_metadata", {}) or {}).get("run_mode") == normalized_mode
            ]

        if not runs:
            console.print("[yellow]No evaluation runs found.[/yellow]\n")
            return

        resolver: PhoenixExperimentResolver | None = None
        show_phoenix = False
        if runs:
            try:
                settings = Settings()
                resolver = PhoenixExperimentResolver(settings)
            except Exception:
                resolver = None
            if resolver and resolver.is_available:
                show_phoenix = any(
                    resolver.can_resolve(getattr(run, "tracker_metadata", None)) for run in runs
                )

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Run ID", style="dim")
        table.add_column("Dataset")
        table.add_column("Mode")
        table.add_column("Model")
        table.add_column("Started At")
        table.add_column("Pass Rate", justify="right")
        table.add_column("Test Cases", justify="right")
        if show_phoenix:
            table.add_column("Phoenix P@K", justify="right")
            table.add_column("Drift", justify="right")

        for run in runs:
            pass_rate_color = "green" if run.pass_rate >= 0.7 else "red"
            metadata = getattr(run, "tracker_metadata", {}) or {}
            run_mode_value = metadata.get("run_mode")
            mode_display = run_mode_value.capitalize() if run_mode_value else "-"
            row = [
                run.run_id[:8] + "...",
                run.dataset_name,
                mode_display,
                run.model_name,
                run.started_at.strftime("%Y-%m-%d %H:%M"),
                f"[{pass_rate_color}]{run.pass_rate:.1%}[/{pass_rate_color}]",
                str(run.total_test_cases),
            ]

            if show_phoenix and resolver:
                stats = resolver.get_stats(getattr(run, "tracker_metadata", None))
                precision_display = "-"
                drift_display = "-"
                if stats:
                    if stats.precision_at_k is not None:
                        precision_display = f"{stats.precision_at_k:.2f}"
                    if stats.drift_score is not None:
                        drift_display = f"{stats.drift_score:.2f}"
                row.extend([precision_display, drift_display])

            table.add_row(*row)

        console.print(table)
        console.print(f"\n[dim]Showing {len(runs)} of {limit} runs[/dim]\n")

    @app.command(name="export")
    def export_cmd(
        run_id: str = typer.Argument(..., help="Run ID to export."),
        output: Path = typer.Option(
            ...,
            "--output",
            "-o",
            help="Output file path (JSON format).",
        ),
        db_path: Path | None = db_option(help_text="Path to database file."),
    ) -> None:
        """Export evaluation run to JSON file.

        Export complete run details including all test case results, metrics,
        and scores to a JSON file for external analysis.

        \b
        Examples:
          # Export a run to JSON
          evalvault export abc12345 -o run_details.json

          # Export from a custom database
          evalvault export abc12345 -o results.json --db custom.db

        \b
        Output includes:
          • Run metadata (dataset, model, timestamps)
          • All test case results with metrics
          • Token usage and latency statistics

        \b
        See also:
          evalvault history  — List runs to find IDs
          evalvault compare  — Compare two runs
          evalvault analyze  — Interactive analysis
        """
        console.print(f"\n[bold]Exporting Run {run_id}[/bold]\n")

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)

        try:
            run = storage.get_run(run_id)
        except KeyError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1) from exc

        with console.status(f"[bold green]Exporting to {output}..."):
            data = run.to_summary_dict()
            data["results"] = [
                {
                    "test_case_id": r.test_case_id,
                    "all_passed": r.all_passed,
                    "tokens_used": r.tokens_used,
                    "latency_ms": r.latency_ms,
                    "metrics": [
                        {
                            "name": m.name,
                            "score": m.score,
                            "threshold": m.threshold,
                            "passed": m.passed,
                            "reason": m.reason,
                        }
                        for m in r.metrics
                    ],
                }
                for r in run.results
            ]

            output.write_text(
                json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
            )
            console.print(f"[green]Exported to {output}[/green]\n")


__all__ = ["register_history_commands"]
