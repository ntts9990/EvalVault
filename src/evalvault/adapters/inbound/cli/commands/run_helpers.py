"""`evalvault run` 명령을 보조하는 헬퍼 모음."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import click
import typer
from click.core import ParameterSource
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from evalvault.adapters.outbound.dataset import StreamingConfig, StreamingDatasetLoader
from evalvault.adapters.outbound.dataset.thresholds import extract_thresholds_from_rows
from evalvault.adapters.outbound.kg.networkx_adapter import NetworkXKnowledgeGraph
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.adapters.outbound.storage.postgres_adapter import PostgreSQLStorageAdapter
from evalvault.config.phoenix_support import (
    get_phoenix_trace_url,
    instrumentation_span,
    set_span_attributes,
)
from evalvault.config.settings import Settings, resolve_tracker_providers
from evalvault.domain.entities import (
    Dataset,
    EvaluationRun,
    GenerationData,
    MultiTurnConversationRecord,
    MultiTurnRunRecord,
    MultiTurnTurnResult,
    PromptSetBundle,
    RAGTraceData,
    RetrievalData,
    RetrievedDocument,
    StageEvent,
)
from evalvault.domain.services import retriever_context
from evalvault.domain.services.dataset_preprocessor import merge_preprocess_summaries
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.domain.services.memory_aware_evaluator import MemoryAwareEvaluator
from evalvault.domain.services.prompt_manifest import (
    PromptDiffSummary,
    load_prompt_manifest,
    summarize_prompt_entry,
)
from evalvault.domain.services.threshold_profiles import (
    SUMMARY_RECOMMENDED_THRESHOLDS,
    apply_threshold_profile,
)
from evalvault.ports.outbound.llm_port import LLMPort
from evalvault.ports.outbound.tracker_port import TrackerPort

from ..utils.console import print_cli_error, print_cli_warning
from ..utils.formatters import format_score, format_status

TrackerType = str
apply_retriever_to_dataset = retriever_context.apply_retriever_to_dataset


@dataclass(frozen=True)
class RunModePreset:
    """심플/전체 실행 모드를 정의한다."""

    name: str
    label: str
    description: str
    default_metrics: tuple[str, ...] | None = None
    default_tracker: TrackerType | None = None
    allow_domain_memory: bool = True
    allow_prompt_metadata: bool = True


RUN_MODE_PRESETS: dict[str, RunModePreset] = {
    "simple": RunModePreset(
        name="simple",
        label="Simple",
        description="기본 메트릭 2종과 Phoenix 추적만 활성화된 간편 실행 모드.",
        default_metrics=("faithfulness", "answer_relevancy"),
        default_tracker="phoenix",
        allow_domain_memory=False,
        allow_prompt_metadata=False,
    ),
    "full": RunModePreset(
        name="full",
        label="Full",
        description="모든 CLI 옵션과 Domain Memory, Prompt manifest를 활용하는 전체 모드.",
    ),
    "multiturn": RunModePreset(
        name="multiturn",
        label="Multiturn",
        description="멀티턴 대화 평가 전용 모드 (멀티턴 메트릭만 지원).",
        default_metrics=("turn_faithfulness", "context_coherence", "drift_rate"),
        allow_domain_memory=False,
        allow_prompt_metadata=False,
    ),
}

SUMMARY_METRIC_ORDER = (
    "summary_faithfulness",
    "summary_score",
    "entity_preservation",
    "summary_accuracy",
    "summary_risk_coverage",
    "summary_non_definitive",
    "summary_needs_followup",
)

SUMMARY_METRIC_SOURCE = {
    "summary_faithfulness": "LLM",
    "summary_score": "LLM",
    "entity_preservation": "Rule",
    "summary_accuracy": "Rule",
    "summary_risk_coverage": "Rule",
    "summary_non_definitive": "Rule",
    "summary_needs_followup": "Rule",
}


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
    _display_summary_guidance(result, console)

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
                # Display claim-level details if available
                if metric.claim_details:
                    cd = metric.claim_details
                    console.print(
                        f"      [dim]Claims: {cd.total_claims} total, "
                        f"{cd.supported_claims} supported, "
                        f"{cd.not_supported_claims} not supported[/dim]"
                    )
                    # Show failed claims
                    for claim in cd.claims:
                        if claim.verdict != "supported":
                            verdict_color = "red" if claim.verdict == "not_supported" else "yellow"
                            console.print(
                                f"        [{verdict_color}]✗[/{verdict_color}] "
                                f"{claim.claim_text[:80]}{'...' if len(claim.claim_text) > 80 else ''}"
                            )
                            if claim.reason:
                                console.print(f"          [dim]{claim.reason}[/dim]")


def _display_summary_guidance(result, console: Console) -> None:
    summary_metrics = [
        metric for metric in result.metrics_evaluated if metric in SUMMARY_RECOMMENDED_THRESHOLDS
    ]
    if not summary_metrics:
        return

    threshold_line = ", ".join(
        f"{metric}>={SUMMARY_RECOMMENDED_THRESHOLDS[metric]:.2f}"
        for metric in SUMMARY_METRIC_ORDER
        if metric in SUMMARY_RECOMMENDED_THRESHOLDS
    )
    warnings = []
    for metric in summary_metrics:
        score = result.get_avg_score(metric)
        if score is None:
            continue
        recommended = SUMMARY_RECOMMENDED_THRESHOLDS[metric]
        source = SUMMARY_METRIC_SOURCE.get(metric, "Rule")
        if score < recommended:
            warnings.append(f"- {metric} ({source}): {score:.3f} < {recommended:.2f}")

    if warnings:
        header = "[bold red]사용자 노출 기준 미달[/bold red]"
        border_style = "red"
    else:
        header = "[bold]요약 평가 기준 참고[/bold]"
        border_style = "yellow"

    lines = [
        header,
        *warnings,
        "",
        f"- 권장 기준: {threshold_line}",
        "- 혼용 언어/temperature 변동으로 점수가 흔들릴 수 있어 다회 실행 평균 확인을 권장합니다.",
        "- 참고 문서: docs/guides/RAGAS_PERFORMANCE_TUNING.md, "
        "docs/internal/reports/TEMPERATURE_SEED_ANALYSIS.md",
    ]

    console.print(Panel("\n".join(lines), title="Summary Evaluation", border_style=border_style))


def format_dataset_preprocess_summary(summary: dict[str, Any] | None) -> str | None:
    """Build a short human-readable summary for dataset preprocessing output."""

    if not summary:
        return None

    reference_filled = int(summary.get("references_filled_from_answer", 0) or 0) + int(
        summary.get("references_filled_from_context", 0) or 0
    )
    contexts_cleaned = int(summary.get("contexts_removed", 0) or 0) + int(
        summary.get("contexts_deduped", 0) or 0
    )
    contexts_trimmed = int(summary.get("contexts_truncated", 0) or 0) + int(
        summary.get("contexts_limited", 0) or 0
    )
    references_missing = int(summary.get("references_missing", 0) or 0)
    references_short = int(summary.get("references_short", 0) or 0)
    dropped_cases = int(summary.get("dropped_cases", 0) or 0)
    empty_questions = int(summary.get("empty_questions", 0) or 0)
    empty_answers = int(summary.get("empty_answers", 0) or 0)

    parts: list[str] = []
    if reference_filled:
        parts.append(
            "reference 보강 "
            f"{reference_filled}건(답변 {summary.get('references_filled_from_answer', 0)}"
            f"/컨텍스트 {summary.get('references_filled_from_context', 0)})"
        )
    reference_issues = max(0, references_missing + references_short - reference_filled)
    if reference_issues:
        parts.append(f"reference 부족 {reference_issues}건")
    if contexts_cleaned or contexts_trimmed:
        parts.append(
            "컨텍스트 정리 "
            f"{contexts_cleaned + contexts_trimmed}건(빈값/중복 {contexts_cleaned}"
            f", 길이/개수 제한 {contexts_trimmed})"
        )
    if dropped_cases:
        parts.append(f"케이스 제외 {dropped_cases}건")
    if empty_questions or empty_answers:
        parts.append(
            "비어있는 필드 "
            f"{empty_questions + empty_answers}건(질문 {empty_questions}/답변 {empty_answers})"
        )

    if not parts:
        return None
    return "데이터셋 전처리: " + ", ".join(parts)


def _display_memory_insights(insights: dict[str, Any], console: Console) -> None:
    """Render Domain Memory insights panel."""

    if not insights:
        return

    recommendations = insights.get("recommendations") or []
    trends = insights.get("trends") or {}
    if not recommendations and not trends:
        return

    trend_lines: list[str] = []
    for metric, info in list(trends.items())[:3]:
        delta = info.get("delta", 0.0)
        baseline = info.get("baseline", 0.0)
        current = info.get("current", 0.0)
        trend_lines.append(
            f"- {metric}: Δ {delta:+.2f} (current {current:.2f} / baseline {baseline:.2f})"
        )

    recommendation_lines = [f"- {rec}" for rec in recommendations[:3]]
    if not trend_lines and not recommendation_lines:
        return

    panel_body = ""
    if trend_lines:
        panel_body += "[bold]Trend Signals[/bold]\n" + "\n".join(trend_lines) + "\n"
    if recommendation_lines:
        if panel_body:
            panel_body += "\n"
        panel_body += "[bold]Recommendations[/bold]\n" + "\n".join(recommendation_lines)

    console.print(Panel(panel_body, title="Domain Memory Insights", border_style="magenta"))


def _get_tracker(
    settings: Settings,
    tracker_type: str,
    console: Console,
    *,
    required: bool = False,
) -> TrackerPort | None:
    """Get the appropriate tracker adapter based on type."""
    if tracker_type == "langfuse":
        if not settings.langfuse_public_key or not settings.langfuse_secret_key:
            message = "Langfuse 자격 증명이 설정되지 않았습니다."
            tips = ["LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY를 .env에 추가하세요."]
            if required:
                print_cli_error(console, message, fixes=tips)
                raise typer.Exit(2)
            print_cli_warning(console, message + " 로깅을 건너뜁니다.", tips=tips)
            return None
        from evalvault.adapters.outbound.tracker.langfuse_adapter import LangfuseAdapter

        return LangfuseAdapter(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )

    elif tracker_type == "mlflow":
        if not settings.mlflow_tracking_uri:
            message = "MLflow tracking URI가 설정되지 않았습니다."
            tips = ["MLFLOW_TRACKING_URI 환경 변수를 설정하세요."]
            if required:
                print_cli_error(console, message, fixes=tips)
                raise typer.Exit(2)
            print_cli_warning(console, message + " 로깅을 건너뜁니다.", tips=tips)
            return None
        try:
            from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

            return MLflowAdapter(
                tracking_uri=settings.mlflow_tracking_uri,
                experiment_name=settings.mlflow_experiment_name,
            )
        except ImportError:
            message = "MLflow extra가 설치되지 않았습니다."
            tips = ["uv sync --extra mlflow 명령으로 구성요소를 설치하세요."]
            if required:
                print_cli_error(console, message, fixes=tips)
                raise typer.Exit(2)
            print_cli_warning(console, message, tips=tips)
            return None

    elif tracker_type == "phoenix":
        try:
            from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

            return PhoenixAdapter(
                endpoint=settings.phoenix_endpoint,
                service_name="evalvault",
                project_name=getattr(settings, "phoenix_project_name", None),
                annotations_enabled=getattr(settings, "phoenix_annotations_enabled", True),
            )
        except ImportError:
            message = "Phoenix extra가 설치되지 않았습니다."
            tips = ["uv sync --extra phoenix 명령으로 의존성을 추가하세요."]
            if required:
                print_cli_error(console, message, fixes=tips)
                raise typer.Exit(2)
            print_cli_warning(console, message, tips=tips)
            return None

    else:
        print_cli_warning(
            console,
            f"알 수 없는 tracker 타입입니다: {tracker_type}",
            tips=["langfuse/mlflow/phoenix/none 중 하나를 지정하세요."],
        )
        return None


def _resolve_tracker_list(tracker_type: str) -> list[str]:
    providers = resolve_tracker_providers(tracker_type)
    if not providers:
        return []
    if providers == ["none"]:
        return ["none"]
    supported = {"langfuse", "mlflow", "phoenix"}
    unknown = [entry for entry in providers if entry not in supported]
    if unknown:
        raise ValueError(f"Unknown tracker provider(s): {', '.join(unknown)}")
    required = {"mlflow", "phoenix"}
    if not required.issubset(set(providers)):
        raise ValueError("tracker must include both 'mlflow' and 'phoenix'")
    return providers


def _build_phoenix_trace_url(endpoint: str, trace_id: str) -> str:
    """Build a Phoenix UI URL for the given trace ID."""

    base = endpoint.rstrip("/")
    suffix = "/v1/traces"
    if base.endswith(suffix):
        base = base[: -len(suffix)]
    return f"{base.rstrip('/')}/#/traces/{trace_id}"


def _log_to_trackers(
    settings: Settings,
    result,
    console: Console,
    tracker_type: str,
    *,
    phoenix_options: dict[str, Any] | None = None,
    log_phoenix_traces_fn: Callable[..., int] | None = None,
) -> None:
    """Log evaluation results to the specified tracker(s)."""
    try:
        tracker_types = _resolve_tracker_list(tracker_type)
    except ValueError as exc:
        print_cli_error(console, "Tracker 설정이 올바르지 않습니다.", details=str(exc))
        raise typer.Exit(2) from exc
    if not tracker_types or tracker_types == ["none"]:
        return

    result.tracker_metadata.setdefault("tracker_providers", tracker_types)
    for provider in tracker_types:
        tracker = _get_tracker(settings, provider, console, required=True)
        if tracker is None:
            raise typer.Exit(2)
        tracker_name = provider.capitalize()
        trace_id: str | None = None
        with console.status(f"[bold green]Logging to {tracker_name}..."):
            try:
                trace_id = tracker.log_evaluation_run(result)
                console.print(f"[green]Logged to {tracker_name}[/green] (trace_id: {trace_id})")
            except Exception as exc:
                print_cli_error(
                    console,
                    f"{tracker_name} 로깅에 실패했습니다.",
                    details=str(exc),
                )
                raise typer.Exit(2) from exc

        if trace_id:
            provider_meta = result.tracker_metadata.setdefault(provider, {})
            if isinstance(provider_meta, dict):
                provider_meta.setdefault("trace_id", trace_id)
            if provider == "phoenix":
                endpoint = getattr(settings, "phoenix_endpoint", "http://localhost:6006/v1/traces")
                if not isinstance(endpoint, str) or not endpoint:
                    endpoint = "http://localhost:6006/v1/traces"
                phoenix_meta = result.tracker_metadata.setdefault("phoenix", {})
                phoenix_meta.update(
                    {
                        "trace_id": trace_id,
                        "endpoint": endpoint,
                        "trace_url": _build_phoenix_trace_url(endpoint, trace_id),
                    }
                )
                phoenix_meta.setdefault("schema_version", 2)
                trace_url = get_phoenix_trace_url(result.tracker_metadata)
                if trace_url:
                    console.print(f"[dim]Phoenix Trace: {trace_url}[/dim]")

                options = phoenix_options or {}
                log_traces = log_phoenix_traces_fn or log_phoenix_traces
                extra = log_traces(
                    tracker,
                    result,
                    max_traces=options.get("max_traces"),
                    metadata=options.get("metadata"),
                )
                if extra:
                    console.print(
                        f"[dim]Recorded {extra} Phoenix RAG trace(s) for detailed observability.[/dim]"
                    )


def _log_analysis_artifacts(
    settings: Settings,
    result: EvaluationRun,
    console: Console,
    tracker_type: str,
    *,
    analysis_payload: dict[str, Any],
    artifact_index: dict[str, Any],
    report_text: str,
    output_path: Path,
    report_path: Path,
) -> None:
    """Log analysis artifacts to tracker(s) as a separate trace/run."""
    try:
        tracker_types = _resolve_tracker_list(tracker_type)
    except ValueError as exc:
        print_cli_error(console, "Tracker 설정이 올바르지 않습니다.", details=str(exc))
        raise typer.Exit(2) from exc
    if not tracker_types or tracker_types == ["none"]:
        return

    metadata = {
        "run_id": result.run_id,
        "dataset_name": result.dataset_name,
        "dataset_version": result.dataset_version,
        "analysis_output": str(output_path),
        "analysis_report": str(report_path),
        "analysis_artifacts_dir": artifact_index.get("dir"),
        "event_type": "analysis",
    }

    for provider in tracker_types:
        tracker = _get_tracker(settings, provider, console, required=True)
        if tracker is None:
            raise typer.Exit(2)
        trace_name = f"analysis-{result.run_id[:8]}"
        try:
            trace_id = tracker.start_trace(trace_name, metadata=metadata)
            tracker.save_artifact(
                trace_id, "analysis_payload", analysis_payload, artifact_type="json"
            )
            tracker.save_artifact(
                trace_id, "analysis_artifacts", artifact_index, artifact_type="json"
            )
            tracker.save_artifact(trace_id, "analysis_report", report_text, artifact_type="text")
            tracker.end_trace(trace_id)
            console.print(
                f"[green]Logged analysis artifacts to {provider.capitalize()}[/green] "
                f"(trace_id: {trace_id})"
            )
        except Exception as exc:
            print_cli_error(
                console,
                f"{provider.capitalize()} 분석 로깅에 실패했습니다.",
                details=str(exc),
            )
            raise typer.Exit(2) from exc


def _save_to_db(
    db_path: Path | None,
    result,
    console: Console,
    *,
    prompt_bundle: PromptSetBundle | None = None,
    export_excel: bool = True,
) -> None:
    """Persist evaluation run (and optional prompt set) to database."""
    storage = build_storage_adapter(settings=Settings(), db_path=db_path)
    storage_label = (
        "PostgreSQL" if isinstance(storage, PostgreSQLStorageAdapter) else f"SQLite ({db_path})"
    )
    export_base = db_path.parent if db_path else Path("data/exports")
    with console.status(f"[bold green]Saving to database {storage_label}..."):
        try:
            if prompt_bundle:
                storage.save_prompt_set(prompt_bundle)
            storage.save_run(result)
            if prompt_bundle:
                storage.link_prompt_set_to_run(
                    result.run_id,
                    prompt_bundle.prompt_set.prompt_set_id,
                )
            if export_excel:
                export_base.mkdir(parents=True, exist_ok=True)
                excel_path = export_base / f"evalvault_run_{result.run_id}.xlsx"
                try:
                    storage.export_run_to_excel(result.run_id, excel_path)
                    console.print(f"[green]Excel export saved: {excel_path}[/green]")
                except Exception as exc:
                    print_cli_warning(
                        console,
                        "엑셀 내보내기에 실패했습니다.",
                        tips=[str(exc)],
                    )
            console.print(f"[green]Results saved to database: {storage_label}[/green]")
            console.print(f"[dim]Run ID: {result.run_id}[/dim]")
            if prompt_bundle:
                console.print(
                    f"[dim]Prompt set saved: {prompt_bundle.prompt_set.name} "
                    f"({prompt_bundle.prompt_set.prompt_set_id[:8]})[/dim]"
                )
        except Exception as exc:  # pragma: no cover - persistence errors
            print_cli_error(
                console,
                "데이터베이스에 저장하지 못했습니다.",
                details=str(exc),
                fixes=["경로 권한과 DB 파일 잠금 상태를 확인하세요."],
            )


def _save_multiturn_to_db(
    db_path: Path | None,
    run_record: MultiTurnRunRecord,
    conversations: list[MultiTurnConversationRecord],
    turn_results: list[MultiTurnTurnResult],
    console: Console,
    *,
    export_excel: bool = True,
    excel_output_path: Path | None = None,
    metric_thresholds: dict[str, float] | None = None,
) -> None:
    """Persist multiturn evaluation run to database."""
    storage = build_storage_adapter(settings=Settings(), db_path=db_path)
    storage_label = (
        "PostgreSQL" if isinstance(storage, PostgreSQLStorageAdapter) else f"SQLite ({db_path})"
    )
    export_base = db_path.parent if db_path else Path("data/exports")
    with console.status(f"[bold green]Saving multiturn run to {storage_label}..."):
        try:
            storage.save_multiturn_run(
                run_record,
                conversations,
                turn_results,
                metric_thresholds=metric_thresholds,
            )
            if export_excel:
                export_base.mkdir(parents=True, exist_ok=True)
                excel_path = excel_output_path or (
                    export_base / f"evalvault_multiturn_{run_record.run_id}.xlsx"
                )
                try:
                    storage.export_multiturn_run_to_excel(run_record.run_id, excel_path)
                    console.print(f"[green]Multiturn Excel export saved: {excel_path}[/green]")
                except Exception as exc:
                    print_cli_warning(
                        console,
                        "멀티턴 엑셀 내보내기에 실패했습니다.",
                        tips=[str(exc)],
                    )
            console.print(f"[green]Multiturn results saved to database: {storage_label}[/green]")
            console.print(f"[dim]Run ID: {run_record.run_id}[/dim]")
        except Exception as exc:  # pragma: no cover - persistence errors
            print_cli_error(
                console,
                "멀티턴 결과를 데이터베이스에 저장하지 못했습니다.",
                details=str(exc),
                fixes=["경로 권한과 DB 파일 잠금 상태를 확인하세요."],
            )


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
            if result.retrieval_metadata:
                data["retrieval_metadata"] = result.retrieval_metadata

            with open(output, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            console.print(f"[green]Results saved to {output}[/green]")
        except Exception as exc:  # pragma: no cover - filesystem errors
            print_cli_error(
                console,
                "결과 파일 저장에 실패했습니다.",
                details=str(exc),
                fixes=["출력 경로 쓰기 권한을 확인하고 재시도하세요."],
            )


def enrich_dataset_with_memory(
    *,
    dataset: Dataset,
    memory_evaluator: MemoryAwareEvaluator,
    domain: str,
    language: str,
) -> int:
    """Append memory-derived facts to dataset contexts."""

    span_attrs = {
        "domain_memory.domain": domain,
        "domain_memory.language": language,
        "dataset.name": dataset.name,
        "dataset.version": dataset.version,
    }
    enriched = 0
    with instrumentation_span("domain_memory.enrich_dataset", span_attrs) as span:
        for test_case in dataset.test_cases:
            augmented = memory_evaluator.augment_context_with_facts(
                question=test_case.question,
                original_context="",
                domain=domain,
                language=language,
            ).strip()
            if augmented and augmented not in test_case.contexts:
                test_case.contexts.append(augmented)
                enriched += 1
        if span:
            set_span_attributes(
                span,
                {
                    "domain_memory.enriched_cases": enriched,
                    "dataset.test_cases": len(dataset.test_cases),
                },
            )
    return enriched


def load_knowledge_graph(file_path: Path) -> NetworkXKnowledgeGraph:
    """Load a knowledge graph JSON file."""

    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("invalid knowledge graph JSON") from exc

    if isinstance(payload, dict) and "knowledge_graph" in payload:
        payload = payload["knowledge_graph"]

    if not isinstance(payload, dict):
        raise ValueError("knowledge graph JSON must be an object with entities and relations")

    return NetworkXKnowledgeGraph.from_dict(payload)


def load_retriever_documents(file_path: Path) -> tuple[list[str], list[str]]:
    """Load retrieval documents and their ids from JSON/JSONL/text files."""

    suffix = file_path.suffix.lower()
    if suffix == ".jsonl":
        items = _load_retriever_jsonl(file_path)
    elif suffix == ".json":
        items = _load_retriever_json(file_path)
    else:
        items = _load_retriever_text(file_path)

    documents: list[str] = []
    doc_ids: list[str] = []

    for idx, item in enumerate(items, start=1):
        content, doc_id = _normalize_document_item(item, idx)
        if not content:
            continue
        documents.append(content)
        doc_ids.append(doc_id)

    if not documents:
        raise ValueError("retriever documents are empty")

    return documents, doc_ids


def _load_retriever_json(file_path: Path) -> list[Any]:
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("invalid JSON retriever documents") from exc

    if isinstance(payload, dict) and "documents" in payload:
        items = payload["documents"]
    else:
        items = payload

    if not isinstance(items, list):
        raise ValueError("retriever JSON must be a list or contain 'documents'")

    return items


def _load_retriever_jsonl(file_path: Path) -> list[Any]:
    items: list[Any] = []
    with file_path.open(encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                items.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at line {idx}") from exc
    return items


def _load_retriever_text(file_path: Path) -> list[str]:
    items: list[str] = []
    with file_path.open(encoding="utf-8") as handle:
        for line in handle:
            content = line.strip()
            if content:
                items.append(content)
    return items


def _normalize_document_item(item: Any, index: int) -> tuple[str | None, str]:
    if isinstance(item, str):
        return item, f"doc_{index}"
    if isinstance(item, dict):
        content = item.get("content") or item.get("text") or item.get("document")
        doc_id = item.get("doc_id") or item.get("id") or f"doc_{index}"
        return (str(content) if isinstance(content, str) else None, str(doc_id))
    return None, f"doc_{index}"


def log_phoenix_traces(
    tracker: TrackerPort,
    run: EvaluationRun,
    *,
    max_traces: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> int:
    """Log per-test-case RAG traces when Phoenix adapter supports it."""

    log_trace = getattr(tracker, "log_rag_trace", None)
    if not callable(log_trace):
        return 0

    limit = max_traces if max_traces is not None else run.total_test_cases

    count = 0
    for result in run.results:
        retrieval_data = None
        if result.contexts:
            docs = []
            for idx, ctx in enumerate(result.contexts, start=1):
                docs.append(
                    RetrievedDocument(
                        content=ctx,
                        score=max(0.1, 1 - 0.05 * (idx - 1)),
                        rank=idx,
                        source=f"context_{idx}",
                    )
                )
            retrieval_data = RetrievalData(
                query=result.question or "",
                retrieval_method="dataset",
                top_k=len(docs),
                retrieval_time_ms=result.latency_ms or 0,
                candidates=docs,
            )

        generation_data = GenerationData(
            model=run.model_name,
            prompt=result.question or "",
            response=result.answer or "",
            generation_time_ms=result.latency_ms or 0,
            input_tokens=0,
            output_tokens=0,
            total_tokens=result.tokens_used,
        )

        trace_metadata = {
            "run_id": run.run_id,
            "test_case_id": result.test_case_id,
        }
        if metadata:
            trace_metadata.update(metadata)

        rag_trace = RAGTraceData(
            query=result.question or "",
            retrieval=retrieval_data,
            generation=generation_data,
            final_answer=result.answer or "",
            total_time_ms=result.latency_ms or 0,
            metadata=trace_metadata,
        )

        try:
            log_trace(rag_trace)
            count += 1
        except Exception:  # pragma: no cover - telemetry best effort
            break

        if limit is not None and count >= limit:
            break

    return count


def _write_stage_events_jsonl(path: Path, events: Sequence[StageEvent]) -> int:
    """Persist stage events as JSONL for downstream ingestion."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
    return len(events)


