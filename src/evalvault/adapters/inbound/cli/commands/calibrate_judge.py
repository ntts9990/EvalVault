from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.inbound.cli.utils.analysis_io import resolve_artifact_dir, write_json
from evalvault.adapters.inbound.cli.utils.console import print_cli_error, progress_spinner
from evalvault.adapters.inbound.cli.utils.options import db_option
from evalvault.adapters.inbound.cli.utils.validators import parse_csv_option, validate_choice
from evalvault.adapters.outbound.judge_calibration_reporter import JudgeCalibrationReporter
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import Settings
from evalvault.domain.services.judge_calibration_service import JudgeCalibrationService

_console = Console()

_ALLOWED_LABELS = ["feedback", "gold", "hybrid"]
_ALLOWED_METHODS = ["platt", "isotonic", "temperature", "none"]


def register_calibrate_judge_commands(app: typer.Typer, console: Console) -> None:
    global _console
    _console = console

    @app.command(name="calibrate-judge")
    def calibrate_judge(
        run_id: str = typer.Argument(..., help="보정 대상 Run ID"),
        labels_source: str = typer.Option(
            "feedback",
            "--labels-source",
            help="라벨 소스 (feedback|gold|hybrid)",
        ),
        method: str = typer.Option(
            "isotonic",
            "--method",
            help="보정 방법 (platt|isotonic|temperature|none)",
        ),
        metrics: str | None = typer.Option(
            None,
            "--metric",
            "-m",
            help="보정 대상 메트릭 (쉼표로 구분, 미지정 시 run 메트릭 전체)",
        ),
        holdout_ratio: float = typer.Option(
            0.2,
            "--holdout-ratio",
            help="검증용 holdout 비율",
        ),
        seed: int = typer.Option(42, "--seed", help="샘플 분할 랜덤 시드"),
        write_back: bool = typer.Option(
            False,
            "--write-back",
            help="보정 결과를 Run 메타데이터에 저장",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="JSON 결과 파일 경로",
        ),
        artifacts_dir: Path | None = typer.Option(
            None,
            "--artifacts-dir",
            help="아티팩트 저장 디렉터리",
        ),
        parallel: bool = typer.Option(
            False,
            "--parallel/--no-parallel",
            help="병렬 실행 활성화",
        ),
        concurrency: int = typer.Option(8, "--concurrency", help="동시성 수준"),
        db_path: Path | None = db_option(help_text="DB 경로"),
    ) -> None:
        labels_source = labels_source.strip().lower()
        method = method.strip().lower()
        validate_choice(labels_source, _ALLOWED_LABELS, _console, value_label="labels-source")
        validate_choice(method, _ALLOWED_METHODS, _console, value_label="method")

        metric_list = parse_csv_option(metrics)
        if holdout_ratio <= 0 or holdout_ratio >= 1:
            print_cli_error(_console, "--holdout-ratio 값은 0과 1 사이여야 합니다.")
            raise typer.Exit(1)
        if seed < 0:
            print_cli_error(_console, "--seed 값은 0 이상이어야 합니다.")
            raise typer.Exit(1)
        if concurrency <= 0:
            print_cli_error(_console, "--concurrency 값은 1 이상이어야 합니다.")
            raise typer.Exit(1)

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        try:
            run = storage.get_run(run_id)
        except KeyError:
            print_cli_error(_console, f"Run을 찾을 수 없습니다: {run_id}")
            raise typer.Exit(1)

        feedbacks = storage.list_feedback(run_id)
        if labels_source in {"feedback", "hybrid"} and not feedbacks:
            print_cli_error(_console, "피드백 라벨이 없습니다.")
            raise typer.Exit(1)

        resolved_metrics = metric_list or list(run.metrics_evaluated)
        if not resolved_metrics:
            print_cli_error(_console, "보정 대상 메트릭이 없습니다.")
            raise typer.Exit(1)

        prefix = f"judge_calibration_{run_id}"
        output_path = (output or Path("reports/calibration") / f"{prefix}.json").expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_artifacts_dir = resolve_artifact_dir(
            base_dir=artifacts_dir,
            output_path=output_path,
            report_path=output_path,
            prefix=prefix,
        )

        service = JudgeCalibrationService()
        reporter = JudgeCalibrationReporter()
        started_at = datetime.now(UTC)

        with progress_spinner(_console, "Judge 보정 실행 중..."):
            result = service.calibrate(
                run,
                feedbacks,
                labels_source=labels_source,
                method=method,
                metrics=resolved_metrics,
                holdout_ratio=holdout_ratio,
                seed=seed,
                parallel=parallel,
                concurrency=concurrency,
            )

        artifacts_index = reporter.write_artifacts(
            result=result,
            artifacts_dir=resolved_artifacts_dir,
        )
        finished_at = datetime.now(UTC)
        payload = _build_envelope(
            result,
            artifacts_index,
            started_at=started_at,
            finished_at=finished_at,
        )
        write_json(output_path, payload)

        _display_summary(result)
        _console.print(f"[green]JSON 저장:[/green] {output_path}")
        _console.print(
            f"[green]아티팩트 저장:[/green] {artifacts_index['dir']} (index: {artifacts_index['index']})"
        )

        if write_back:
            metadata = run.tracker_metadata or {}
            metadata["judge_calibration"] = reporter.render_json(result)
            metadata["judge_calibration"]["artifacts"] = artifacts_index
            metadata["judge_calibration"]["output"] = str(output_path)
            storage.update_run_metadata(run_id, metadata)
            _console.print("[green]보정 결과를 메타데이터에 저장했습니다.[/green]")

        if result.summary.gate_passed is False:
            raise typer.Exit(2)

    return None


