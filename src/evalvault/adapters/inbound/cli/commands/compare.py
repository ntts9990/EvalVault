from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.analysis.comparison_pipeline_adapter import (
    ComparisonPipelineAdapter,
)
from evalvault.adapters.outbound.analysis.pipeline_factory import build_analysis_pipeline_service
from evalvault.adapters.outbound.analysis.statistical_adapter import StatisticalAnalysisAdapter
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.services.run_comparison_service import (
    RunComparisonError,
    RunComparisonRequest,
    RunComparisonService,
)

from ..utils.analysis_io import (
    build_comparison_scorecard,
    resolve_artifact_dir,
    resolve_output_paths,
    serialize_pipeline_result,
    write_json,
    write_pipeline_artifacts,
)
from ..utils.console import print_cli_error
from ..utils.options import db_option, profile_option
from ..utils.validators import parse_csv_option, validate_choice


def _coerce_test_type(value: str) -> str:
    if value == "t-test":
        return "t-test"
    return "mann-whitney"


def register_compare_commands(app: typer.Typer, console: Console) -> None:
    @app.command(name="compare")
    def compare(
        run_id_a: str = typer.Argument(..., help="기준 Run ID"),
        run_id_b: str = typer.Argument(..., help="비교 Run ID"),
        metrics: str | None = typer.Option(
            None,
            "--metrics",
            "-m",
            help="비교할 메트릭 목록 (쉼표 구분)",
        ),
        test: str = typer.Option(
            "t-test",
            "--test",
            "-t",
            help="통계 검정 (t-test | mann-whitney)",
        ),
        output_format: str = typer.Option(
            "table",
            "--format",
            "-f",
            help="출력 형식 (table, json)",
        ),
        output: Path | None = typer.Option(None, "--output", "-o", help="JSON 출력 파일"),
        report: Path | None = typer.Option(None, "--report", help="리포트 출력 파일"),
        output_dir: Path | None = typer.Option(
            None,
            "--output-dir",
            help="출력 기본 디렉터리",
        ),
        artifacts_dir: Path | None = typer.Option(
            None,
            "--artifacts-dir",
            help="아티팩트 저장 디렉터리",
        ),
        parallel: bool = typer.Option(
            False,
            "--parallel/--no-parallel",
            help="병렬 파이프라인 실행",
        ),
        concurrency: int | None = typer.Option(
            None,
            "--concurrency",
            min=1,
            help="병렬 실행 동시성 제한",
        ),
        db_path: Path | None = db_option(help_text="DB 경로"),
        profile: str | None = profile_option(help_text="LLM 프로필"),
    ) -> None:
        validate_choice(test, ["t-test", "mann-whitney"], console, value_label="test")
        validate_choice(output_format, ["table", "json"], console, value_label="format")

        metric_list = parse_csv_option(metrics)
        metric_list = metric_list or None

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        analysis_adapter = StatisticalAnalysisAdapter()

        settings = Settings()
        profile_name = profile or settings.evalvault_profile
        if profile_name:
            settings = apply_profile(settings, profile_name)

        llm_adapter = None
        try:
            from evalvault.adapters.outbound.llm import get_llm_adapter

            llm_adapter = get_llm_adapter(settings)
        except Exception as exc:
            console.print(f"[yellow]경고: LLM 어댑터 초기화 실패 ({exc})[/yellow]")

        pipeline_service = build_analysis_pipeline_service(
            storage=storage,
            llm_adapter=llm_adapter,
        )
        pipeline_adapter = ComparisonPipelineAdapter(pipeline_service)

        service = RunComparisonService(
            storage=storage,
            analysis_port=analysis_adapter,
            pipeline_port=pipeline_adapter,
        )

        request = RunComparisonRequest(
            run_id_a=run_id_a,
            run_id_b=run_id_b,
            metrics=metric_list,
            test_type=_coerce_test_type(test),
            parallel=parallel,
            concurrency=concurrency,
        )

        try:
            outcome = service.compare_runs(request)
        except RunComparisonError as exc:
            print_cli_error(console, str(exc))
            raise typer.Exit(exc.exit_code) from exc

        comparison_prefix = f"comparison_{run_id_a[:8]}_{run_id_b[:8]}"
        resolved_base_dir = output_dir or Path("reports/comparison")
        output_path, report_path = resolve_output_paths(
            base_dir=resolved_base_dir,
            output_path=output,
            report_path=report,
            prefix=comparison_prefix,
        )
        if artifacts_dir is not None:
            resolved_artifacts_dir = artifacts_dir
            resolved_artifacts_dir.mkdir(parents=True, exist_ok=True)
        else:
            resolved_artifacts_dir = resolve_artifact_dir(
                base_dir=output_dir,
                output_path=output_path,
                report_path=report_path,
                prefix=comparison_prefix,
            )

        artifact_index = write_pipeline_artifacts(
            outcome.pipeline_result,
            artifacts_dir=resolved_artifacts_dir,
        )

        payload = _build_envelope(outcome, artifact_index)
        payload["run_ids"] = list(outcome.run_ids)
        payload["data"] = serialize_pipeline_result(outcome.pipeline_result)
        payload["data"]["run_ids"] = list(outcome.run_ids)
        payload["data"]["artifacts"] = artifact_index
        write_json(output_path, payload)
        report_path.write_text(outcome.report_text, encoding="utf-8")

        if output_format == "table":
            _render_table(console, outcome)
        else:
            console.print(json.dumps(payload, ensure_ascii=False, indent=2))

        if outcome.is_degraded:
            console.print("[yellow]리포트가 일부 누락되었을 수 있습니다.[/yellow]")

        console.print(f"[green]비교 결과 저장:[/green] {output_path}")
        console.print(f"[green]비교 리포트 저장:[/green] {report_path}")
        console.print(
            "[green]비교 아티팩트 저장:[/green] "
            f"{artifact_index['dir']} (index: {artifact_index['index']})"
        )

        if outcome.is_degraded:
            raise typer.Exit(2)