def _is_oss_open_model(model_name: str | None) -> bool:
    """Return True when a model should be routed through the OSS/Ollama backend."""

    if not model_name:
        return False
    normalized = model_name.lower()
    return normalized.startswith("gpt-oss-")


def _build_streaming_dataset_template(dataset_path: Path) -> Dataset:
    """Construct a Dataset stub for streaming mode using metadata from source file."""

    path = Path(dataset_path)
    metadata: dict[str, Any] = {"source_file": str(path)}
    thresholds: dict[str, float] = {}
    name = path.stem
    version = "stream"

    suffix = path.suffix.lower()
    if suffix == ".json":
        (
            name,
            version,
            metadata_from_file,
            thresholds_from_file,
        ) = _load_json_metadata_for_stream(path)
        metadata.update(metadata_from_file)
        thresholds.update(thresholds_from_file)
    elif suffix == ".csv":
        thresholds.update(_load_csv_thresholds_for_stream(path))
    elif suffix in {".xlsx", ".xls"}:
        thresholds.update(_load_excel_thresholds_for_stream(path))

    return Dataset(
        name=name,
        version=version,
        test_cases=[],
        metadata=metadata,
        source_file=str(path),
        thresholds=thresholds,
    )


def _load_json_metadata_for_stream(path: Path) -> tuple[str, str, dict[str, Any], dict[str, float]]:
    """Read lightweight metadata/thresholds from a JSON dataset for streaming mode."""

    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return (path.stem, "stream", {}, {})

    name = payload.get("name", path.stem)
    version = payload.get("version", "stream")

    metadata = payload.get("metadata", {}).copy()
    description = payload.get("description")
    if description and "description" not in metadata:
        metadata["description"] = description

    thresholds: dict[str, float] = {}
    raw_thresholds = payload.get("thresholds") or {}
    for metric, value in raw_thresholds.items():
        try:
            thresholds[metric] = float(value)
        except (TypeError, ValueError):
            continue

    return (name, version, metadata, thresholds)