def _build_envelope(
    result,
    artifacts_index: dict[str, str],
    *,
    started_at: datetime,
    finished_at: datetime,
) -> dict[str, object]:
    duration_ms = int((finished_at - started_at).total_seconds() * 1000)
    status = "ok" if result.summary.gate_passed else "degraded"
    return {
        "command": "calibrate-judge",
        "version": 1,
        "status": status,
        "started_at": started_at.astimezone(UTC).isoformat(),
        "finished_at": finished_at.astimezone(UTC).isoformat(),
        "duration_ms": duration_ms,
        "artifacts": artifacts_index,
        "data": {
            "summary": _serialize_summary(result.summary),
            "metrics": [_serialize_metric(metric) for metric in result.metrics],
            "case_results": {
                metric: [_serialize_case(case) for case in cases]
                for metric, cases in result.case_results.items()
            },
            "warnings": list(result.warnings),
        },
    }


def _serialize_summary(summary) -> dict[str, object]:
    return {
        "run_id": summary.run_id,
        "labels_source": summary.labels_source,
        "method": summary.method,
        "metrics": list(summary.metrics),
        "holdout_ratio": summary.holdout_ratio,
        "seed": summary.seed,
        "total_labels": summary.total_labels,
        "total_samples": summary.total_samples,
        "gate_passed": summary.gate_passed,
        "gate_threshold": summary.gate_threshold,
        "notes": list(summary.notes),
    }


def _serialize_metric(metric) -> dict[str, object]:
    return {
        "metric": metric.metric,
        "method": metric.method,
        "sample_count": metric.sample_count,
        "label_count": metric.label_count,
        "mae": metric.mae,
        "pearson": metric.pearson,
        "spearman": metric.spearman,
        "temperature": metric.temperature,
        "parameters": dict(metric.parameters),
        "gate_passed": metric.gate_passed,
        "warning": metric.warning,
    }


def _serialize_case(case) -> dict[str, object]:
    return {
        "test_case_id": case.test_case_id,
        "raw_score": case.raw_score,
        "calibrated_score": case.calibrated_score,
        "label": case.label,
        "label_source": case.label_source,
    }


def _display_summary(result) -> None:
    summary_table = Table(title="Judge 보정 요약", show_header=True, header_style="bold cyan")
    summary_table.add_column("메트릭")
    summary_table.add_column("표본", justify="right")
    summary_table.add_column("라벨", justify="right")
    summary_table.add_column("MAE", justify="right")
    summary_table.add_column("Pearson", justify="right")
    summary_table.add_column("Spearman", justify="right")
    summary_table.add_column("Gate", justify="right")

    for metric in result.metrics:
        summary_table.add_row(
            metric.metric,
            str(metric.sample_count),
            str(metric.label_count),
            _format_metric(metric.mae),
            _format_metric(metric.pearson),
            _format_metric(metric.spearman),
            "PASS" if metric.gate_passed else "FAIL",
        )

    _console.print(summary_table)
    _console.print(
        f"라벨 소스: {result.summary.labels_source} | "
        f"방법: {result.summary.method} | "
        f"Gate: {'PASS' if result.summary.gate_passed else 'FAIL'}"
    )

    if result.warnings:
        for warning in result.warnings:
            _console.print(f"[yellow]경고:[/yellow] {warning}")


def _format_metric(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.3f}"
