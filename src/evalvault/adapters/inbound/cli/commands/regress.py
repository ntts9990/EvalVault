from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.inbound.cli.utils.analysis_io import write_json
from evalvault.adapters.outbound.analysis.statistical_adapter import (
    StatisticalAnalysisAdapter,
)
from evalvault.adapters.outbound.report.ci_report_formatter import (
    CIGateMetricRow,
    format_ci_regression_report,
)
from evalvault.adapters.outbound.report.pr_comment_formatter import (
    format_ci_gate_pr_comment,
)
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import Settings
from evalvault.domain.services.regression_gate_service import (
    RegressionGateReport,
    RegressionGateService,
    TestType,
)

from ..utils.formatters import format_diff, format_score, format_status
from ..utils.options import db_option
from ..utils.validators import parse_csv_option, validate_choice


def _coerce_test_type(value: str) -> TestType:
    if value == "t-test":
        return "t-test"
    return "mann-whitney"


OutputFormat = Literal["table", "json", "github-actions"]
CIGateOutputFormat = Literal["github", "gitlab", "json", "pr-comment"]


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _build_envelope(
    *,
    report: RegressionGateReport | None,
    status: str,
    started_at: datetime,
    finished_at: datetime,
    duration_ms: int,
    message: str | None = None,
    error_type: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "command": "regress",
        "version": 1,
        "status": status,
        "started_at": _format_timestamp(started_at),
        "finished_at": _format_timestamp(finished_at),
        "duration_ms": duration_ms,
        "artifacts": None,
        "data": report.to_dict() if report else None,
    }
    if message:
        payload["message"] = message
    if error_type:
        payload["error_type"] = error_type
    return payload