def _load_csv_thresholds_for_stream(path: Path) -> dict[str, float]:
    """Read thresholds from CSV rows without loading the full dataset."""
    import csv

    encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr", "latin-1"]
    for encoding in encodings:
        try:
            with open(path, encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None:
                    return {}
                return extract_thresholds_from_rows(reader)
        except UnicodeDecodeError:
            continue
        except Exception:
            return {}
    return {}


def _load_excel_thresholds_for_stream(path: Path) -> dict[str, float]:
    """Read thresholds from Excel rows without loading the full dataset."""
    try:
        import pandas as pd

        engine = "xlrd" if path.suffix.lower() == ".xls" else "openpyxl"
        df = pd.read_excel(path, engine=engine, nrows=50)
    except Exception:
        return {}

    return extract_thresholds_from_rows(df.to_dict(orient="records"))


def _resolve_thresholds(
    metrics: list[str],
    dataset: Dataset,
    *,
    profile: str | None = None,
) -> dict[str, float]:
    """Resolve thresholds by preferring dataset values and falling back to defaults."""

    base_thresholds = dataset.thresholds or {}
    resolved: dict[str, float] = {}
    for metric in metrics:
        resolved[metric] = base_thresholds.get(metric, 0.7)
    if profile:
        resolved = apply_threshold_profile(metrics, resolved, profile)
    return resolved


def _merge_evaluation_runs(
    existing: EvaluationRun | None,
    incoming: EvaluationRun,
    *,
    dataset_name: str,
    dataset_version: str,
    metrics: list[str],
    thresholds: dict[str, float],
) -> EvaluationRun:
    """Merge chunk-level evaluation runs into a single aggregate result."""

    if existing is None:
        merged = incoming
    else:
        merged = existing
        merged.results.extend(incoming.results)
        merged.total_tokens = (merged.total_tokens or 0) + (incoming.total_tokens or 0)
        if merged.total_cost_usd is None and incoming.total_cost_usd is None:
            merged.total_cost_usd = None
        else:
            merged.total_cost_usd = (merged.total_cost_usd or 0.0) + (
                incoming.total_cost_usd or 0.0
            )
        merged.finished_at = incoming.finished_at

    merged_preprocess = merge_preprocess_summaries(
        (merged.tracker_metadata or {}).get("dataset_preprocess"),
        (incoming.tracker_metadata or {}).get("dataset_preprocess"),
    )
    if merged_preprocess:
        merged.tracker_metadata["dataset_preprocess"] = merged_preprocess

    merged.dataset_name = dataset_name
    merged.dataset_version = dataset_version
    merged.metrics_evaluated = list(metrics)
    merged.thresholds = dict(thresholds)
    return merged


def _build_streaming_progress_callback(
    on_progress: Callable[[int, int | None, str], None],
    *,
    offset: int,
    total_estimate: int | None,
) -> Callable[[int, int, str], None]:
    def progress_callback(current: int, _total: int, message: str) -> None:
        on_progress(offset + current, total_estimate, message)

    return progress_callback


async def _evaluate_streaming_run(
    dataset_path: Path,
    dataset_template: Dataset,
    metrics: list[str],
    thresholds: dict[str, float],
    evaluator: RagasEvaluator,
    llm: LLMPort,
    chunk_size: int,
    parallel: bool,
    batch_size: int,
    prompt_overrides: dict[str, str] | None = None,
    on_progress: Callable[[int, int | None, str], None] | None = None,
) -> EvaluationRun:
    """Evaluate a dataset in streaming mode, chunk by chunk."""

    config = StreamingConfig(chunk_size=chunk_size)
    loader = StreamingDatasetLoader(config)
    merged_run: EvaluationRun | None = None
    metadata_template = dict(dataset_template.metadata or {})
    threshold_template = dict(dataset_template.thresholds or {})
    source_file = dataset_template.source_file or str(dataset_path)
    processed_total = 0
    progress_callback_wrapper: Callable[[int, int, str], None] | None = None

    iterator = loader.stream(dataset_path)
    estimated_total = iterator.stats.estimated_total_rows
    chunk: list[Any] = []

    for test_case in iterator:
        chunk.append(test_case)
        if len(chunk) < chunk_size:
            continue
        chunk_offset = processed_total
        chunk_dataset = Dataset(
            name=dataset_template.name,
            version=dataset_template.version,
            test_cases=list(chunk),
            metadata=dict(metadata_template),
            source_file=source_file,
            thresholds=dict(threshold_template),
        )
        if iterator.stats.estimated_total_rows is not None:
            estimated_total = iterator.stats.estimated_total_rows
        progress_callback_wrapper = None
        if on_progress:
            progress_callback_wrapper = _build_streaming_progress_callback(
                on_progress,
                offset=chunk_offset,
                total_estimate=estimated_total,
            )

        chunk_run = await evaluator.evaluate(
            dataset=chunk_dataset,
            metrics=metrics,
            llm=llm,
            thresholds=thresholds,
            parallel=parallel,
            batch_size=batch_size,
            prompt_overrides=prompt_overrides,
            on_progress=progress_callback_wrapper,
        )
        merged_run = _merge_evaluation_runs(
            merged_run,
            chunk_run,
            dataset_name=dataset_template.name,
            dataset_version=dataset_template.version,
            metrics=metrics,
            thresholds=thresholds,
        )
        processed_total += len(chunk)
        chunk = []

    if chunk:
        chunk_offset = processed_total
        chunk_dataset = Dataset(
            name=dataset_template.name,
            version=dataset_template.version,
            test_cases=list(chunk),
            metadata=dict(metadata_template),
            source_file=source_file,
            thresholds=dict(threshold_template),
        )
        if iterator.stats.estimated_total_rows is not None:
            estimated_total = iterator.stats.estimated_total_rows
        progress_callback_wrapper = None
        if on_progress:
            progress_callback_wrapper = _build_streaming_progress_callback(
                on_progress,
                offset=chunk_offset,
                total_estimate=estimated_total,
            )

        chunk_run = await evaluator.evaluate(
            dataset=chunk_dataset,
            metrics=metrics,
            llm=llm,
            thresholds=thresholds,
            parallel=parallel,
            batch_size=batch_size,
            prompt_overrides=prompt_overrides,
            on_progress=progress_callback_wrapper,
        )
        merged_run = _merge_evaluation_runs(
            merged_run,
            chunk_run,
            dataset_name=dataset_template.name,
            dataset_version=dataset_template.version,
            metrics=metrics,
            thresholds=thresholds,
        )
        processed_total += len(chunk)

    if merged_run is None:
        empty_dataset = Dataset(
            name=dataset_template.name,
            version=dataset_template.version,
            test_cases=[],
            metadata=dict(metadata_template),
            source_file=source_file,
            thresholds=dict(threshold_template),
        )
        merged_run = await evaluator.evaluate(
            dataset=empty_dataset,
            metrics=metrics,
            llm=llm,
            thresholds=thresholds,
            parallel=parallel,
            batch_size=batch_size,
            prompt_overrides=prompt_overrides,
        )

    merged_run.thresholds = dict(thresholds)
    merged_run.metrics_evaluated = list(metrics)
    merged_run.dataset_name = dataset_template.name
    merged_run.dataset_version = dataset_template.version
    return merged_run


def _collect_prompt_metadata(
    *,
    manifest_path: Path | None,
    prompt_files: list[Path],
    console: Console | None = None,
) -> list[dict[str, Any]]:
    """Read prompt files and summarize manifest differences."""

    if not prompt_files:
        return []

    manifest_data = None
    if manifest_path:
        try:
            manifest_data = load_prompt_manifest(manifest_path)
        except Exception as exc:  # pragma: no cover - guardrail
            if console:
                print_cli_warning(
                    console,
                    f"Prompt manifest를 불러오지 못했습니다: {manifest_path}",
                    tips=[str(exc)],
                )
            manifest_data = None

    summaries: list[dict[str, Any]] = []
    for prompt_file in prompt_files:
        target = prompt_file.expanduser()
        try:
            content = target.read_text(encoding="utf-8")
        except FileNotFoundError:
            normalized = target
            try:
                normalized = target.resolve()
            except FileNotFoundError:
                normalized = target
            summary = PromptDiffSummary(
                path=normalized.as_posix(),
                status="missing_file",
            )
            summaries.append(asdict(summary))
            if console:
                print_cli_warning(
                    console,
                    f"프롬프트 파일을 찾을 수 없습니다: {target}",
                    tips=["경로/파일명을 확인하고 다시 시도하세요."],
                )
            continue

        summary = summarize_prompt_entry(
            manifest_data,
            prompt_path=target,
            content=content,
        )
        summary_dict = asdict(summary)
        summary_dict["content_preview"] = _build_content_preview(content)
        summary_dict["content"] = content
        summaries.append(summary_dict)

    return summaries


def _build_content_preview(content: str, *, max_chars: int = 4000) -> str:
    """Trim prompt content to a safe preview size."""

    if not content:
        return ""
    normalized = content.strip()
    if len(normalized) <= max_chars:
        return normalized
    remaining = len(normalized) - max_chars
    return normalized[:max_chars].rstrip() + f"\n... (+{remaining} chars)"


def _option_was_provided(ctx: typer.Context | click.Context | None, param_name: str) -> bool:
    """Check whether a CLI option was explicitly provided."""

    if ctx is None:
        return False
    try:
        source = ctx.get_parameter_source(param_name)
    except (AttributeError, KeyError):
        return False
    return source == ParameterSource.COMMANDLINE


def _print_run_mode_banner(console: Console, preset: RunModePreset) -> None:
    """Render a short banner describing the selected run mode."""

    bullet_lines: list[str] = []
    if preset.default_metrics:
        bullet_lines.append(f"- Metrics: {', '.join(preset.default_metrics)} (locked)")
    if preset.default_tracker:
        bullet_lines.append(f"- Tracker: {preset.default_tracker}")
    bullet_lines.append(
        "- Domain Memory: enabled" if preset.allow_domain_memory else "- Domain Memory: disabled"
    )
    if not preset.allow_prompt_metadata:
        bullet_lines.append("- Prompt manifest capture: disabled")

    body = preset.description
    if bullet_lines:
        body = f"{preset.description}\n\n" + "\n".join(bullet_lines)

    border_style = "cyan" if preset.name == "simple" else "blue"
    console.print(Panel(body, title=f"Run Mode: {preset.label}", border_style=border_style))
