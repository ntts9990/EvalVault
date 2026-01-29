"""EvalVault CLI의 분석 관련 명령."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from evalvault.adapters.outbound.analysis import (
    CausalAnalysisAdapter,
    HypothesisGeneratorModule,
    NetworkAnalyzerModule,
    NLPAnalysisAdapter,
    StatisticalAnalysisAdapter,
    TimeSeriesAdvancedModule,
)
from evalvault.adapters.outbound.analysis.pipeline_factory import (
    build_analysis_pipeline_service,
)
from evalvault.adapters.outbound.analysis.pipeline_helpers import to_serializable
from evalvault.adapters.outbound.cache import MemoryCacheAdapter
from evalvault.adapters.outbound.llm import get_llm_adapter
from evalvault.adapters.outbound.report import DashboardGenerator, MarkdownReportAdapter
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.adapters.outbound.storage.postgres_adapter import PostgreSQLStorageAdapter
from evalvault.config.phoenix_support import get_phoenix_trace_url
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
from evalvault.domain.services.analysis_service import AnalysisService

from ..utils.analysis_io import (
    build_comparison_scorecard,
    extract_markdown_report,
    get_node_output,
    resolve_artifact_dir,
    resolve_output_paths,
    serialize_pipeline_result,
    write_json,
    write_pipeline_artifacts,
)
from ..utils.options import db_option, profile_option
from ..utils.validators import parse_csv_option

_console = Console()


def register_analyze_commands(app: typer.Typer, console: Console) -> None:
    """Attach analyze/analyze-compare commands to the root Typer app."""

    global _console
    _console = console

    @app.command()
    def analyze(  # noqa: PLR0913 - CLI 옵션 다양성을 위한 길이 허용
        run_id: str = typer.Argument(..., help="분석할 Run ID"),
        nlp: bool = typer.Option(False, "--nlp", "-N", help="NLP 분석 포함"),
        causal: bool = typer.Option(False, "--causal", "-c", help="인과 분석 포함"),
        playbook: bool = typer.Option(
            False, "--playbook", "-B", help="플레이북 기반 개선 분석 포함"
        ),
        enable_llm: bool = typer.Option(
            False,
            "--enable-llm",
            "-L",
            help="플레이북 분석에서 LLM 인사이트 생성",
        ),
        dashboard: bool = typer.Option(False, "--dashboard", help="시각화 대시보드 생성"),
        dashboard_format: str = typer.Option(
            "png", "--dashboard-format", help="대시보드 출력 형식 (png, svg, pdf)"
        ),
        anomaly_detect: bool = typer.Option(
            False, "--anomaly-detect", "-A", help="이상치 탐지 실행 (Phase 2)"
        ),
        window_size: int = typer.Option(
            200, "--window-size", "-w", help="이상치 탐지 윈도 크기", min=50, max=500
        ),
        forecast: bool = typer.Option(False, "--forecast", "-F", help="성능 예측 실행 (Phase 2)"),
        forecast_horizon: int = typer.Option(
            3, "--forecast-horizon", help="예측 범위(런 개수)", min=1, max=10
        ),
        network: bool = typer.Option(
            False, "--network", help="메트릭 상관관계 네트워크 생성 (Phase 3)"
        ),
        min_correlation: float = typer.Option(
            0.5, "--min-correlation", help="네트워크 최소 상관계수", min=0, max=1
        ),
        generate_hypothesis: bool = typer.Option(
            False, "--generate-hypothesis", "-H", help="가설 자동 생성 (Phase 4)"
        ),
        hypothesis_method: str = typer.Option(
            "heuristic",
            "--hypothesis-method",
            help="가설 생성 방식 (heuristic, hyporefine, union)",
        ),
        num_hypotheses: int = typer.Option(
            5, "--num-hypotheses", help="생성할 가설 수", min=1, max=20
        ),
        output: Path | None = typer.Option(None, "--output", "-o", help="JSON 출력 파일"),
        report: Path | None = typer.Option(
            None, "--report", "-r", help="리포트 출력 파일 (*.md 또는 *.html)"
        ),
        excel_output: Path | None = typer.Option(
            None, "--excel-output", help="분석 결과 Excel 출력 경로"
        ),
        save: bool = typer.Option(False, "--save", "-S", help="분석 결과 DB 저장"),
        db_path: Path | None = db_option(help_text="DB 경로"),
        profile: str | None = profile_option(
            help_text="NLP 임베딩용 모델 프로필 (dev, prod, openai)",
        ),
    ) -> None:
        """평가 실행 결과를 분석하고 통계 인사이트를 표시합니다."""

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)

        try:
            run = storage.get_run(run_id)
        except KeyError:
            _console.print(f"[red]오류: Run을 찾을 수 없습니다: {run_id}[/red]")
            raise typer.Exit(1)

        if not run.results:
            _console.print("[yellow]경고: 분석할 테스트 케이스 결과가 없습니다.[/yellow]")
            raise typer.Exit(0)
        trace_url = get_phoenix_trace_url(getattr(run, "tracker_metadata", None))

        analysis_adapter = StatisticalAnalysisAdapter()
        cache_adapter = MemoryCacheAdapter()

        # Create NLP adapter if requested
        nlp_adapter = None
        if nlp:
            settings = Settings()
            profile_name = profile or settings.evalvault_profile
            if profile_name:
                settings = apply_profile(settings, profile_name)

            llm_adapter = get_llm_adapter(settings)
            nlp_adapter = NLPAnalysisAdapter(
                llm_adapter=llm_adapter,
                use_embeddings=True,
            )

        causal_adapter = None
        if causal:
            causal_adapter = CausalAnalysisAdapter()

        service = AnalysisService(
            analysis_adapter=analysis_adapter,
            nlp_adapter=nlp_adapter,
            causal_adapter=causal_adapter,
            cache_adapter=cache_adapter,
        )

        _console.print(f"\n[bold]분석 시작: {run_id}[/bold]")
        if trace_url:
            _console.print(f"[dim]Phoenix 트레이스: {trace_url}[/dim]")
        _console.print()
        bundle = service.analyze_run(run, include_nlp=nlp, include_causal=causal)

        if not bundle.statistical:
            _console.print("[yellow]통계 분석 결과가 없습니다.[/yellow]")
            raise typer.Exit(0)

        analysis = bundle.statistical
        _display_analysis_summary(analysis)
        _display_metric_stats(analysis)
        _display_correlations(analysis)
        _display_low_performers(analysis)
        _display_insights(analysis)

        if bundle.has_nlp and bundle.nlp:
            _display_nlp_analysis(bundle.nlp)

        if bundle.has_causal and bundle.causal:
            _display_causal_analysis(bundle.causal)

        improvement_report = None
        if playbook:
            stage_metrics = storage.list_stage_metrics(run_id)
            if not stage_metrics:
                _console.print(
                    "[yellow]스테이지 메트릭이 없습니다. "
                    "`evalvault stage compute-metrics <run_id>` 실행 후 가이드를 포함하세요."
                    "[/yellow]"
                )
            improvement_report = _perform_playbook_analysis(
                run,
                enable_llm,
                profile,
                stage_metrics=stage_metrics,
            )

        def _save_analysis_payload(payload: Any, analysis_type: str) -> None:
            serialized = to_serializable(payload)
            if not isinstance(serialized, dict):
                serialized = {"value": serialized}
            storage.save_analysis_result(
                run_id=run_id,
                analysis_type=analysis_type,
                result_data=serialized,
            )

        if save or excel_output:
            storage.save_analysis(analysis)
            if bundle.nlp is not None:
                storage.save_nlp_analysis(bundle.nlp)
            if bundle.causal is not None:
                _save_analysis_payload(bundle.causal, "causal")
            if improvement_report is not None:
                _save_analysis_payload(improvement_report, "playbook")
            storage_label = (
                "PostgreSQL"
                if isinstance(storage, PostgreSQLStorageAdapter)
                else f"SQLite ({db_path})"
            )
            _console.print(f"\n[green]분석 결과 DB 저장: {storage_label}[/green]")

        if dashboard:
            dashboard_gen = DashboardGenerator()
            _console.print("\n[bold cyan]Generating visualization dashboard...[/bold cyan]")

            fig = dashboard_gen.generate_evaluation_dashboard(run_id)

            output_dir = Path("reports/dashboard")
            output_dir.mkdir(parents=True, exist_ok=True)

            output_path = output_dir / f"dashboard_{run_id[:8]}.{dashboard_format}"
            fig.savefig(output_path, dpi=300, bbox_inches="tight")
            _console.print(f"\n[green]Dashboard saved to: {output_path}[/green]")

        anomaly_result = None
        forecast_result = None
        if anomaly_detect or forecast:
            ts_analyzer = TimeSeriesAdvancedModule(window_size=window_size)
            run_history = storage.list_runs(limit=50)

            if not run_history or len(run_history) < 5:
                _console.print("[yellow]Need at least 5 runs for time series analysis.[/yellow]")
            else:
                if anomaly_detect:
                    _console.print("\n[bold cyan]Running anomaly detection...[/bold cyan]")
                    history_data = [
                        {
                            "run_id": r.run_id,
                            "pass_rate": r.pass_rate,
                            "timestamp": r.started_at,
                        }
                        for r in run_history
                    ]
                    anomaly_result = ts_analyzer.detect_anomalies(history_data)
                    _display_anomaly_detection(anomaly_result)

                if forecast:
                    _console.print("\n[bold cyan]Running performance forecasting...[/bold cyan]")
                    history_data = [
                        {"run_id": r.run_id, "pass_rate": r.pass_rate} for r in run_history
                    ]
                    forecast_result = ts_analyzer.forecast_performance(
                        history_data, horizon=forecast_horizon
                    )
                    _display_forecast_result(forecast_result)

        net_result = None
        if network:
            _console.print("\n[bold cyan]Building metric correlation network...[/bold cyan]")
            net_analyzer = NetworkAnalyzerModule()

            if not bundle.statistical or not bundle.statistical.significant_correlations:
                _console.print("[yellow]No significant correlations for network analysis.[/yellow]")
            else:
                correlations_data = [
                    {
                        "variable1": corr.variable1,
                        "variable2": corr.variable2,
                        "correlation": corr.correlation,
                        "p_value": corr.p_value,
                        "is_significant": corr.is_significant,
                    }
                    for corr in bundle.statistical.significant_correlations
                ]
                graph = net_analyzer.build_correlation_network(
                    correlations_data, min_correlation=min_correlation
                )
                net_result = net_analyzer.analyze_metric_network(graph)
                _display_network_analysis(net_result)

        hypotheses = None
        if generate_hypothesis:
            _console.print(
                f"\n[bold cyan]Generating hypotheses ({hypothesis_method})...[/bold cyan]"
            )
            hyp_gen = HypothesisGeneratorModule(
                method=hypothesis_method, num_hypotheses=num_hypotheses
            )

            metric_scores = {}
            for metric_name, stats in analysis.metrics_summary.items():
                metric_scores[metric_name] = stats.mean

            low_performers_data = [
                {
                    "question": lp.test_case_id,
                    "metric_name": lp.metric_name,
                }
                for lp in (analysis.low_performers or [])
            ]

            hypotheses = hyp_gen.generate_simple_hypotheses(
                run_id, metric_scores, low_performers_data
            )
            _display_hypothesis_generation(hypotheses, hypothesis_method)

        if save or excel_output:
            if anomaly_result is not None:
                _save_analysis_payload(anomaly_result, "time_series_anomaly")
            if forecast_result is not None:
                _save_analysis_payload(forecast_result, "time_series_forecast")
            if net_result is not None:
                _save_analysis_payload(net_result, "network")
            if hypotheses is not None:
                _save_analysis_payload(hypotheses, "hypotheses")

        if output:
            _export_analysis_json(analysis, output, bundle.nlp if nlp else None, improvement_report)
            _console.print(f"\n[green]분석 결과 내보냄: {output}[/green]")

        if report:
            _generate_report(bundle, report, include_nlp=nlp, improvement_report=improvement_report)
            _console.print(f"\n[green]리포트 생성: {report}[/green]")

        if excel_output:
            exported = storage.export_analysis_results_to_excel(run_id, excel_output)
            _console.print(f"\n[green]Excel 생성: {exported}[/green]")

    @app.command(name="analyze-compare")
    @app.command(name="compare-analysis")
    def analyze_compare(
        run_id1: str = typer.Argument(..., help="첫 번째 Run ID"),
        run_id2: str = typer.Argument(..., help="두 번째 Run ID"),
        metrics: str | None = typer.Option(
            None, "--metrics", "-m", help="비교할 메트릭(쉼표 구분)"
        ),
        test: str = typer.Option("t-test", "--test", "-t", help="통계 검정 (t-test, mann-whitney)"),
        output: Path | None = typer.Option(None, "--output", "-o", help="JSON 출력 파일"),
        report: Path | None = typer.Option(None, "--report", "-r", help="리포트 출력 파일 (*.md)"),
        output_dir: Path | None = typer.Option(
            None,
            "--output-dir",
            help="비교 산출물 저장 디렉터리 (기본: reports/comparison)",
        ),
        db_path: Path | None = db_option(help_text="DB 경로"),
        profile: str | None = profile_option(
            help_text="비교 리포트용 LLM 프로필 (dev, prod, openai)",
        ),
    ) -> None:
        """두 실행을 통계적으로 비교합니다."""

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)

        try:
            run_a = storage.get_run(run_id1)
            run_b = storage.get_run(run_id2)
        except KeyError as exc:
            _console.print(f"[red]오류: {exc}[/red]")
            raise typer.Exit(1) from exc

        metric_list = parse_csv_option(metrics)
        if not metric_list:
            metric_list = None

        analysis_adapter = StatisticalAnalysisAdapter()
        service = AnalysisService(analysis_adapter)

        trace_a = get_phoenix_trace_url(getattr(run_a, "tracker_metadata", None))
        trace_b = get_phoenix_trace_url(getattr(run_b, "tracker_metadata", None))

        _console.print("\n[bold]실행 비교:[/bold]")
        _console.print(f"  실행 A: {run_id1}")
        if trace_a:
            _console.print(f"    Phoenix 트레이스: {trace_a}")
        _console.print(f"  실행 B: {run_id2}")
        if trace_b:
            _console.print(f"    Phoenix 트레이스: {trace_b}")
        _console.print(f"  검정: {test}\n")

        if test == "t-test":
            test_type = "t-test"
        elif test == "mann-whitney":
            test_type = "mann-whitney"
        else:
            _console.print(f"[red]Error: Unsupported test type: {test}[/red]")
            raise typer.Exit(1)

        comparisons = service.compare_runs(run_a, run_b, metrics=metric_list, test_type=test_type)

        if not comparisons:
            _console.print("[yellow]비교할 공통 메트릭이 없습니다.[/yellow]")
            raise typer.Exit(0)

        table = Table(title="통계 비교", show_header=True, header_style="bold cyan")
        table.add_column("메트릭")
        table.add_column("실행 A (평균)", justify="right")
        table.add_column("실행 B (평균)", justify="right")
        table.add_column("변화 (%)", justify="right")
        table.add_column("p-값", justify="right")
        table.add_column("효과 크기", justify="right")
        table.add_column("유의")
        table.add_column("승자")

        for comparison in comparisons:
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

        _console.print(table)
        _console.print()

        comparison_prefix = f"comparison_{run_id1[:8]}_{run_id2[:8]}"
        base_dir = output_dir or Path("reports/comparison")
        output_path, report_path = resolve_output_paths(
            base_dir=base_dir,
            output_path=output,
            report_path=report,
            prefix=comparison_prefix,
        )

        settings = Settings()
        profile_name = profile or settings.evalvault_profile
        if profile_name:
            settings = apply_profile(settings, profile_name)
        llm_adapter = None
        try:
            llm_adapter = get_llm_adapter(settings)
        except Exception as exc:
            _console.print(f"[yellow]경고: LLM 어댑터 초기화 실패 ({exc})[/yellow]")

        pipeline_service = build_analysis_pipeline_service(
            storage=storage,
            llm_adapter=llm_adapter,
        )
        with _console.status("[bold green]비교 분석 파이프라인 실행 중..."):
            pipeline_result = pipeline_service.analyze_intent(
                AnalysisIntent.GENERATE_COMPARISON,
                run_id=run_id1,
                run_ids=[run_id1, run_id2],
                compare_metrics=metric_list,
                test_type=test,
                report_type="comparison",
                use_llm_report=True,
            )

        artifacts_dir = resolve_artifact_dir(
            base_dir=output_dir,
            output_path=output_path,
            report_path=report_path,
            prefix=comparison_prefix,
        )
        artifact_index = write_pipeline_artifacts(
            pipeline_result,
            artifacts_dir=artifacts_dir,
        )
        payload = serialize_pipeline_result(pipeline_result)
        payload["run_ids"] = [run_id1, run_id2]
        payload["artifacts"] = artifact_index
        write_json(output_path, payload)

        report_text = extract_markdown_report(pipeline_result.final_output)
        if not report_text:
            report_text = "# 비교 분석 보고서\n\n보고서 본문을 찾지 못했습니다.\n"
        report_path.write_text(report_text, encoding="utf-8")

        _display_pipeline_comparison_summary(pipeline_result, run_id1, run_id2)

        _console.print(f"[green]비교 분석 결과 저장:[/green] {output_path}")
        _console.print(f"[green]비교 분석 보고서 저장:[/green] {report_path}\n")
        _console.print(
            "[green]비교 분석 상세 결과 저장:[/green] "
            f"{artifact_index['dir']} (index: {artifact_index['index']})\n"
        )


def _display_analysis_summary(analysis) -> None:
    """Display analysis summary panel."""

    panel = Panel(
        f"""[bold]분석 요약[/bold]