def _build_envelope(outcome, artifact_index: dict[str, str]) -> dict[str, object]:
    return {
        "command": "compare",
        "version": 1,
        "status": outcome.status,
        "started_at": outcome.started_at.isoformat(),
        "finished_at": outcome.finished_at.isoformat(),
        "duration_ms": outcome.duration_ms,
        "artifacts": {
            "dir": artifact_index.get("dir"),
            "index": artifact_index.get("index"),
        },
    }


def _render_table(console: Console, outcome) -> None:
    table = Table(title="통계 비교", show_header=True, header_style="bold cyan")
    table.add_column("메트릭")
    table.add_column("실행 A (평균)", justify="right")
    table.add_column("실행 B (평균)", justify="right")
    table.add_column("변화 (%)", justify="right")
    table.add_column("p-값", justify="right")
    table.add_column("효과 크기", justify="right")
    table.add_column("유의")
    table.add_column("승자")

    for comparison in outcome.comparisons:
        sig_style = "green" if comparison.is_significant else "dim"
        winner = comparison.winner[:8] if comparison.winner else "-"
        table.add_row(
            comparison.metric,
            f"{comparison.mean_a:.3f}",
            f"{comparison.mean_b:.3f}",
            f"{comparison.diff_percent:+.1f}%",
            f"{comparison.p_value:.4f}",
            f"{comparison.effect_size:.2f} ({comparison.effect_level.value})",
            f"[{sig_style}]{'예' if comparison.is_significant else '아니오'}[/{sig_style}]",
            winner,
        )

    console.print("\n[bold]실행 비교 결과[/bold]")
    console.print(table)
    console.print()

    scorecard = build_comparison_scorecard(
        outcome.pipeline_result.get_node_result("run_metric_comparison").output
        if outcome.pipeline_result.get_node_result("run_metric_comparison")
        else {}
    )
    if not scorecard:
        return

    summary_table = Table(title="비교 스코어카드", show_header=True, header_style="bold cyan")
    summary_table.add_column("메트릭")
    summary_table.add_column("A", justify="right")
    summary_table.add_column("B", justify="right")
    summary_table.add_column("차이", justify="right")
    summary_table.add_column("p-값", justify="right")
    summary_table.add_column("효과 크기", justify="right")
    summary_table.add_column("유의 여부")

    for row in scorecard:
        effect_size = row.get("effect_size")
        effect_level = row.get("effect_level")
        effect_text = (
            f"{effect_size:.2f} ({effect_level})"
            if isinstance(effect_size, (float, int)) and effect_level
            else "-"
        )
        summary_table.add_row(
            str(row.get("metric") or "-"),
            _format_float(row.get("mean_a")),
            _format_float(row.get("mean_b")),
            _format_float(row.get("diff"), signed=True),
            _format_float(row.get("p_value")),
            effect_text,
            "예" if row.get("is_significant") else "아니오",
        )

    console.print(summary_table)
    console.print()


def _format_float(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "-"
    try:
        if signed:
            return f"{float(value):+.3f}"
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "-"


__all__ = ["register_compare_commands"]