def register_regress_commands(app: typer.Typer, console: Console) -> None:
    @app.command()
    def regress(
        run_id: str = typer.Argument(..., help="Candidate run ID to check."),
        baseline: str = typer.Option(
            ...,
            "--baseline",
            "-b",
            help="Baseline run ID for regression detection.",
        ),
        fail_on_regression: float = typer.Option(
            0.05,
            "--fail-on-regression",
            "-r",
            help="Fail if metric drops by more than this amount (default: 0.05).",
        ),
        test: TestType = typer.Option(
            "t-test",
            "--test",
            "-t",
            help="Statistical test (t-test, mann-whitney).",
        ),
        metrics: str | None = typer.Option(
            None,
            "--metrics",
            "-m",
            help="Comma-separated list of metrics to check.",
        ),
        output_format: OutputFormat = typer.Option(
            "table",
            "--format",
            "-f",
            help="Output format: table, json, or github-actions.",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Write JSON summary to a file.",
        ),
        parallel: bool = typer.Option(
            True,
            "--parallel/--no-parallel",
            help="Enable parallel execution for metric checks.",
        ),
        concurrency: int = typer.Option(
            8,
            "--concurrency",
            help="Concurrency level when running in parallel.",
        ),
        db_path: Path | None = db_option(help_text="Database path"),
    ) -> None:
        started_at = datetime.now(UTC)
        if db_path is None:
            console.print("[red]Error:[/red] Database path is not configured.")
            raise typer.Exit(1)

        validate_choice(test, ["t-test", "mann-whitney"], console, value_label="test")
        metric_list = parse_csv_option(metrics)

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        analysis_adapter = StatisticalAnalysisAdapter()
        service = RegressionGateService(storage=storage, analysis_adapter=analysis_adapter)

        try:
            report = service.run_gate(
                run_id,
                baseline,
                metrics=metric_list or None,
                test_type=_coerce_test_type(test),
                fail_on_regression=fail_on_regression,
                parallel=parallel,
                concurrency=concurrency,
            )
        except (KeyError, ValueError) as exc:
            finished_at = datetime.now(UTC)
            duration_ms = int((finished_at - started_at).total_seconds() * 1000)
            payload = _build_envelope(
                report=None,
                status="error",
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                message=str(exc),
                error_type=type(exc).__name__,
            )
            if output:
                write_json(output, payload)
            if output_format == "json":
                console.print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1) from exc
        except Exception as exc:
            finished_at = datetime.now(UTC)
            duration_ms = int((finished_at - started_at).total_seconds() * 1000)
            payload = _build_envelope(
                report=None,
                status="error",
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                message=str(exc),
                error_type=type(exc).__name__,
            )
            if output:
                write_json(output, payload)
            if output_format == "json":
                console.print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(3) from exc

        finished_at = report.finished_at
        duration_ms = report.duration_ms
        payload = _build_envelope(
            report=report,
            status="ok",
            started_at=report.started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
        )
        if output:
            write_json(output, payload)

        if output_format == "json":
            console.print(json.dumps(payload, ensure_ascii=False, indent=2))
        elif output_format == "github-actions":
            _render_github_actions(report, console)
        else:
            _render_table(report, console)

        if report.regression_detected:
            raise typer.Exit(2)

    @app.command(name="ci-gate")
    def ci_gate(
        baseline_run_id: str = typer.Argument(..., help="Baseline run ID."),
        current_run_id: str = typer.Argument(..., help="Current run ID."),
        regression_threshold: float = typer.Option(
            0.05,
            "--regression-threshold",
            help="Fail if regression rate exceeds this threshold (default: 0.05).",
        ),
        output_format: str = typer.Option(
            "github",
            "--format",
            "-f",
            help="Output format: github, gitlab, json, or pr-comment.",
        ),
        fail_on_regression: bool = typer.Option(
            True,
            "--fail-on-regression/--no-fail-on-regression",
            help="Fail the command when regression rate exceeds threshold.",
        ),
        db_path: Path | None = db_option(default=None, help_text="Database path"),
    ) -> None:
        """CI/CD 파이프라인용 회귀 게이트 체크."""
        started_at = datetime.now(UTC)
        if db_path is None:
            console.print("[red]Error:[/red] Database path is not configured.")
            raise typer.Exit(1)

        validate_choice(
            output_format,
            ["github", "gitlab", "json", "pr-comment"],
            console,
            value_label="format",
        )

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        analysis_adapter = StatisticalAnalysisAdapter()
        service = RegressionGateService(storage=storage, analysis_adapter=analysis_adapter)

        try:
            current_run = storage.get_run(current_run_id)
            storage.get_run(baseline_run_id)
            report = service.run_gate(
                current_run_id,
                baseline_run_id,
            )
        except KeyError as exc:
            finished_at = datetime.now(UTC)
            duration_ms = int((finished_at - started_at).total_seconds() * 1000)
            payload = _build_envelope(
                report=None,
                status="error",
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                message=str(exc),
                error_type=type(exc).__name__,
            )
            if output_format == "json":
                console.print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(3) from exc
        except (ValueError, RuntimeError) as exc:
            finished_at = datetime.now(UTC)
            duration_ms = int((finished_at - started_at).total_seconds() * 1000)
            payload = _build_envelope(
                report=None,
                status="error",
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                message=str(exc),
                error_type=type(exc).__name__,
            )
            if output_format == "json":
                console.print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1) from exc

        thresholds = dict.fromkeys(current_run.metrics_evaluated, 0.7)
        thresholds.update(current_run.thresholds or {})

        rows: list[CIGateMetricRow] = []
        threshold_failures = []
        regressed_metrics = []
        for result in report.results:
            avg_score = current_run.get_avg_score(result.metric)
            threshold = thresholds.get(result.metric, 0.7)
            threshold_passed = avg_score is not None and avg_score >= threshold
            if not threshold_passed:
                threshold_failures.append(result.metric)
            if result.regression:
                regressed_metrics.append(result.metric)
            if result.regression:
                status = "⚠️"
            elif threshold_passed:
                status = "✅"
            else:
                status = "❌"
            rows.append(
                CIGateMetricRow(
                    metric=result.metric,
                    baseline_score=result.baseline_score,
                    current_score=result.candidate_score,
                    change_percent=result.diff_percent,
                    status=status,
                )
            )

        regression_rate = len(regressed_metrics) / len(report.results) if report.results else 0.0
        all_thresholds_passed = not threshold_failures
        gate_passed = all_thresholds_passed and regression_rate < regression_threshold

        finished_at = datetime.now(UTC)
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        payload = {
            "baseline_run_id": baseline_run_id,
            "current_run_id": current_run_id,
            "gate_passed": gate_passed,
            "all_thresholds_passed": all_thresholds_passed,
            "regression_rate": regression_rate,
            "regression_threshold": regression_threshold,
            "regressed_metrics": regressed_metrics,
            "threshold_failures": threshold_failures,
            "started_at": _format_timestamp(started_at),
            "finished_at": _format_timestamp(finished_at),
            "duration_ms": duration_ms,
            "report": report.to_dict(),
        }

        if output_format == "json":
            console.print(json.dumps(payload, ensure_ascii=False, indent=2))
        elif output_format == "pr-comment":
            markdown = format_ci_gate_pr_comment(
                rows,
                baseline_run_id=baseline_run_id,
                current_run_id=current_run_id,
                regression_rate=regression_rate,
                regression_threshold=regression_threshold,
                gate_passed=gate_passed,
                threshold_failures=threshold_failures,
                regressed_metrics=regressed_metrics,
            )
            console.print(markdown)
        else:
            markdown = format_ci_regression_report(
                rows,
                regression_rate=regression_rate,
                regression_threshold=regression_threshold,
                gate_passed=gate_passed,
            )
            console.print(markdown)

        if not all_thresholds_passed:
            raise typer.Exit(1)
        if not gate_passed and fail_on_regression:
            raise typer.Exit(2)

    @app.command(name="regress-baseline")
    def regress_baseline(
        action: str = typer.Argument(
            ...,
            help="Action: 'set' to save baseline, 'get' to retrieve baseline run_id.",
        ),
        baseline_key: str = typer.Option(
            "default",
            "--key",
            "-k",
            help="Baseline key identifier (default: 'default').",
        ),
        run_id: str | None = typer.Option(
            None,
            "--run-id",
            "-r",
            help="Run ID to set as baseline (required for 'set').",
        ),
        dataset_name: str | None = typer.Option(
            None,
            "--dataset",
            help="Dataset name for the baseline.",
        ),
        branch: str | None = typer.Option(
            None,
            "--branch",
            help="Git branch name.",
        ),
        commit_sha: str | None = typer.Option(
            None,
            "--commit",
            help="Git commit SHA.",
        ),
        output_format: str = typer.Option(
            "text",
            "--format",
            "-f",
            help="Output format: text, json.",
        ),
        db_path: Path | None = db_option(default=None, help_text="Database path"),
    ) -> None:
        """Manage regression baselines for CI/CD integration."""
        if db_path is None:
            console.print("[red]Error:[/red] Database path is not configured.")
            raise typer.Exit(1)

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)

        if action == "set":
            if not run_id:
                console.print("[red]Error:[/red] --run-id is required for 'set' action.")
                raise typer.Exit(1)
            try:
                storage.get_run(run_id)
            except KeyError:
                console.print(f"[red]Error:[/red] Run not found: {run_id}")
                raise typer.Exit(1)

            storage.set_regression_baseline(
                baseline_key,
                run_id,
                dataset_name=dataset_name,
                branch=branch,
                commit_sha=commit_sha,
            )
            if output_format == "json":
                console.print(
                    json.dumps(
                        {"status": "ok", "baseline_key": baseline_key, "run_id": run_id},
                        ensure_ascii=False,
                    )
                )
            else:
                console.print(f"[green]Baseline '{baseline_key}' set to run_id: {run_id}[/green]")
        elif action == "get":
            baseline = storage.get_regression_baseline(baseline_key)
            if not baseline:
                if output_format == "json":
                    console.print(
                        json.dumps(
                            {"status": "not_found", "baseline_key": baseline_key},
                            ensure_ascii=False,
                        )
                    )
                else:
                    console.print(f"[yellow]Baseline '{baseline_key}' not found.[/yellow]")
                raise typer.Exit(1)

            if output_format == "json":
                console.print(json.dumps(baseline, ensure_ascii=False, indent=2, default=str))
            else:
                console.print(baseline["run_id"])
        else:
            console.print(f"[red]Error:[/red] Unknown action: {action}. Use 'set' or 'get'.")
            raise typer.Exit(1)