실행 ID: {analysis.run_id}
분석 유형: {analysis.analysis_type.value}
생성 시각: {analysis.created_at.strftime("%Y-%m-%d %H:%M:%S")}

전체 통과율: [{"green" if analysis.overall_pass_rate >= 0.7 else "yellow" if analysis.overall_pass_rate >= 0.5 else "red"}]{analysis.overall_pass_rate:.1%}[/]
분석 메트릭 수: {len(analysis.metrics_summary)}
유의미한 상관관계: {len(analysis.significant_correlations)}
저성능 케이스: {len(analysis.low_performers)}""",
        title="[bold cyan]통계 분석[/bold cyan]",
        border_style="cyan",
    )
    _console.print(panel)


def _display_metric_stats(analysis) -> None:
    """Display metric statistics table."""

    if not analysis.metrics_summary:
        return

    table = Table(title="메트릭 통계", show_header=True, header_style="bold cyan")
    table.add_column("메트릭")
    table.add_column("평균", justify="right")
    table.add_column("표준편차", justify="right")
    table.add_column("최소", justify="right")
    table.add_column("최대", justify="right")
    table.add_column("중앙값", justify="right")
    table.add_column("통과율", justify="right")

    for metric_name, stats in analysis.metrics_summary.items():
        pass_rate = analysis.metric_pass_rates.get(metric_name, 0)
        pass_style = "green" if pass_rate >= 0.7 else "yellow" if pass_rate >= 0.5 else "red"

        table.add_row(
            metric_name,
            f"{stats.mean:.3f}",
            f"{stats.std:.3f}",
            f"{stats.min:.3f}",
            f"{stats.max:.3f}",
            f"{stats.median:.3f}",
            f"[{pass_style}]{pass_rate:.1%}[/{pass_style}]",
        )

    _console.print(table)


def _display_pipeline_comparison_summary(pipeline_result, run_id1: str, run_id2: str) -> None:
    """Display a concise comparison summary for pipeline reports."""

    comparison_output = get_node_output(pipeline_result, "run_metric_comparison")
    change_output = get_node_output(pipeline_result, "run_change_detection")
    run_output = get_node_output(pipeline_result, "load_runs")

    runs = run_output.get("runs", []) if isinstance(run_output, dict) else []
    run_a = runs[0] if len(runs) > 0 else None
    run_b = runs[1] if len(runs) > 1 else None

    model_a = run_a.model_name if isinstance(run_a, EvaluationRun) else "-"
    model_b = run_b.model_name if isinstance(run_b, EvaluationRun) else "-"
    dataset_a = run_a.dataset_name if isinstance(run_a, EvaluationRun) else "-"
    dataset_b = run_b.dataset_name if isinstance(run_b, EvaluationRun) else "-"

    summary = comparison_output.get("summary", {}) if isinstance(comparison_output, dict) else {}
    pass_rate_diff = summary.get("pass_rate_diff")
    avg_score_diff = summary.get("avg_score_diff")

    dataset_changes = change_output.get("dataset_changes", [])
    config_changes = change_output.get("config_changes", [])
    prompt_changes = change_output.get("prompt_changes", {})
    prompt_summary = prompt_changes.get("summary", {}) if isinstance(prompt_changes, dict) else {}

    _console.print("\n[bold]비교 분석 요약[/bold]")
    _console.print(f"- 실행 A: {run_id1} ({model_a}, {dataset_a})")
    _console.print(f"- 실행 B: {run_id2} ({model_b}, {dataset_b})")
    _console.print(f"- 통과율 변화: {_format_percent(pass_rate_diff, signed=True)}")
    _console.print(f"- 평균 점수 변화: {_format_float(avg_score_diff, signed=True)}")
    _console.print(
        f"- 데이터셋 변경: {len(dataset_changes) if isinstance(dataset_changes, list) else 0}건"
    )
    _console.print(
        f"- 설정 변경: {len(config_changes) if isinstance(config_changes, list) else 0}건"
    )
    _console.print(
        "- 프롬프트 변경: "
        f"{prompt_summary.get('changed', 0)}건 (상태: {prompt_changes.get('status', '알 수 없음')})"
    )

    scorecard = build_comparison_scorecard(comparison_output)
    if not scorecard:
        _console.print("[yellow]비교 스코어카드 데이터가 없습니다.[/yellow]\n")
        return

    table = Table(title="비교 스코어카드", show_header=True, header_style="bold cyan")
    table.add_column("메트릭")
    table.add_column("A", justify="right")
    table.add_column("B", justify="right")
    table.add_column("차이", justify="right")
    table.add_column("p-값", justify="right")
    table.add_column("효과 크기", justify="right")
    table.add_column("유의 여부")

    for row in scorecard:
        effect_size = _format_float(row.get("effect_size"), precision=2)
        effect_level = row.get("effect_level")
        effect_text = f"{effect_size} ({effect_level})" if effect_level else f"{effect_size}"
        significant = "예" if row.get("is_significant") else "아니오"
        table.add_row(
            str(row.get("metric") or "-"),
            _format_float(row.get("mean_a")),
            _format_float(row.get("mean_b")),
            _format_float(row.get("diff"), signed=True),
            _format_float(row.get("p_value")),
            effect_text,
            significant,
        )

    _console.print(table)


def _format_float(value: float | None, precision: int = 3, *, signed: bool = False) -> str:
    if value is None:
        return "-"
    try:
        if signed:
            return f"{float(value):+.{precision}f}"
        return f"{float(value):.{precision}f}"
    except (TypeError, ValueError):
        return "-"


def _format_percent(value: float | None, precision: int = 1, *, signed: bool = False) -> str:
    if value is None:
        return "-"
    try:
        if signed:
            return f"{float(value):+.{precision}%}"
        return f"{float(value):.{precision}%}"
    except (TypeError, ValueError):
        return "-"
    _console.print()


def _display_correlations(analysis) -> None:
    """Display significant correlations."""

    if not analysis.significant_correlations:
        return

    _console.print("[bold]유의미한 상관관계:[/bold]")
    for corr in analysis.significant_correlations[:5]:
        direction = "[green]+" if corr.correlation > 0 else "[red]-"
        _console.print(
            f"  {direction}{abs(corr.correlation):.2f}[/] "
            f"{corr.variable1} ↔ {corr.variable2} "
            f"(p={corr.p_value:.4f}, {corr.interpretation})"
        )
    _console.print()


def _display_low_performers(analysis) -> None:
    """Display low performing test cases."""

    if not analysis.low_performers:
        return

    _console.print(f"[bold]저성능 테스트 케이스 ({len(analysis.low_performers)}):[/bold]")

    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("테스트 케이스")
    table.add_column("메트릭")
    table.add_column("점수", justify="right")
    table.add_column("임계값", justify="right")
    table.add_column("가능한 원인")

    for low_perf in analysis.low_performers[:10]:
        causes = ", ".join(low_perf.potential_causes[:2]) if low_perf.potential_causes else "-"
        table.add_row(
            low_perf.test_case_id[:12] + "..."
            if len(low_perf.test_case_id) > 15
            else low_perf.test_case_id,
            low_perf.metric_name,
            f"[red]{low_perf.score:.3f}[/red]",
            f"{low_perf.threshold:.2f}",
            causes[:40] + "..." if len(causes) > 40 else causes,
        )

    _console.print(table)
    _console.print()


def _display_insights(analysis) -> None:
    """Display analysis insights."""

    if not analysis.insights:
        return

    _console.print("[bold]인사이트:[/bold]")
    for insight in analysis.insights:
        _console.print(f"  • {insight}")
    _console.print()


def _display_nlp_analysis(nlp_analysis) -> None:
    """Display NLP analysis results."""

    _console.print("\n[bold cyan]NLP 분석[/bold cyan]\n")

    if nlp_analysis.question_stats:
        _console.print("[bold]텍스트 통계(질문):[/bold]")
        stats = nlp_analysis.question_stats
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("지표", style="bold")
        table.add_column("값", justify="right")

        table.add_row("전체 문자 수", str(stats.char_count))
        table.add_row("전체 단어 수", str(stats.word_count))
        table.add_row("전체 문장 수", str(stats.sentence_count))
        table.add_row("평균 단어 길이", f"{stats.avg_word_length:.2f}")
        table.add_row("어휘 다양성", f"{stats.unique_word_ratio:.1%}")
        table.add_row("평균 문장 길이", f"{stats.avg_sentence_length:.1f} 단어")

        _console.print(table)
        _console.print()

    if nlp_analysis.question_types:
        _console.print("[bold]질문 유형 분포:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("유형")
        table.add_column("개수", justify="right")
        table.add_column("비율", justify="right")
        table.add_column("평균 점수")

        for question_type in nlp_analysis.question_types:
            avg_scores_str = ", ".join(
                f"{name}: {score:.2f}" for name, score in (question_type.avg_scores or {}).items()
            )
            table.add_row(
                question_type.question_type.value.capitalize(),
                str(question_type.count),
                f"{question_type.percentage:.1%}",
                avg_scores_str or "-",
            )

        _console.print(table)
        _console.print()

    if nlp_analysis.top_keywords:
        _console.print("[bold]상위 키워드:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("키워드")
        table.add_column("빈도", justify="right")
        table.add_column("TF-IDF 점수", justify="right")

        for keyword in nlp_analysis.top_keywords[:10]:
            table.add_row(keyword.keyword, str(keyword.frequency), f"{keyword.tfidf_score:.3f}")

        _console.print(table)
        _console.print()

    if nlp_analysis.insights:
        _console.print("[bold]NLP 인사이트:[/bold]")
        for insight in nlp_analysis.insights:
            _console.print(f"  • {insight}")
        _console.print()


def _display_causal_analysis(causal_analysis) -> None:
    """Display causal analysis results."""

    _console.print("\n[bold magenta]인과 분석[/bold magenta]\n")

    significant_impacts = causal_analysis.significant_impacts
    if significant_impacts:
        _console.print("[bold]유의미한 요인-메트릭 관계:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("요인")
        table.add_column("메트릭")
        table.add_column("방향")
        table.add_column("강도")
        table.add_column("상관계수", justify="right")
        table.add_column("p-값", justify="right")

        for impact in significant_impacts[:10]:
            direction_style = "green" if impact.direction.value == "positive" else "red"
            table.add_row(
                impact.factor_type.value,
                impact.metric_name,
                f"[{direction_style}]{impact.direction.value}[/{direction_style}]",
                impact.strength.value,
                f"{impact.correlation:.3f}",
                f"{impact.p_value:.4f}",
            )

        _console.print(table)
        _console.print()

    strong_relationships = causal_analysis.strong_relationships
    if strong_relationships:
        _console.print("[bold]강한 인과 관계 (신뢰도 > 0.7):[/bold]")
        for rel in strong_relationships[:5]:
            direction_arrow = "↑" if rel.direction.value == "positive" else "↓"
            _console.print(
                f"  • {rel.cause.value} → {rel.effect_metric} {direction_arrow} "
                f"(신뢰도: {rel.confidence:.2f})"
            )
        _console.print()

    if causal_analysis.root_causes:
        _console.print("[bold]근본 원인 분석:[/bold]")
        for rc in causal_analysis.root_causes:
            primary_str = ", ".join(f.value for f in rc.primary_causes)
            _console.print(f"  [bold]{rc.metric_name}:[/bold]")
            _console.print(f"    주요 원인: {primary_str}")
            if rc.contributing_factors:
                contributing_str = ", ".join(f.value for f in rc.contributing_factors)
                _console.print(f"    기여 요인: {contributing_str}")
            if rc.explanation:
                _console.print(f"    설명: {rc.explanation}")
        _console.print()

    if causal_analysis.interventions:
        _console.print("[bold]권장 개입:[/bold]")
        for intervention in causal_analysis.interventions[:5]:
            priority_str = {1: "🔴 높음", 2: "🟡 중간", 3: "🟢 낮음"}.get(
                intervention.priority, f"우선순위 {intervention.priority}"
            )
            _console.print(f"  [{priority_str}] {intervention.intervention}")
            _console.print(f"      대상: {intervention.target_metric}")
            _console.print(f"      기대 효과: {intervention.expected_impact}")
        _console.print()

    if causal_analysis.insights:
        _console.print("[bold]인과 인사이트:[/bold]")
        for insight in causal_analysis.insights:
            _console.print(f"  • {insight}")
        _console.print()


def _export_analysis_json(
    analysis, output_path: Path, nlp_analysis=None, improvement_report=None
) -> None:
    """Export analysis to JSON file."""

    from dataclasses import asdict

    data = {
        "analysis_id": analysis.analysis_id,
        "run_id": analysis.run_id,
        "analysis_type": analysis.analysis_type.value,
        "created_at": analysis.created_at.isoformat(),
        "overall_pass_rate": analysis.overall_pass_rate,
        "metric_pass_rates": analysis.metric_pass_rates,
        "metrics_summary": {
            name: asdict(stats) for name, stats in analysis.metrics_summary.items()
        },
        "correlation_matrix": analysis.correlation_matrix,
        "correlation_metrics": analysis.correlation_metrics,
        "significant_correlations": [asdict(c) for c in analysis.significant_correlations],
        "low_performers": [asdict(lp) for lp in analysis.low_performers],
        "insights": analysis.insights,
    }

    if nlp_analysis:
        data["nlp_analysis"] = {
            "run_id": nlp_analysis.run_id,
            "question_stats": asdict(nlp_analysis.question_stats)
            if nlp_analysis.question_stats
            else None,
            "answer_stats": asdict(nlp_analysis.answer_stats)
            if nlp_analysis.answer_stats
            else None,
            "context_stats": asdict(nlp_analysis.context_stats)
            if nlp_analysis.context_stats
            else None,
            "question_types": [
                {
                    "question_type": qt.question_type.value,
                    "count": qt.count,
                    "percentage": qt.percentage,
                    "avg_scores": qt.avg_scores,
                }
                for qt in nlp_analysis.question_types
            ],
            "top_keywords": [asdict(kw) for kw in nlp_analysis.top_keywords],
            "insights": nlp_analysis.insights,
        }

    if improvement_report:
        data["improvement_report"] = improvement_report.to_dict()

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _perform_playbook_analysis(
    run,
    enable_llm: bool,
    profile: str | None,
    *,
    stage_metrics=None,
):
    """Perform playbook-based improvement analysis."""

    from evalvault.adapters.outbound.improvement.insight_generator import InsightGenerator
    from evalvault.adapters.outbound.improvement.pattern_detector import PatternDetector
    from evalvault.adapters.outbound.improvement.playbook_loader import get_default_playbook
    from evalvault.adapters.outbound.improvement.stage_metric_playbook_loader import (
        StageMetricPlaybookLoader,
    )
    from evalvault.domain.services.improvement_guide_service import ImprovementGuideService

    _console.print("\n[bold cyan]플레이북 기반 개선 분석[/bold cyan]\n")

    playbook = get_default_playbook()
    detector = PatternDetector(playbook=playbook)

    insight_generator = None
    if enable_llm:
        settings = Settings()
        profile_name = profile or settings.evalvault_profile
        if profile_name:
            settings = apply_profile(settings, profile_name)

        llm_adapter = get_llm_adapter(settings)
        insight_generator = InsightGenerator(llm_adapter=llm_adapter)
        _console.print("[dim]LLM 기반 인사이트 생성 활성화[/dim]")

    stage_metric_playbook = StageMetricPlaybookLoader().load()

    service = ImprovementGuideService(
        pattern_detector=detector,
        insight_generator=insight_generator,
        playbook=playbook,
        stage_metric_playbook=stage_metric_playbook,
        enable_llm_enrichment=enable_llm,
    )

    with _console.status("[bold green]패턴 분석 및 권장사항 생성 중..."):
        report = service.generate_report(
            run,
            include_llm_analysis=enable_llm,
            stage_metrics=stage_metrics,
        )

    _display_improvement_report(report)
    return report


def _display_improvement_report(report) -> None:
    """Display improvement report in console."""

    from evalvault.domain.entities.improvement import ImprovementPriority

    summary = f"""[bold]개선 분석 요약[/bold]
