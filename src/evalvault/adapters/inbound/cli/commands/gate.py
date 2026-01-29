"""Quality gate command registration for EvalVault CLI."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.phoenix_support import get_phoenix_trace_url
from evalvault.config.settings import Settings

from ..utils.formatters import format_diff, format_score, format_status
from ..utils.options import db_option


def register_gate_commands(app: typer.Typer, console: Console) -> None:
    """Attach the `gate` command to the given Typer app."""

    @app.command()
    def gate(  # noqa: PLR0912, PLR0913 - CLI 옵션 유지
        run_id: str = typer.Argument(..., help="Run ID to check"),
        threshold: list[str] = typer.Option(
            None,
            "--threshold",
            "-t",
            help="Custom threshold in format 'metric:value' (e.g., 'faithfulness:0.8')",
        ),
        baseline: str | None = typer.Option(
            None,
            "--baseline",
            "-b",
            help="Baseline run ID for regression detection",
        ),
        fail_on_regression: float = typer.Option(
            0.05,
            "--fail-on-regression",
            "-r",
            help="Fail if metric drops by more than this amount (default: 0.05)",
        ),
        output_format: str = typer.Option(
            "table",
            "--format",
            "-f",
            help="Output format: table, json, or github-actions",
        ),
        db_path: Path = db_option(help_text="Database path"),
    ) -> None:
        """Quality gate check for CI/CD pipelines."""

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)

        try:
            run = storage.get_run(run_id)
        except KeyError:
            if output_format == "json":
                console.print(
                    json.dumps({"status": "error", "message": f"Run not found: {run_id}"})
                )
            elif output_format == "github-actions":
                console.print(f"::error::Run not found: {run_id}")
            else:
                console.print(f"[red]Error: Run not found: {run_id}[/red]")
            raise typer.Exit(3)

        custom_thresholds = {}
        if threshold:
            for entry in threshold:
                if ":" not in entry:
                    console.print(f"[red]Error: Invalid threshold format: {entry}[/red]")
                    console.print("[dim]Use format: metric:value (e.g., faithfulness:0.8)[/dim]")
                    raise typer.Exit(1)
                metric, value = entry.split(":", 1)
                try:
                    custom_thresholds[metric.strip()] = float(value.strip())
                except ValueError:
                    console.print(f"[red]Error: Invalid threshold value: {value}[/red]")
                    raise typer.Exit(1)

        thresholds = dict.fromkeys(run.metrics_evaluated, 0.7)
        thresholds.update(run.thresholds or {})
        thresholds.update(custom_thresholds)

        baseline_run = None
        if baseline:
            try:
                baseline_run = storage.get_run(baseline)
            except KeyError:
                message = f"Baseline run not found: {baseline}"
                if output_format == "json":
                    console.print(json.dumps({"status": "error", "message": message}))
                elif output_format == "github-actions":
                    console.print(f"::error::{message}")
                else:
                    console.print(f"[red]Error: {message}[/red]")
                raise typer.Exit(3)

        results = []
        all_passed = True
        regression_detected = False

        for metric in run.metrics_evaluated:
            avg_score = run.get_avg_score(metric)
            thresh = thresholds.get(metric, 0.7)
            passed = avg_score >= thresh
            metric_result = {
                "metric": metric,
                "score": avg_score,
                "threshold": thresh,
                "passed": passed,
            }
            if not passed:
                all_passed = False

            if baseline_run and metric in baseline_run.metrics_evaluated:
                baseline_score = baseline_run.get_avg_score(metric)
                diff = avg_score - baseline_score
                metric_result["baseline_score"] = baseline_score
                metric_result["diff"] = diff
                metric_result["regression"] = diff < -fail_on_regression
                if metric_result["regression"]:
                    regression_detected = True

            results.append(metric_result)

        trace_url = get_phoenix_trace_url(getattr(run, "tracker_metadata", None))

        if output_format == "json":
            output_data = {
                "run_id": run_id,
                "status": "passed" if all_passed and not regression_detected else "failed",
                "all_thresholds_passed": all_passed,
                "regression_detected": regression_detected,
                "results": results,
            }
            if baseline:
                output_data["baseline_id"] = baseline
                output_data["fail_on_regression"] = fail_on_regression
            if trace_url:
                output_data["phoenix_trace_url"] = trace_url
            console.print(json.dumps(output_data, indent=2))
        elif output_format == "github-actions":
            for metric_result in results:
                status = "✅" if metric_result["passed"] else "❌"
                reg_status = ""
                if "regression" in metric_result:
                    reg_status = " (📉 REGRESSION)" if metric_result["regression"] else ""
                console.print(
                    f"{status} {metric_result['metric']}: {metric_result['score']:.3f} "
                    f"(threshold: {metric_result['threshold']:.2f}){reg_status}"
                )

            console.print(
                f"::set-output name=passed::{str(all_passed and not regression_detected).lower()}"
            )
            console.print(f"::set-output name=pass_rate::{run.pass_rate:.3f}")
            if trace_url:
                console.print(f"::notice::Phoenix Trace: {trace_url}")
            if not all_passed:
                failed_metrics = [r["metric"] for r in results if not r["passed"]]
                console.print(
                    f"::error::Quality gate failed. Metrics below threshold: {', '.join(failed_metrics)}"
                )
            if regression_detected:
                regressed_metrics = [r["metric"] for r in results if r.get("regression")]
                console.print(f"::warning::Regression detected in: {', '.join(regressed_metrics)}")
        else:
            console.print(f"\n[bold]Quality Gate Check: {run_id}[/bold]\n")
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Metric")
            table.add_column("Score", justify="right")
            table.add_column("Threshold", justify="right")
            table.add_column("Status", justify="center")
            if baseline_run:
                table.add_column("Baseline", justify="right")
                table.add_column("Diff", justify="right")
                table.add_column("Regression", justify="center")

            for metric_result in results:
                score_text = format_score(metric_result["score"], metric_result["passed"])
                status = format_status(metric_result["passed"])
                if baseline_run:
                    baseline_score = metric_result.get("baseline_score", "-")
                    baseline_display = (
                        format_score(baseline_score)
                        if isinstance(baseline_score, float)
                        else str(baseline_score)
                    )
                    diff_value = metric_result.get("diff")
                    diff_str = format_diff(diff_value if isinstance(diff_value, float) else None)
                    reg_status = format_status(
                        not metric_result.get("regression", False),
                        success_text="NO",
                        failure_text="YES",
                    )
                    table.add_row(
                        metric_result["metric"],
                        score_text,
                        f"{metric_result['threshold']:.2f}",
                        status,
                        baseline_display,
                        diff_str,
                        reg_status,
                    )
                else:
                    table.add_row(
                        metric_result["metric"],
                        score_text,
                        f"{metric_result['threshold']:.2f}",
                        status,
                    )

            console.print(table)
            if trace_url:
                console.print(f"[dim]Phoenix Trace: {trace_url}[/dim]")
            if all_passed and not regression_detected:
                console.print("\n[bold green]✅ Quality gate PASSED[/bold green]")
            else:
                if not all_passed:
                    failed = [r["metric"] for r in results if not r["passed"]]
                    console.print("\n[bold red]❌ Quality gate FAILED[/bold red]")
                    console.print(f"[red]Failed metrics: {', '.join(failed)}[/red]")
                if regression_detected:
                    regressed = [r["metric"] for r in results if r.get("regression")]
                    console.print("\n[bold yellow]📉 Regression detected[/bold yellow]")
                    console.print(f"[yellow]Regressed metrics: {', '.join(regressed)}[/yellow]")
            console.print()

        if not all_passed:
            raise typer.Exit(1)
        if regression_detected:
            raise typer.Exit(2)


__all__ = ["register_gate_commands"]