def _render_table(report: RegressionGateReport, console: Console) -> None:
    console.print(f"\n[bold]Regression Gate Check: {report.candidate_run_id}[/bold]\n")
    console.print(f"Baseline: {report.baseline_run_id}")
    console.print(f"Test: {report.test_type}\n")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Baseline", justify="right")
    table.add_column("Candidate", justify="right")
    table.add_column("Diff", justify="right")
    table.add_column("p-value", justify="right")
    table.add_column("Regression", justify="center")

    for result in report.results:
        table.add_row(
            result.metric,
            format_score(result.baseline_score),
            format_score(result.candidate_score),
            format_diff(result.diff),
            f"{result.p_value:.4f}",
            format_status(not result.regression, success_text="NO", failure_text="YES"),
        )

    console.print(table)
    if report.regression_detected:
        regressed = [r.metric for r in report.results if r.regression]
        console.print("\n[bold red]Regression detected[/bold red]")
        console.print(f"[red]Regressed metrics: {', '.join(regressed)}[/red]")
    else:
        console.print("\n[bold green]Regression gate PASSED[/bold green]")
    console.print()


def _render_github_actions(report: RegressionGateReport, console: Console) -> None:
    for result in report.results:
        status = "✅" if not result.regression else "❌"
        reg_status = " (REGRESSION)" if result.regression else ""
        console.print(
            f"{status} {result.metric}: {result.candidate_score:.3f} "
            f"(baseline: {result.baseline_score:.3f}, diff: {result.diff:+.3f}){reg_status}"
        )

    console.print(f"::set-output name=passed::{str(not report.regression_detected).lower()}")
    if report.regression_detected:
        regressed = [r.metric for r in report.results if r.regression]
        console.print(f"::error::Regression detected in: {', '.join(regressed)}")


__all__ = ["register_regress_commands"]
