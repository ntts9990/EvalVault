"""History/compare/export commands for the EvalVault CLI."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter


def register_history_commands(app: typer.Typer, console: Console) -> None:
    """Attach history/compare/export commands to the root Typer app."""

    @app.command()
    def history(
        limit: int = typer.Option(
            10,
            "--limit",
            "-n",
            help="Maximum number of runs to show.",
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
        db_path: Path = typer.Option(
            Path("evalvault.db"),
            "--db",
            help="Path to database file.",
        ),
    ) -> None:
        """Show evaluation run history."""
        console.print("\n[bold]Evaluation History[/bold]\n")

        storage = SQLiteStorageAdapter(db_path=db_path)
        runs = storage.list_runs(limit=limit, dataset_name=dataset, model_name=model)

        if not runs:
            console.print("[yellow]No evaluation runs found.[/yellow]\n")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Run ID", style="dim")
        table.add_column("Dataset")
        table.add_column("Model")
        table.add_column("Started At")
        table.add_column("Pass Rate", justify="right")
        table.add_column("Test Cases", justify="right")

        for run in runs:
            pass_rate_color = "green" if run.pass_rate >= 0.7 else "red"
            table.add_row(
                run.run_id[:8] + "...",
                run.dataset_name,
                run.model_name,
                run.started_at.strftime("%Y-%m-%d %H:%M"),
                f"[{pass_rate_color}]{run.pass_rate:.1%}[/{pass_rate_color}]",
                str(run.total_test_cases),
            )

        console.print(table)
        console.print(f"\n[dim]Showing {len(runs)} of {limit} runs[/dim]\n")

    @app.command()
    def compare(
        run_id1: str = typer.Argument(..., help="First run ID to compare."),
        run_id2: str = typer.Argument(..., help="Second run ID to compare."),
        db_path: Path = typer.Option(
            Path("evalvault.db"),
            "--db",
            help="Path to database file.",
        ),
    ) -> None:
        """Compare two evaluation runs."""
        console.print("\n[bold]Comparing Evaluation Runs[/bold]\n")

        storage = SQLiteStorageAdapter(db_path=db_path)

        try:
            run1 = storage.get_run(run_id1)
            run2 = storage.get_run(run_id2)
        except KeyError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1) from exc

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric")
        table.add_column(f"Run 1\n{run_id1[:12]}...", justify="right")
        table.add_column(f"Run 2\n{run_id2[:12]}...", justify="right")
        table.add_column("Difference", justify="right")

        table.add_row("Dataset", run1.dataset_name, run2.dataset_name, "-")
        table.add_row("Model", run1.model_name, run2.model_name, "-")
        table.add_row(
            "Test Cases",
            str(run1.total_test_cases),
            str(run2.total_test_cases),
            str(run2.total_test_cases - run1.total_test_cases),
        )

        pass_rate_diff = run2.pass_rate - run1.pass_rate
        diff_color = "green" if pass_rate_diff > 0 else "red" if pass_rate_diff < 0 else "dim"
        table.add_row(
            "Pass Rate",
            f"{run1.pass_rate:.1%}",
            f"{run2.pass_rate:.1%}",
            f"[{diff_color}]{pass_rate_diff:+.1%}[/{diff_color}]",
        )

        for metric in run1.metrics_evaluated:
            if metric in run2.metrics_evaluated:
                score1 = run1.get_avg_score(metric)
                score2 = run2.get_avg_score(metric)
                diff = score2 - score1 if score1 is not None and score2 is not None else None
                diff_str = (
                    f"[{'green' if diff and diff > 0 else 'red' if diff and diff < 0 else 'dim'}]{diff:+.3f}[/{'green' if diff and diff > 0 else 'red' if diff and diff < 0 else 'dim'}]"
                    if diff is not None
                    else "-"
                )
                table.add_row(
                    f"Avg {metric}",
                    f"{score1:.3f}" if score1 is not None else "-",
                    f"{score2:.3f}" if score2 is not None else "-",
                    diff_str,
                )

        console.print(table)
        console.print()

    @app.command(name="export")
    def export_cmd(
        run_id: str = typer.Argument(..., help="Run ID to export."),
        output: Path = typer.Option(
            ...,
            "--output",
            "-o",
            help="Output file path (JSON format).",
        ),
        db_path: Path = typer.Option(
            Path("evalvault.db"),
            "--db",
            help="Path to database file.",
        ),
    ) -> None:
        """Export evaluation run to JSON file."""
        console.print(f"\n[bold]Exporting Run {run_id}[/bold]\n")

        storage = SQLiteStorageAdapter(db_path=db_path)

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