실행 ID: {report.run_id}
전체 테스트 케이스: {report.total_test_cases}
생성된 가이드: {len(report.guides)}
분석 방법: {", ".join(m.value for m in report.analysis_methods_used)}

[bold]메트릭 성능 vs 임계값[/bold]"""

    for metric, score in report.metric_scores.items():
        gap = report.metric_gaps.get(metric, 0)
        status = "[red]임계값 미달[/red]" if gap > 0 else "[green]임계값 충족[/green]"
        summary += f"\n  {metric}: {score:.3f} ({status})"
        if gap > 0:
            summary += f" [dim](격차: -{gap:.3f})[/dim]"

    _console.print(Panel(summary, title="[bold cyan]개선 분석[/bold cyan]", border_style="cyan"))

    stage_summary = report.metadata.get("stage_metrics_summary")
    if stage_summary:
        pass_rate = stage_summary.get("pass_rate")
        pass_rate_text = f"{pass_rate:.1%}" if pass_rate is not None else "-"
        _console.print(
            "\n[bold]스테이지 메트릭 요약[/bold] "
            f"(평가됨: {stage_summary.get('evaluated', 0)}, "
            f"통과: {stage_summary.get('passed', 0)}, "
            f"실패: {stage_summary.get('failed', 0)}, "
            f"통과율: {pass_rate_text})"
        )
        top_failures = stage_summary.get("top_failures", [])
        if top_failures:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("메트릭")
            table.add_column("실패 건수", justify="right")
            table.add_column("평균 점수", justify="right")
            table.add_column("임계값", justify="right")
            for item in top_failures:
                threshold = item.get("threshold")
                threshold_text = f"{threshold:.3f}" if threshold is not None else "-"
                table.add_row(
                    str(item.get("metric_name", "-")),
                    str(item.get("count", 0)),
                    f"{item.get('avg_score', 0.0):.3f}",
                    threshold_text,
                )
            _console.print(table)
        else:
            _console.print("[green]스테이지 메트릭 실패가 없습니다.[/green]")

    if not report.guides:
        _console.print("[yellow]개선 가이드가 생성되지 않았습니다.[/yellow]")
        return

    critical_guides = report.get_critical_guides()
    if critical_guides:
        _console.print("\n[bold red]치명적 이슈 (P0)[/bold red]")
        for guide in critical_guides:
            _display_guide(guide)

    high_priority = [g for g in report.guides if g.priority == ImprovementPriority.P1_HIGH]
    if high_priority:
        _console.print("\n[bold yellow]높은 우선순위 (P1)[/bold yellow]")
        for guide in high_priority[:3]:
            _display_guide(guide)

    medium_priority = [g for g in report.guides if g.priority == ImprovementPriority.P2_MEDIUM]
    if medium_priority:
        _console.print("\n[bold blue]중간 우선순위 (P2)[/bold blue]")
        for guide in medium_priority[:2]:
            _display_guide(guide)


def _display_guide(guide) -> None:
    """Display a single improvement guide."""

    component_icons = {
        "retriever": "🔍",
        "reranker": "📊",
        "generator": "🤖",
        "chunker": "📄",
        "embedder": "📐",
        "query_processor": "🔧",
        "prompt": "💬",
    }

    icon = component_icons.get(guide.component.value, "📌")
    _console.print(
        f"\n  {icon} [bold]{guide.component.value.upper()}[/bold] - {', '.join(guide.target_metrics)}"
    )

    if guide.evidence:
        primary = guide.evidence.primary_pattern
        if primary:
            _console.print(f"     패턴: {primary.pattern_type.value}")
            _console.print(
                f"     영향: {primary.affected_count}/{primary.total_count} 테스트 케이스 "
                f"({primary.affected_ratio:.1%})"
            )
        elif guide.evidence.total_failures > 0:
            _console.print(f"     실패: {guide.evidence.total_failures} 테스트 케이스")
            _console.print(f"     실패 평균 점수: {guide.evidence.avg_score_failures:.3f}")

    if guide.actions:
        _console.print("     [bold]권장 조치:[/bold]")
        for action in guide.actions[:3]:
            effort_color = {"low": "green", "medium": "yellow", "high": "red"}.get(
                action.effort, "white"
            )
            effort_label = {"low": "낮음", "medium": "중간", "high": "높음"}.get(
                action.effort, action.effort
            )
            _console.print(f"       • {action.title}")
            if action.description:
                if len(action.description) > 60:
                    _console.print(f"         [dim]{action.description[:60]}...[/dim]")
                else:
                    _console.print(f"         [dim]{action.description}[/dim]")
            _console.print(
                f"         기대 개선: +{action.expected_improvement:.1%} | 노력도: "
                f"[{effort_color}]{effort_label}[/{effort_color}]"
            )

    if guide.verification_command:
        _console.print(f"     [dim]검증: {guide.verification_command}[/dim]")


def _generate_report(
    bundle, output_path: Path, include_nlp: bool = True, improvement_report=None
) -> None:
    """Generate analysis report (Markdown or HTML)."""

    adapter = MarkdownReportAdapter()
    suffix = output_path.suffix.lower()
    if suffix == ".html":
        content = adapter.generate_html(bundle, include_nlp=include_nlp)
    else:
        content = adapter.generate_markdown(bundle, include_nlp=include_nlp)

    if improvement_report:
        stage_summary = improvement_report.metadata.get("stage_metrics_summary")
        if stage_summary:
            pass_rate = stage_summary.get("pass_rate")
            pass_rate_text = f"{pass_rate:.1%}" if pass_rate is not None else "해당 없음"
            content += "\n\n## 스테이지 메트릭 요약\n"
            content += f"\n- 전체 메트릭: {stage_summary.get('total', 0)}"
            content += f"\n- 평가됨: {stage_summary.get('evaluated', 0)}"
            content += (
                f"\n- 통과: {stage_summary.get('passed', 0)} / "
                f"실패: {stage_summary.get('failed', 0)}"
            )
            content += f"\n- 통과율: {pass_rate_text}\n"
            top_failures = stage_summary.get("top_failures", [])
            if top_failures:
                content += "\n| 메트릭 | 실패 건수 | 평균 점수 | 임계값 |\n"
                content += "|--------|----------|-----------|--------|\n"
                for item in top_failures:
                    threshold = item.get("threshold")
                    threshold_text = f"{threshold:.3f}" if threshold is not None else "-"
                    content += (
                        f"| {item.get('metric_name')} | {item.get('count', 0)} | "
                        f"{item.get('avg_score', 0.0):.3f} | {threshold_text} |\n"
                    )
        content += "\n\n" + improvement_report.to_markdown()

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(content)


def _display_anomaly_detection(anomaly_result) -> None:
    _console.print("\n[bold]Anomaly Detection Results[/bold]")
    _console.print(f"Detection method: {anomaly_result.detection_method}")
    _console.print(f"Threshold: {anomaly_result.threshold:.2f}")
    _console.print(f"Total runs: {anomaly_result.total_runs}")

    if anomaly_result.anomalies:
        detected = [a for a in anomaly_result.anomalies if a.is_anomaly]
        if detected:
            _console.print(f"\n[red]Detected {len(detected)} anomalies:[/red]")
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Run ID")
            table.add_column("Score", justify="right")
            table.add_column("Pass Rate", justify="right")
            table.add_column("Severity")

            for anomaly in detected[:10]:
                severity_color = (
                    "red"
                    if anomaly.severity == "high"
                    else "yellow"
                    if anomaly.severity == "medium"
                    else "green"
                )
                table.add_row(
                    anomaly.run_id[:12] + "...",
                    f"{anomaly.anomaly_score:.2f}",
                    f"{anomaly.pass_rate:.1%}",
                    f"[{severity_color}]{anomaly.severity}[/{severity_color}]",
                )
            _console.print(table)
        else:
            _console.print("[green]No anomalies detected.[/green]")

    if anomaly_result.insights:
        _console.print("\n[bold]Insights:[/bold]")
        for insight in anomaly_result.insights:
            _console.print(f"  • {insight}")


def _display_forecast_result(forecast_result) -> None:
    _console.print("\n[bold]Forecast Results[/bold]")
    _console.print(f"Method: {forecast_result.method}")
    _console.print(f"Horizon: {forecast_result.horizon} runs")

    if forecast_result.predicted_values:
        _console.print("\n[bold]Predicted Pass Rates:[/bold]")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Run")
        table.add_column("Predicted", justify="right")

        for i, value in enumerate(forecast_result.predicted_values, 1):
            table.add_row(f"+{i}", f"{value:.1%}")
        _console.print(table)

        avg_forecast = sum(forecast_result.predicted_values) / len(forecast_result.predicted_values)
        _console.print(f"\nAverage forecast: {avg_forecast:.1%}")


def _display_network_analysis(net_result) -> None:
    _console.print("\n[bold]Network Analysis Results[/bold]")
    _console.print(f"Nodes (metrics): {net_result.node_count}")
    _console.print(f"Edges (correlations): {net_result.edge_count}")
    _console.print(f"Density: {net_result.density:.3f}")
    _console.print(f"Avg clustering: {net_result.avg_clustering:.3f}")

    if net_result.communities:
        _console.print(f"\n[bold]Communities ({len(net_result.communities)}):[/bold]")
        for i, community in enumerate(net_result.communities):
            if len(community) > 1:
                _console.print(f"  Community {i + 1}: {', '.join(community)}")

    if net_result.hub_metrics:
        _console.print("\n[bold]Hub Metrics:[/bold]")
        for metric in net_result.hub_metrics:
            _console.print(f"  • {metric}")

    if net_result.insights:
        _console.print("\n[bold]Insights:[/bold]")
        for insight in net_result.insights:
            _console.print(f"  • {insight}")


def _display_hypothesis_generation(hypotheses, method: str) -> None:
    _console.print("\n[bold]Hypothesis Generation Results[/bold]")
    _console.print(f"Method: {method}")
    _console.print(f"Total hypotheses: {len(hypotheses)}")

    if hypotheses:
        _console.print("\n[bold]Generated Hypotheses:[/bold]")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#")
        table.add_column("Hypothesis")
        table.add_column("Metric")
        table.add_column("Confidence", justify="right")
        table.add_column("Evidence")

        for i, hyp in enumerate(hypotheses[:10], 1):
            confidence_color = (
                "green" if hyp.confidence >= 0.8 else "yellow" if hyp.confidence >= 0.6 else "red"
            )
            table.add_row(
                str(i),
                hyp.text[:60] + "..." if len(hyp.text) > 60 else hyp.text,
                hyp.metric_name or "-",
                f"[{confidence_color}]{hyp.confidence:.2f}[/{confidence_color}]",
                hyp.evidence[:30] + "..." if len(hyp.evidence) > 30 else hyp.evidence,
            )
        _console.print(table)

        high_conf = [h for h in hypotheses if h.confidence >= 0.8]
        if high_conf:
            _console.print(
                f"\n[green]High confidence hypotheses: {len(high_conf)}/{len(hypotheses)}[/green]"
            )


__all__ = [
    "register_analyze_commands",
    "_perform_playbook_analysis",
    "_display_improvement_report",
]
