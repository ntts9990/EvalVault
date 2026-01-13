"""`evalvault run` 명령 전용 Typer 등록 모듈."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable, Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

import click
import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.analysis.pipeline_factory import build_analysis_pipeline_service
from evalvault.adapters.outbound.dataset import get_loader
from evalvault.adapters.outbound.documents.versioned_loader import (
    load_versioned_chunks_from_pdf_dir,
)
from evalvault.adapters.outbound.domain_memory.sqlite_adapter import SQLiteDomainMemoryAdapter
from evalvault.adapters.outbound.llm import SettingsLLMFactory, get_llm_adapter
from evalvault.adapters.outbound.nlp.korean.toolkit_factory import try_create_korean_toolkit
from evalvault.adapters.outbound.phoenix.sync_service import (
    PhoenixDatasetInfo,
    PhoenixSyncError,
    PhoenixSyncService,
    build_experiment_metadata,
)
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.adapters.outbound.tracer.phoenix_tracer_adapter import PhoenixTracerAdapter
from evalvault.config.phoenix_support import ensure_phoenix_instrumentation
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
from evalvault.domain.services.document_versioning import parse_contract_date
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.domain.services.memory_aware_evaluator import MemoryAwareEvaluator
from evalvault.domain.services.memory_based_analysis import MemoryBasedAnalysis
from evalvault.domain.services.prompt_registry import (
    PromptInput,
    build_prompt_bundle,
    build_prompt_inputs_from_snapshots,
    build_prompt_summary,
)
from evalvault.domain.services.ragas_prompt_overrides import (
    PromptOverrideError,
    load_ragas_prompt_overrides,
)
from evalvault.domain.services.retriever_context import apply_versioned_retriever_to_dataset
from evalvault.domain.services.stage_event_builder import StageEventBuilder
from evalvault.ports.outbound.korean_nlp_port import RetrieverPort

from ..utils.analysis_io import (
    build_metric_scorecard,
    build_priority_highlights,
    build_quality_summary,
    extract_markdown_report,
    get_node_output,
    resolve_artifact_dir,
    resolve_output_paths,
    serialize_pipeline_result,
    write_json,
    write_pipeline_artifacts,
)
from ..utils.console import print_cli_error, print_cli_warning, progress_spinner
from ..utils.options import db_option, memory_db_option, profile_option
from ..utils.presets import format_preset_help, get_preset, list_presets
from ..utils.progress import evaluation_progress, streaming_progress
from ..utils.validators import parse_csv_option, validate_choice, validate_choices
from . import run_helpers
from .run_helpers import (
    RUN_MODE_PRESETS,
    _build_streaming_dataset_template,
    _collect_prompt_metadata,
    _display_memory_insights,
    _display_results,
    _evaluate_streaming_run,
    _is_oss_open_model,
    _log_to_tracker,
    _option_was_provided,
    _print_run_mode_banner,
    _resolve_thresholds,
    _save_results,
    _save_to_db,
    _write_stage_events_jsonl,
    enrich_dataset_with_memory,
    format_dataset_preprocess_summary,
    load_knowledge_graph,
    load_retriever_documents,
    log_phoenix_traces,
)

DEFAULT_RUN_MODE = "full"
_merge_evaluation_runs = run_helpers._merge_evaluation_runs
apply_retriever_to_dataset = run_helpers.apply_retriever_to_dataset


def _build_dense_retriever(
    *,
    documents: list[str],
    settings: Settings,
    profile_name: str | None,
) -> Any:
    """Build and index a dense retriever, preferring Ollama embeddings when available."""

    from evalvault.adapters.outbound.nlp.korean.dense_retriever import KoreanDenseRetriever

    embedding_model = settings.ollama_embedding_model
    if settings.llm_provider == "ollama":
        model_info = KoreanDenseRetriever.SUPPORTED_MODELS.get(embedding_model)
        if model_info and model_info.get("type") == "ollama":
            from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter

            ollama_adapter = OllamaAdapter(settings)
            if profile_name in {"dev", "prod"}:
                dense_retriever = KoreanDenseRetriever(
                    profile=profile_name,
                    ollama_adapter=ollama_adapter,
                )
            else:
                dense_retriever = KoreanDenseRetriever(
                    model_name=embedding_model,
                    ollama_adapter=ollama_adapter,
                )
            dense_retriever.index(documents)
            return dense_retriever

    try:
        dense_retriever = KoreanDenseRetriever()
        dense_retriever.index(documents)
        return dense_retriever
    except Exception as exc:
        raise RuntimeError(
            "Dense retriever initialization failed. "
            "Use --profile dev/prod (Ollama embedding), or install/prepare a local embedding model."
        ) from exc


def _log_timestamp(console: Console, verbose: bool, message: str) -> None:
    if not verbose:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"[dim]{timestamp} {message}[/dim]")


def _log_duration(
    console: Console,
    verbose: bool,
    message: str,
    started_at: datetime,
) -> None:
    if not verbose:
        return
    elapsed = (datetime.now() - started_at).total_seconds()
    _log_timestamp(console, verbose, f"{message} ({elapsed:.2f}s)")


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
        evaluation_preset: str | None = typer.Option(
            None,
            "--preset",
            help=(
                "Use a preset configuration (quick/production/summary/comprehensive). "
                f"{format_preset_help()}"
            ),
        ),
        summary: bool = typer.Option(
            False,
            "--summary",
            help=(
                "Enable summarization evaluation preset "
                "(summary_score, summary_faithfulness, entity_preservation)."
            ),
            rich_help_panel="Simple mode preset",
        ),
        metrics: str = typer.Option(
            "faithfulness,answer_relevancy",
            "--metrics",
            "-m",
            help="Comma-separated list of metrics to evaluate. Overrides preset if both are specified.",
            rich_help_panel="Simple mode preset",
        ),
        threshold_profile: str | None = typer.Option(
            None,
            "--threshold-profile",
            help="Apply a threshold profile (summary/qa) to matching metrics.",
            rich_help_panel="Full mode options",
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
        auto_analyze: bool = typer.Option(
            False,
            "--auto-analyze",
            help="평가 완료 후 통합 분석을 자동 실행하고 보고서를 저장합니다.",
        ),
        analysis_output: Path | None = typer.Option(
            None,
            "--analysis-json",
            help="자동 분석 JSON 결과 파일 경로 (기본값: reports/analysis).",
        ),
        analysis_report: Path | None = typer.Option(
            None,
            "--analysis-report",
            help="자동 분석 Markdown 보고서 경로 (기본값: reports/analysis).",
        ),
        analysis_dir: Path | None = typer.Option(
            None,
            "--analysis-dir",
            help="자동 분석 결과 저장 디렉터리 (기본: reports/analysis).",
        ),
        retriever: str | None = typer.Option(
            None,
            "--retriever",
            "-r",
            help="Retriever to fill empty contexts (bm25, dense, hybrid, graphrag).",
            rich_help_panel="Full mode options",
        ),
        retriever_docs: Path | None = typer.Option(
            None,
            "--retriever-docs",
            help="Documents for retriever: .json/.jsonl/.txt file or a PDF directory.",
            rich_help_panel="Full mode options",
        ),
        kg: Path | None = typer.Option(
            None,
            "--kg",
            "-k",
            help="Knowledge graph JSON file for GraphRAG retriever.",
            rich_help_panel="Full mode options",
        ),
        retriever_top_k: int = typer.Option(
            5,
            "--retriever-top-k",
            help="Top-K documents to retrieve (default: 5).",
            rich_help_panel="Full mode options",
        ),
        pdf_ocr: bool = typer.Option(
            False,
            "--pdf-ocr/--no-pdf-ocr",
            help="When --retriever-docs is a PDF directory, run OCR fallback if needed.",
            rich_help_panel="Full mode options",
        ),
        pdf_ocr_backend: str = typer.Option(
            "paddleocr",
            "--pdf-ocr-backend",
            help="OCR backend for PDFs (paddleocr).",
            rich_help_panel="Full mode options",
        ),
        pdf_ocr_mode: str = typer.Option(
            "text",
            "--pdf-ocr-mode",
            help="OCR extraction mode (text|structure).",
            rich_help_panel="Full mode options",
        ),
        pdf_ocr_lang: str = typer.Option(
            "korean",
            "--pdf-ocr-lang",
            help="OCR language code for PaddleOCR (default: korean).",
            rich_help_panel="Full mode options",
        ),
        pdf_ocr_device: str = typer.Option(
            "auto",
            "--pdf-ocr-device",
            help="OCR device selection (auto|cpu|gpu).",
            rich_help_panel="Full mode options",
        ),
        pdf_ocr_min_chars: int = typer.Option(
            200,
            "--pdf-ocr-min-chars",
            help="If extracted text is shorter than this, OCR fallback runs.",
            rich_help_panel="Full mode options",
        ),
        pdf_chunk_size: int = typer.Option(
            1200,
            "--pdf-chunk-size",
            min=200,
            help="Chunk size for PDF directory ingestion.",
            rich_help_panel="Full mode options",
        ),
        pdf_chunk_overlap: int = typer.Option(
            120,
            "--pdf-chunk-overlap",
            min=0,
            help="Chunk overlap for PDF directory ingestion.",
            rich_help_panel="Full mode options",
        ),
        pdf_max_chunks: int | None = typer.Option(
            None,
            "--pdf-max-chunks",
            min=1,
            help="Optional cap on total chunks built from PDFs (speed guardrail).",
            rich_help_panel="Full mode options",
        ),
        stage_events: Path | None = typer.Option(
            None,
            "--stage-events",
            help="Write stage events as JSONL for later ingestion.",
        ),
        stage_store: bool = typer.Option(
            False,
            "--stage-store/--no-stage-store",
            help="Store stage events in the SQLite database (requires --db).",
        ),
        tracker: str = typer.Option(
            "none",
            "--tracker",
            "-t",
            help="Tracker to log results: 'langfuse', 'mlflow', 'phoenix', or 'none'.",
            rich_help_panel="Simple mode preset",
        ),
        langfuse: bool = typer.Option(
            False,
            "--langfuse",
            "-l",
            help="[Deprecated] Use --tracker langfuse instead.",
            hidden=True,
        ),
        phoenix_max_traces: int | None = typer.Option(
            None,
            "--phoenix-max-traces",
            help="Max per-test-case traces to send to Phoenix (default: send all).",
            rich_help_panel="Full mode options",
        ),
        phoenix_dataset: str | None = typer.Option(
            None,
            "--phoenix-dataset",
            help="Upload the dataset/test cases to Phoenix under this name.",
            rich_help_panel="Full mode options",
        ),
        phoenix_dataset_description: str | None = typer.Option(
            None,
            "--phoenix-dataset-description",
            help="Description stored on the Phoenix dataset (default: dataset metadata).",
            rich_help_panel="Full mode options",
        ),
        phoenix_experiment: str | None = typer.Option(
            None,
            "--phoenix-experiment",
            help="Create a Phoenix experiment record for this run (requires dataset upload).",
            rich_help_panel="Full mode options",
        ),
        phoenix_experiment_description: str | None = typer.Option(
            None,
            "--phoenix-experiment-description",
            help="Description stored on the Phoenix experiment.",
            rich_help_panel="Full mode options",
        ),
        prompt_manifest: Path | None = typer.Option(
            Path("agent/prompts/prompt_manifest.json"),
            "--prompt-manifest",
            help="Path to Phoenix prompt manifest JSON.",
            rich_help_panel="Full mode options",
        ),
        prompt_files: str | None = typer.Option(
            None,
            "--prompt-files",
            help="Comma-separated prompt files to capture in Phoenix metadata.",
            rich_help_panel="Full mode options",
        ),
        prompt_set_name: str | None = typer.Option(
            None,
            "--prompt-set-name",
            help="Name for the prompt set snapshot stored in the DB.",
            rich_help_panel="Full mode options",
        ),
        prompt_set_description: str | None = typer.Option(
            None,
            "--prompt-set-description",
            help="Description for the prompt set snapshot.",
            rich_help_panel="Full mode options",
        ),
        system_prompt: str | None = typer.Option(
            None,
            "--system-prompt",
            help="System prompt text for the target LLM (stored for comparison).",
            rich_help_panel="Full mode options",
        ),
        system_prompt_file: Path | None = typer.Option(
            None,
            "--system-prompt-file",
            help="Path to a system prompt file to store alongside this run.",
            rich_help_panel="Full mode options",
        ),
        system_prompt_name: str | None = typer.Option(
            None,
            "--system-prompt-name",
            help="Optional name for the system prompt snapshot.",
            rich_help_panel="Full mode options",
        ),
        ragas_prompts: Path | None = typer.Option(
            None,
            "--ragas-prompts",
            help="YAML file with Ragas metric prompt overrides.",
            rich_help_panel="Full mode options",
        ),
        mode: str = typer.Option(
            DEFAULT_RUN_MODE,
            "--mode",
            help="실행 모드 선택: 'simple'은 간편 실행, 'full'은 모든 옵션 노출.",
            rich_help_panel="Run modes",
        ),
        db_path: Path | None = db_option(
            help_text="Path to SQLite database file for storing results.",
        ),
        use_domain_memory: bool = typer.Option(
            False,
            "--use-domain-memory",
            help="Leverage Domain Memory for threshold adjustment and insights.",
            rich_help_panel="Domain Memory (full mode)",
        ),
        memory_domain: str | None = typer.Option(
            None,
            "--memory-domain",
            help="Domain name for Domain Memory (defaults to dataset metadata).",
            rich_help_panel="Domain Memory (full mode)",
        ),
        memory_language: str = typer.Option(
            "ko",
            "--memory-language",
            help="Language code for Domain Memory lookups (default: ko).",
            rich_help_panel="Domain Memory (full mode)",
        ),
        memory_db: Path | None = memory_db_option(
            help_text="Path to Domain Memory database (default: data/db/evalvault_memory.db).",
        ),
        memory_augment_context: bool = typer.Option(
            False,
            "--augment-context",
            help="Append retrieved factual memories to each test case context.",
            rich_help_panel="Domain Memory (full mode)",
        ),
        verbose: bool = typer.Option(
            False,
            "--verbose",
            "-v",
            help="Show detailed output.",
        ),
        parallel: bool = typer.Option(
            False,
            "--parallel",
            "-P",
            help="Enable parallel evaluation for faster processing.",
        ),
        batch_size: int = typer.Option(
            5,
            "--batch-size",
            "-b",
            help="Batch size for parallel evaluation (default: 5).",
        ),
        stream: bool = typer.Option(
            False,
            "--stream",
            "-s",
            help="Enable streaming evaluation for large datasets (process file in chunks).",
        ),
        stream_chunk_size: int = typer.Option(
            200,
            "--stream-chunk-size",
            help="Chunk size when streaming evaluation is enabled (default: 200).",
        ),
        claim_level: bool = typer.Option(
            False,
            "--claim-level",
            help="Enable claim-level faithfulness analysis for detailed results.",
            rich_help_panel="Full mode options",
        ),
    ) -> None:
        """Run RAG evaluation on a dataset.

        \b
        Run Modes:
          • Simple — Safe defaults (2 metrics + Phoenix tracker + no Domain Memory).
          • Full — Expose all prompt/Domain Memory/streaming options.

        \b
        Presets:
          • quick — Fast iteration with faithfulness metric only.
          • production — Balanced evaluation with 4 core metrics.
          • summary — Summarization evaluation with 3 summary-focused metrics.
          • comprehensive — Complete evaluation with all 6 metrics.

        \b
        Examples:
          # Basic evaluation with default metrics
          evalvault run data.json -m faithfulness

          # Use preset for quick iteration
          evalvault run --preset quick dataset.json

          # Summarization evaluation
          evalvault run --summary dataset.json

          # Production run with JSON output
          evalvault run --preset production dataset.json -o results.json

          # With retriever (auto-fill contexts)
          evalvault run questions.json -r hybrid --retriever-docs docs.json

          # Full mode with Domain Memory
          evalvault run --mode full data.json --use-domain-memory

          # Parallel evaluation for faster processing
          evalvault run data.json -m faithfulness -P -b 10

          # Streaming for large datasets
          evalvault run large.json -m faithfulness --stream

        \b
        See also:
          evalvault metrics     — List available metrics
          evalvault history     — View past evaluation runs
          evalvault analyze     — Analyze run results
          evalvault benchmark   — Run retrieval benchmarks
        """
        try:
            ctx = click.get_current_context()
        except RuntimeError:
            ctx = None
        alias_invoked = ctx.meta.get("run_mode_alias") if ctx else None
        run_mode_value = (mode or DEFAULT_RUN_MODE).lower()
        preset = RUN_MODE_PRESETS.get(run_mode_value)
        if not preset:
            print_cli_error(
                console,
                "--mode 값이 올바르지 않습니다.",
                fixes=[f"사용 가능: {', '.join(sorted(RUN_MODE_PRESETS))}"],
            )
            raise typer.Exit(2)

        if (
            preset.name == "simple"
            or _option_was_provided(ctx, "mode")
            or alias_invoked is not None
        ):
            _print_run_mode_banner(console, preset)

        summary_flag = summary
        if summary_flag and preset.default_metrics:
            print_cli_warning(
                console,
                "Simple 모드에서는 요약 평가 옵션이 적용되지 않습니다.",
                tips=["--mode full로 전환해 요약 메트릭을 사용하세요."],
            )

        if summary_flag and evaluation_preset and evaluation_preset.lower() != "summary":
            print_cli_error(
                console,
                "--summary 옵션은 다른 preset과 함께 사용할 수 없습니다.",
                fixes=["--summary 또는 --preset summary 중 하나만 사용하세요."],
            )
            raise typer.Exit(1)

        if summary_flag and not preset.default_metrics:
            evaluation_preset = evaluation_preset or "summary"

        # Handle evaluation preset
        eval_preset_config = None
        if evaluation_preset:
            eval_preset_config = get_preset(evaluation_preset)
            if not eval_preset_config:
                print_cli_error(
                    console,
                    f"Invalid preset: {evaluation_preset}",
                    fixes=[
                        f"Available presets: {', '.join(list_presets())}",
                        "Run 'evalvault run --help' to see preset descriptions",
                    ],
                )
                raise typer.Exit(1)
            console.print(
                f"[dim]Using preset '{eval_preset_config.name}': {eval_preset_config.description}[/dim]"
            )

        metric_list = parse_csv_option(metrics)
        metrics_override = _option_was_provided(ctx, "metrics")
        if summary_flag and metrics_override:
            print_cli_warning(
                console,
                "--metrics가 지정되어 요약 프리셋 적용을 건너뜁니다.",
                tips=["요약 전용 메트릭을 사용하려면 --metrics 옵션을 제거하세요."],
            )

        # Apply preset metrics if preset is specified and metrics not explicitly overridden
        if eval_preset_config and not metrics_override:
            metric_list = list(eval_preset_config.metrics)
            console.print(f"[dim]Preset metrics: {', '.join(metric_list)}[/dim]")
        if preset.default_metrics:
            preset_metrics = list(preset.default_metrics)
            if metrics_override and set(metric_list) != set(preset_metrics):
                print_cli_warning(
                    console,
                    "Simple 모드는 faithfulness/answer_relevancy를 강제합니다.",
                    tips=["고급 메트릭 구성이 필요하면 --mode full로 실행하세요."],
                )
            metric_list = preset_metrics
        validate_choices(metric_list, available_metrics, console, value_label="metric")

        tracker_override = _option_was_provided(ctx, "tracker") or langfuse
        selected_tracker = tracker
        if preset.default_tracker:
            if tracker_override and tracker != preset.default_tracker:
                print_cli_warning(
                    console,
                    f"Simple 모드는 tracker={preset.default_tracker}로 고정됩니다.",
                    tips=["다른 Tracker를 사용하려면 --mode full을 사용하세요."],
                )
            selected_tracker = preset.default_tracker
        tracker = selected_tracker

        prompt_manifest_value = prompt_manifest
        prompt_files_value = prompt_files
        if not preset.allow_prompt_metadata:
            if prompt_files or _option_was_provided(ctx, "prompt_manifest"):
                print_cli_warning(
                    console,
                    "Simple 모드에서는 Prompt manifest/diff 기능이 비활성화됩니다.",
                    tips=["프롬프트 추적이 필요하면 --mode full을 사용하세요."],
                )
            prompt_manifest_value = None
            prompt_files_value = None

        prompt_manifest_path = prompt_manifest_value.expanduser() if prompt_manifest_value else None
        prompt_file_list = [
            Path(item).expanduser() for item in parse_csv_option(prompt_files_value)
        ]
        prompt_metadata_entries: list[dict[str, Any]] = []
        if prompt_file_list:
            prompt_metadata_entries = _collect_prompt_metadata(
                manifest_path=prompt_manifest_path,
                prompt_files=prompt_file_list,
                console=console,
            )
            if prompt_metadata_entries:
                console.print(
                    "[dim]Collected Phoenix prompt metadata for "
                    f"{len(prompt_metadata_entries)} file(s).[/dim]"
                )
                unsynced = [
                    entry for entry in prompt_metadata_entries if entry.get("status") != "synced"
                ]
                if unsynced:
                    print_cli_warning(
                        console,
                        "Prompt 파일이 manifest와 다릅니다.",
                        tips=["`uv run evalvault phoenix prompt-diff`로 변경 사항을 확인하세요."],
                    )

        if system_prompt and system_prompt_file:
            print_cli_error(
                console,
                "--system-prompt와 --system-prompt-file은 함께 사용할 수 없습니다.",
                fixes=["둘 중 하나만 설정하세요."],
            )
            raise typer.Exit(1)

        prompt_inputs: list[PromptInput] = []
        system_prompt_text: str | None = None
        system_prompt_source: str | None = None
        if system_prompt_file:
            try:
                resolved_prompt_file = system_prompt_file.expanduser()
                system_prompt_text = resolved_prompt_file.read_text(encoding="utf-8")
                system_prompt_source = str(resolved_prompt_file)
            except FileNotFoundError:
                print_cli_error(
                    console,
                    "시스템 프롬프트 파일을 찾을 수 없습니다.",
                    details=str(system_prompt_file),
                )
                raise typer.Exit(1)
        elif system_prompt:
            system_prompt_text = system_prompt
            system_prompt_source = "inline"

        if system_prompt_text:
            prompt_name = system_prompt_name or (
                system_prompt_file.stem if system_prompt_file else "system_prompt"
            )
            prompt_inputs.append(
                PromptInput(
                    content=system_prompt_text,
                    name=prompt_name,
                    kind="system",
                    role="system",
                    source=system_prompt_source,
                )
            )

        ragas_prompt_overrides: dict[str, str] = {}
        ragas_prompt_source: str | None = None
        if ragas_prompts:
            ragas_prompts_path = ragas_prompts.expanduser()
            ragas_prompt_source = str(ragas_prompts_path)
            try:
                ragas_prompt_overrides = load_ragas_prompt_overrides(ragas_prompt_source)
            except PromptOverrideError as exc:
                print_cli_error(
                    console,
                    "Ragas 프롬프트 YAML을 파싱하지 못했습니다.",
                    details=str(exc),
                )
                raise typer.Exit(1)
            except FileNotFoundError:
                print_cli_error(
                    console,
                    "Ragas 프롬프트 YAML 파일을 찾을 수 없습니다.",
                    details=ragas_prompt_source,
                )
                raise typer.Exit(1)

        if ragas_prompt_overrides:
            for metric_name, prompt_text in ragas_prompt_overrides.items():
                if metric_name not in metric_list:
                    print_cli_warning(
                        console,
                        f"Ragas 프롬프트 오버라이드가 선택된 메트릭에 없습니다: {metric_name}",
                        tips=["--metrics에 해당 메트릭을 추가하거나 YAML을 정리하세요."],
                    )
                prompt_inputs.append(
                    PromptInput(
                        content=prompt_text,
                        name=f"ragas.{metric_name}",
                        kind="ragas",
                        role=metric_name,
                        source=ragas_prompt_source,
                    )
                )
        prompt_bundle = None
        if prompt_inputs and not db_path:
            print_cli_warning(
                console,
                "Prompt snapshot은 --db 저장 시에만 DB에 기록됩니다.",
                tips=["--db data/db/evalvault.db 옵션을 추가하세요."],
            )

        if stream_chunk_size <= 0:
            print_cli_error(
                console,
                "--stream-chunk-size 값은 1 이상이어야 합니다.",
                fixes=["예: --stream-chunk-size 200"],
            )
            raise typer.Exit(1)

        domain_memory_requested = (
            use_domain_memory or memory_domain is not None or memory_augment_context
        )
        if not preset.allow_domain_memory and domain_memory_requested:
            print_cli_warning(
                console,
                "Simple 모드에서는 Domain Memory를 사용할 수 없습니다.",
                tips=["--mode full로 전환해 Domain Memory 및 컨텍스트 증강을 활성화하세요."],
            )
            use_domain_memory = False
            memory_domain = None
            memory_augment_context = False
            domain_memory_requested = False

        if stream and domain_memory_requested:
            print_cli_error(
                console,
                "Streaming 모드에서는 Domain Memory 옵션을 사용할 수 없습니다.",
                fixes=["스트리밍을 끄거나 --mode full에서 Domain Memory를 비활성화하세요."],
            )
            raise typer.Exit(1)
        if stream and (phoenix_dataset or phoenix_experiment):
            print_cli_error(
                console,
                "Streaming 모드에서는 Phoenix Dataset/Experiment 업로드가 지원되지 않습니다.",
                fixes=["스트리밍 없이 업로드하거나 Phoenix 업로드 옵션을 제거하세요."],
            )
            raise typer.Exit(1)

        ollama_env_url = os.environ.get("OLLAMA_BASE_URL")
        if ollama_env_url:
            normalized_url = ollama_env_url.strip()
            if normalized_url and "://" not in normalized_url:
                os.environ["OLLAMA_BASE_URL"] = f"http://{normalized_url}"

        settings = Settings()

        # Apply profile (CLI > .env > default)
        profile_name = profile or settings.evalvault_profile
        if profile_name:
            settings = apply_profile(settings, profile_name)

        if db_path is None:
            db_path = Path(settings.evalvault_db_path)

        # Override model if specified
        if model:
            if _is_oss_open_model(model) and settings.llm_provider != "vllm":
                settings.llm_provider = "ollama"
                settings.ollama_model = model
                console.print(
                    "[dim]OSS model detected. Routing request through Ollama backend.[/dim]"
                )
            elif settings.llm_provider == "ollama":
                settings.ollama_model = model
            elif settings.llm_provider == "vllm":
                settings.vllm_model = model
            else:
                settings.openai_model = model

        if settings.llm_provider == "openai" and not settings.openai_api_key:
            print_cli_error(
                console,
                "OPENAI_API_KEY가 설정되지 않았습니다.",
                fixes=[
                    ".env 파일 또는 환경 변수에 OPENAI_API_KEY=... 값을 추가하세요.",
                    "--profile dev 같이 Ollama 기반 프로필을 사용해 로컬 모델을 실행하세요.",
                ],
            )
            raise typer.Exit(1)

        provider = str(getattr(settings, "llm_provider", "")).strip().lower()
        if provider == "ollama":
            try:
                import httpx

                resp = httpx.get(
                    f"{settings.ollama_base_url.rstrip('/')}/api/tags",
                    timeout=httpx.Timeout(5.0, connect=2.0),
                )
                resp.raise_for_status()
                payload = resp.json()
                raw_models = payload.get("models", []) if isinstance(payload, dict) else []
                models = {
                    str(item.get("name"))
                    for item in raw_models
                    if isinstance(item, dict) and item.get("name")
                }

                required_models = {settings.ollama_model, settings.ollama_embedding_model}
                if "faithfulness" in set(metric_list):
                    fallback_provider = (
                        settings.faithfulness_fallback_provider.strip().lower()
                        if settings.faithfulness_fallback_provider
                        else "ollama"
                    )
                    fallback_model = settings.faithfulness_fallback_model
                    if fallback_provider == "ollama" and not fallback_model:
                        fallback_model = "gpt-oss-safeguard:20b"
                    if fallback_provider == "ollama" and fallback_model:
                        required_models.add(fallback_model)

                missing = sorted({m for m in required_models if m and m not in models})
                if missing:
                    print_cli_error(
                        console,
                        "Ollama 모델이 준비되지 않았습니다.",
                        details="missing: " + ", ".join(missing),
                        fixes=[
                            "필요 모델을 받아두세요: "
                            + " ".join(f"`ollama pull {m}`" for m in missing)
                        ],
                    )
                    raise typer.Exit(1)
            except typer.Exit:
                raise
            except Exception as exc:
                print_cli_error(
                    console,
                    "Ollama 서버에 연결할 수 없습니다.",
                    details=str(exc),
                    fixes=[
                        "Ollama가 실행 중인지 확인하세요: `ollama serve` (또는 데스크톱 앱 실행).",
                        "필요 모델을 받아두세요: `ollama pull gpt-oss-safeguard:20b`, `ollama pull qwen3-embedding:0.6b`.",
                        "서버 URL을 바꿨다면 .env의 `OLLAMA_BASE_URL`을 확인하세요.",
                    ],
                )
                raise typer.Exit(1) from exc

        if provider == "vllm":
            try:
                import httpx

                base_url = settings.vllm_base_url.rstrip("/")
                resp = httpx.get(
                    f"{base_url}/models",
                    timeout=httpx.Timeout(5.0, connect=2.0),
                    headers={
                        **(
                            {"Authorization": f"Bearer {settings.vllm_api_key}"}
                            if settings.vllm_api_key
                            else {}
                        )
                    },
                )
                resp.raise_for_status()
            except Exception as exc:
                print_cli_error(
                    console,
                    "vLLM 서버에 연결할 수 없습니다.",
                    details=str(exc),
                    fixes=[
                        "vLLM(OpenAI-compatible) 서버가 실행 중인지 확인하세요.",
                        "`.env`의 `VLLM_BASE_URL`/`VLLM_MODEL` 설정을 확인하세요.",
                    ],
                )
                raise typer.Exit(1) from exc

        if settings.llm_provider == "ollama":
            base_url = getattr(settings, "ollama_base_url", "")
            if not isinstance(base_url, str):
                base_url = ""
            base_url = base_url.strip()
            if not base_url:
                base_url = "http://localhost:11434"
            elif "://" not in base_url:
                base_url = f"http://{base_url}"
            settings.ollama_base_url = base_url
            display_model = f"ollama/{settings.ollama_model}"
        elif settings.llm_provider == "vllm":
            display_model = f"vllm/{settings.vllm_model}"
        else:
            display_model = settings.openai_model

        console.print("\n[bold]EvalVault[/bold] - RAG Evaluation")
        console.print(f"Dataset: [cyan]{dataset}[/cyan]")
        console.print(f"Metrics: [cyan]{', '.join(metric_list)}[/cyan]")
        console.print(f"Provider: [cyan]{settings.llm_provider}[/cyan]")
        console.print(f"Model: [cyan]{display_model}[/cyan]")
        if profile_name:
            console.print(f"Profile: [cyan]{profile_name}[/cyan]")
        console.print()
        _log_timestamp(console, verbose, f"실행 시작 (mode={preset.name})")

        phoenix_trace_metadata: dict[str, Any] = {
            "dataset.path": str(dataset),
            "metrics": metric_list,
            "run_mode": preset.name,
        }
        if threshold_profile:
            phoenix_trace_metadata["threshold.profile"] = str(threshold_profile).strip().lower()

        # Load dataset or configure streaming metadata
        if stream:
            stream_started_at = datetime.now()
            _log_timestamp(
                console,
                verbose,
                f"스트리밍 템플릿 생성 시작 (chunk_size={stream_chunk_size})",
            )
            ds = _build_streaming_dataset_template(dataset)
            _log_duration(console, verbose, "스트리밍 템플릿 생성 완료", stream_started_at)
            console.print(
                f"[dim]Streaming evaluation enabled (chunk size={stream_chunk_size}).[/dim]"
            )
            phoenix_trace_metadata["dataset.stream"] = True
            phoenix_trace_metadata["dataset.template_version"] = ds.version
        else:
            dataset_load_started_at = datetime.now()
            _log_timestamp(console, verbose, f"데이터셋 로딩 시작: {dataset}")
            with progress_spinner(console, "📂 데이터셋 로딩 중...") as update_progress:
                try:
                    loader = get_loader(dataset)
                    ds = loader.load(dataset)
                    update_progress(f"✅ {len(ds)}개 테스트 케이스 로드 완료")
                    _log_duration(console, verbose, "데이터셋 로딩 완료", dataset_load_started_at)
                    phoenix_trace_metadata["dataset.test_cases"] = len(ds)
                    if ds.metadata:
                        for key, value in ds.metadata.items():
                            phoenix_trace_metadata[f"dataset.meta.{key}"] = str(value)
                except Exception as exc:  # pragma: no cover - user feedback path
                    _log_duration(console, verbose, "데이터셋 로딩 실패", dataset_load_started_at)
                    print_cli_error(
                        console,
                        "데이터셋을 불러오지 못했습니다.",
                        details=str(exc),
                        fixes=[
                            "파일 경로와 확장자(csv/json/xlsx)를 확인하세요.",
                            "데이터셋 스키마가 문서와 동일한지 검증하세요.",
                        ],
                    )
                    raise typer.Exit(1) from exc

        if memory_domain:
            ds.metadata["domain"] = memory_domain
            phoenix_trace_metadata["dataset.meta.domain"] = memory_domain

        retriever_instance: RetrieverPort | None = None
        retriever_doc_ids: list[str] | None = None
        prefilled_retriever_metadata: dict[str, dict[str, Any]] = {}
        used_versioned_prefill = False
        versioned_prefill_stats: dict[str, Any] | None = None
        if retriever:
            _log_timestamp(console, verbose, f"Retriever 준비 시작 (mode={retriever})")
            validate_choice(
                retriever,
                ("bm25", "dense", "hybrid", "graphrag"),
                console,
                value_label="retriever",
            )
            if stream:
                print_cli_warning(
                    console,
                    "Streaming 모드에서는 retriever 적용을 건너뜁니다.",
                    tips=["--stream을 끄거나 streaming용 retriever 지원을 기다려주세요."],
                )
            elif not retriever_docs:
                print_cli_warning(
                    console,
                    "Retriever를 사용하려면 문서 파일이 필요합니다.",
                    tips=["--retriever-docs <documents.json> 옵션을 함께 지정하세요."],
                )
            elif retriever == "graphrag" and not kg:
                print_cli_warning(
                    console,
                    "GraphRAG retriever를 사용하려면 KG 파일이 필요합니다.",
                    tips=["--kg <knowledge_graph.json> 옵션을 함께 지정하세요."],
                )
            else:
                if retriever_docs.is_dir():
                    phoenix_trace_metadata["retriever.mode"] = retriever
                    phoenix_trace_metadata["retriever.docs"] = str(retriever_docs)

                    if retriever not in {"bm25", "dense", "hybrid"}:
                        print_cli_warning(
                            console,
                            "버전 PDF 문서는 bm25/dense/hybrid에서만 지원됩니다.",
                            tips=["GraphRAG는 버전 문서 적용을 아직 지원하지 않습니다."],
                        )
                    else:
                        pdf_count = len(list(retriever_docs.glob("*.pdf")))

                        pdf_ocr_backend_value = str(pdf_ocr_backend).strip().lower()
                        pdf_ocr_mode_value = str(pdf_ocr_mode).strip().lower()
                        pdf_ocr_device_value = str(pdf_ocr_device).strip().lower()
                        validate_choice(
                            pdf_ocr_backend_value,
                            ("paddleocr",),
                            console,
                            value_label="pdf_ocr_backend",
                        )
                        validate_choice(
                            pdf_ocr_mode_value,
                            ("text", "structure"),
                            console,
                            value_label="pdf_ocr_mode",
                        )
                        validate_choice(
                            pdf_ocr_device_value,
                            ("auto", "cpu", "gpu"),
                            console,
                            value_label="pdf_ocr_device",
                        )

                        contract_dates: list[date | None] = []
                        for test_case in ds.test_cases:
                            if any(ctx.strip() for ctx in test_case.contexts):
                                continue
                            contract = None
                            if isinstance(test_case.metadata, dict):
                                contract = parse_contract_date(
                                    test_case.metadata.get("contract_date")
                                )
                            contract_dates.append(contract)

                        retriever_docs_started_at = datetime.now()
                        try:
                            versioned_chunks = load_versioned_chunks_from_pdf_dir(
                                retriever_docs,
                                chunk_size=pdf_chunk_size,
                                overlap=pdf_chunk_overlap,
                                enable_ocr=pdf_ocr,
                                ocr_backend=pdf_ocr_backend_value,
                                ocr_lang=pdf_ocr_lang,
                                ocr_device=pdf_ocr_device_value,
                                ocr_mode=pdf_ocr_mode_value,
                                ocr_min_chars=pdf_ocr_min_chars,
                                contract_dates=contract_dates,
                                max_chunks=pdf_max_chunks,
                            )
                            _log_duration(
                                console,
                                verbose,
                                f"버전 PDF 문서 로드 완료 (chunks={len(versioned_chunks)})",
                                retriever_docs_started_at,
                            )
                        except Exception as exc:
                            _log_duration(
                                console,
                                verbose,
                                "버전 PDF 문서 로드 실패",
                                retriever_docs_started_at,
                            )
                            print_cli_error(
                                console,
                                "버전 PDF 문서를 불러오지 못했습니다.",
                                details=str(exc),
                                fixes=[
                                    "스캔 PDF(텍스트 레이어 없음)라면 --pdf-ocr를 켜세요.",
                                    "OCR 사용 시: `uv sync --extra ocr_paddle`로 의존성을 설치하고 paddlepaddle wheel이 필요합니다.",
                                    "OCR 없이 진행하려면 --no-pdf-ocr로 실행하세요.",
                                    "PDF 파일명에 적용일(YYYYMMDD/YYMMDD 등)이 포함되어야 합니다.",
                                ],
                            )
                            raise typer.Exit(1) from exc

                        apply_started_at = datetime.now()
                        try:
                            if retriever in {"bm25", "hybrid"}:
                                from evalvault.adapters.outbound.nlp.korean import KoreanNLPToolkit

                                toolkit = KoreanNLPToolkit()

                                def build_versioned_retriever(docs: Sequence[str]) -> RetrieverPort:
                                    instance = toolkit.build_retriever(
                                        list(docs),
                                        use_hybrid=retriever == "hybrid",
                                        verbose=verbose,
                                    )
                                    if instance is None:
                                        raise RuntimeError("Retriever initialization failed")
                                    return instance

                            else:

                                def build_versioned_retriever(docs: Sequence[str]) -> RetrieverPort:
                                    return _build_dense_retriever(
                                        documents=list(docs),
                                        settings=settings,
                                        profile_name=profile_name,
                                    )

                            prefilled_retriever_metadata = apply_versioned_retriever_to_dataset(
                                dataset=ds,
                                versioned_chunks=versioned_chunks,
                                build_retriever=build_versioned_retriever,
                                top_k=retriever_top_k,
                            )
                            used_versioned_prefill = True

                            filled_case_ids = set(prefilled_retriever_metadata)
                            parsed_contract_dates = set()
                            unknown_contract_dates = 0
                            for test_case in ds.test_cases:
                                if test_case.id not in filled_case_ids:
                                    continue
                                contract = None
                                if isinstance(test_case.metadata, dict):
                                    contract = parse_contract_date(
                                        test_case.metadata.get("contract_date")
                                    )
                                if contract is None:
                                    unknown_contract_dates += 1
                                else:
                                    parsed_contract_dates.add(contract)

                            versioned_prefill_stats = {
                                "pdf_files": pdf_count,
                                "chunks": len(versioned_chunks),
                                "filled_test_cases": len(filled_case_ids),
                                "contract_dates": len(parsed_contract_dates),
                                "unknown_contract_dates": unknown_contract_dates,
                            }
                            phoenix_trace_metadata["retriever.versioned_docs"] = True
                            phoenix_trace_metadata["retriever.versioned.pdf_files"] = pdf_count
                            phoenix_trace_metadata["retriever.versioned.chunks"] = len(
                                versioned_chunks
                            )
                            phoenix_trace_metadata["retriever.versioned.contract_dates"] = len(
                                parsed_contract_dates
                            )

                            message = (
                                "Versioned PDF prefill: "
                                f"pdfs={pdf_count}, chunks={len(versioned_chunks)}, "
                                f"filled={len(filled_case_ids)}, contract_dates={len(parsed_contract_dates)}"
                            )
                            if pdf_ocr:
                                message += f", ocr={pdf_ocr_backend_value}/{pdf_ocr_mode_value}/{pdf_ocr_device_value}"
                            if verbose and unknown_contract_dates:
                                message += f", unknown_contract_dates={unknown_contract_dates}"
                            console.print(f"[dim]{message}[/dim]")

                            _log_duration(
                                console,
                                verbose,
                                "버전 PDF retriever 적용 완료",
                                apply_started_at,
                            )
                        except Exception as exc:
                            _log_duration(
                                console,
                                verbose,
                                "버전 PDF retriever 적용 실패",
                                apply_started_at,
                            )
                            print_cli_error(
                                console,
                                "버전 PDF retriever 적용에 실패했습니다.",
                                details=str(exc),
                                fixes=[
                                    "--verbose로 원인을 확인하세요.",
                                    "dense/hybrid는 임베딩 모델이 필요합니다. 기본은 `--profile dev`(Ollama + qwen3-embedding)입니다.",
                                    "Ollama 사용 시 `ollama pull qwen3-embedding:0.6b` 후 다시 실행하세요.",
                                ],
                            )
                            raise typer.Exit(1) from exc
                else:
                    documents: list[str] = []
                    doc_ids: list[str] = []
                    retriever_docs_started_at = datetime.now()
                    try:
                        documents, doc_ids = load_retriever_documents(retriever_docs)
                        retriever_doc_ids = doc_ids
                        _log_duration(
                            console,
                            verbose,
                            f"Retriever 문서 로드 완료 (count={len(documents)})",
                            retriever_docs_started_at,
                        )
                    except Exception as exc:
                        _log_duration(
                            console,
                            verbose,
                            "Retriever 문서 로드 실패",
                            retriever_docs_started_at,
                        )
                        print_cli_error(
                            console,
                            "Retriever 문서를 불러오지 못했습니다.",
                            details=str(exc),
                            fixes=["JSON/JSONL/TXT 형식을 확인하세요."],
                        )
                        raise typer.Exit(1) from exc

                    retriever_init_started_at = datetime.now()
                    try:
                        if retriever == "graphrag":
                            from evalvault.adapters.outbound.kg.graph_rag_retriever import (
                                GraphRAGRetriever,
                            )

                            if kg is None:
                                print_cli_error(
                                    console,
                                    "GraphRAG retriever를 사용하려면 KG 파일이 필요합니다.",
                                    fixes=["--kg <knowledge_graph.json> 옵션을 함께 지정하세요."],
                                )
                                raise typer.Exit(1)
                            kg_path = kg

                            try:
                                kg_graph = load_knowledge_graph(kg_path)
                            except Exception as exc:
                                print_cli_error(
                                    console,
                                    "Knowledge Graph 파일을 불러오지 못했습니다.",
                                    details=str(exc),
                                    fixes=["KG JSON 스키마와 경로를 확인하세요."],
                                )
                                raise typer.Exit(1) from exc

                            bm25_retriever = None
                            try:
                                from evalvault.adapters.outbound.nlp.korean import KoreanNLPToolkit

                                toolkit = KoreanNLPToolkit()
                                bm25_retriever = toolkit.build_retriever(
                                    documents,
                                    use_hybrid=False,
                                    verbose=verbose,
                                )
                            except Exception as exc:  # pragma: no cover - optional dependency
                                print_cli_warning(
                                    console,
                                    "GraphRAG용 BM25 retriever 초기화에 실패했습니다.",
                                    tips=[str(exc)],
                                )

                            dense_retriever = None
                            try:
                                dense_retriever = _build_dense_retriever(
                                    documents=documents,
                                    settings=settings,
                                    profile_name=profile_name,
                                )
                            except Exception as exc:  # pragma: no cover - optional dependency
                                print_cli_warning(
                                    console,
                                    "GraphRAG용 Dense retriever 초기화에 실패했습니다.",
                                    tips=[str(exc)],
                                )

                            kg_doc_ids = {
                                str(entity.source_document_id)
                                for entity in kg_graph.get_all_entities()
                                if entity.source_document_id
                            }
                            if kg_doc_ids and not (kg_doc_ids & set(doc_ids)):
                                preview = ", ".join(sorted(kg_doc_ids)[:3])
                                print_cli_warning(
                                    console,
                                    "KG의 doc_id가 문서 doc_id와 매칭되지 않습니다.",
                                    tips=[
                                        "문서 파일의 doc_id를 KG source_document_id와 동일하게 지정하세요.",
                                        f"예시 KG doc_id: {preview}",
                                    ],
                                )

                            retriever_instance = GraphRAGRetriever(
                                kg_graph,
                                bm25_retriever=bm25_retriever,
                                dense_retriever=dense_retriever,
                                documents=documents,
                                document_ids=doc_ids,
                            )
                        elif retriever == "dense":
                            retriever_instance = _build_dense_retriever(
                                documents=documents,
                                settings=settings,
                                profile_name=profile_name,
                            )
                        else:
                            from evalvault.adapters.outbound.nlp.korean import KoreanNLPToolkit

                            toolkit = KoreanNLPToolkit()
                            retriever_instance = toolkit.build_retriever(
                                documents,
                                use_hybrid=retriever == "hybrid",
                                verbose=verbose,
                            )
                        if retriever_instance:
                            _log_duration(
                                console,
                                verbose,
                                "Retriever 초기화 완료",
                                retriever_init_started_at,
                            )
                        else:
                            _log_duration(
                                console,
                                verbose,
                                "Retriever 초기화 실패",
                                retriever_init_started_at,
                            )
                    except Exception as exc:  # pragma: no cover - dependency/IO issues
                        _log_duration(
                            console,
                            verbose,
                            "Retriever 초기화 실패",
                            retriever_init_started_at,
                        )
                        print_cli_warning(
                            console,
                            "Retriever 초기화에 실패했습니다.",
                            tips=[str(exc)],
                        )
                        retriever_instance = None

                    if retriever_instance:
                        phoenix_trace_metadata["retriever.mode"] = retriever
                        phoenix_trace_metadata["retriever.docs"] = str(retriever_docs)
                        if retriever == "graphrag" and kg:
                            phoenix_trace_metadata["retriever.kg"] = str(kg)

        try:
            resolved_thresholds = _resolve_thresholds(
                metric_list,
                ds,
                profile=threshold_profile,
            )
        except ValueError as exc:
            print_cli_error(
                console,
                "Threshold profile 값이 올바르지 않습니다.",
                details=str(exc),
                fixes=["--threshold-profile summary|qa 중 하나를 선택하세요."],
            )
            raise typer.Exit(2) from exc

        phoenix_dataset_name = phoenix_dataset
        if phoenix_experiment and not phoenix_dataset_name:
            phoenix_dataset_name = f"{ds.name}:{ds.version}"

        phoenix_dataset_description_value = phoenix_dataset_description
        if phoenix_dataset_name and not phoenix_dataset_description_value:
            desc_source = ds.metadata.get("description") if isinstance(ds.metadata, dict) else None
            phoenix_dataset_description_value = desc_source or f"{ds.name} v{ds.version}"

        phoenix_sync_service: PhoenixSyncService | None = None
        phoenix_dataset_result: dict[str, Any] | None = None
        phoenix_experiment_result: dict[str, Any] | None = None

        if phoenix_dataset_name or phoenix_experiment:
            try:
                phoenix_sync_service = PhoenixSyncService(
                    endpoint=settings.phoenix_endpoint,
                    api_token=getattr(settings, "phoenix_api_token", None),
                )
            except PhoenixSyncError as exc:
                print_cli_warning(
                    console,
                    "Phoenix Sync 서비스를 초기화할 수 없습니다.",
                    tips=[str(exc)],
                )
                phoenix_sync_service = None

        effective_tracker = tracker
        if langfuse and tracker == "none" and not preset.default_tracker:
            effective_tracker = "langfuse"
            print_cli_warning(
                console,
                "--langfuse 플래그는 곧 제거됩니다.",
                tips=["대신 --tracker langfuse를 사용하세요."],
            )

        config_wants_phoenix = getattr(settings, "phoenix_enabled", False)
        if not isinstance(config_wants_phoenix, bool):
            config_wants_phoenix = False
        should_enable_phoenix = effective_tracker == "phoenix" or config_wants_phoenix
        if should_enable_phoenix:
            ensure_phoenix_instrumentation(settings, console=console, force=True)

        llm_factory = SettingsLLMFactory(settings)
        korean_toolkit = try_create_korean_toolkit()
        evaluator = RagasEvaluator(korean_toolkit=korean_toolkit, llm_factory=llm_factory)
        llm_adapter = None
        try:
            llm_adapter = get_llm_adapter(settings)
        except Exception as exc:
            provider = str(getattr(settings, "llm_provider", "")).strip().lower()
            recovered = False
            if provider == "ollama" and "http://" in str(exc):
                base_url = getattr(settings, "ollama_base_url", "")
                if not isinstance(base_url, str) or not base_url.strip():
                    base_url = "http://localhost:11434"
                elif "://" not in base_url:
                    base_url = f"http://{base_url.strip()}"
                settings.ollama_base_url = base_url
                try:
                    llm_adapter = get_llm_adapter(settings)
                    recovered = True
                except Exception as retry_exc:
                    exc = retry_exc

            if not recovered:
                fixes: list[str] = []
                if provider == "ollama":
                    fixes = [
                        "Ollama 서버가 실행 중인지 확인하세요 (기본: http://localhost:11434).",
                        "필요 모델을 받아두세요: `ollama pull gpt-oss-safeguard:20b` 및 `ollama pull qwen3-embedding:0.6b`.",
                        "URL을 바꿨다면 .env의 `OLLAMA_BASE_URL`을 확인하세요.",
                    ]
                elif provider == "openai":
                    fixes = [
                        "`.env`에 `OPENAI_API_KEY`를 설정하세요.",
                        "프록시/네트워크가 필요한 환경이면 연결 가능 여부를 확인하세요.",
                    ]
                elif provider == "vllm":
                    fixes = [
                        "`.env`의 `VLLM_BASE_URL`/`VLLM_MODEL` 설정을 확인하세요.",
                        "vLLM 서버가 OpenAI 호환 API로 실행 중인지 확인하세요.",
                    ]
                else:
                    fixes = ["--profile 또는 환경변수 설정을 확인하세요."]

                print_cli_error(
                    console,
                    "LLM/임베딩 어댑터를 초기화하지 못했습니다.",
                    details=str(exc),
                    fixes=fixes,
                )
                raise typer.Exit(1) from exc

        assert llm_adapter is not None

        memory_adapter: SQLiteDomainMemoryAdapter | None = None
        memory_evaluator: MemoryAwareEvaluator | None = None
        memory_domain_name = memory_domain or ds.metadata.get("domain") or "default"
        memory_required = domain_memory_requested
        reliability_snapshot: dict[str, float] | None = None

        if memory_required:
            phoenix_trace_metadata["domain_memory.enabled"] = True
            phoenix_trace_metadata["domain_memory.domain"] = memory_domain_name
            phoenix_trace_metadata["domain_memory.language"] = memory_language
            phoenix_trace_metadata["domain_memory.augment_context"] = memory_augment_context
        else:
            phoenix_trace_metadata["domain_memory.enabled"] = False

        if memory_required:
            memory_started_at = datetime.now()
            _log_timestamp(
                console,
                verbose,
                f"Domain Memory 초기화 시작 (domain={memory_domain_name}, lang={memory_language})",
            )
            try:
                memory_db_path = memory_db or settings.evalvault_memory_db_path
                memory_adapter = SQLiteDomainMemoryAdapter(memory_db_path)
                memory_evaluator = MemoryAwareEvaluator(
                    evaluator=evaluator,
                    memory_port=memory_adapter,
                    tracer=PhoenixTracerAdapter(),
                )
                console.print(
                    "[dim]Domain Memory enabled for "
                    f"'{memory_domain_name}' ({memory_language}).[/dim]"
                )
                if memory_adapter:
                    reliability = memory_adapter.get_aggregated_reliability(
                        domain=memory_domain_name,
                        language=memory_language,
                    )
                    reliability_snapshot = reliability
                    if reliability:
                        console.print(
                            "[dim]Reliability snapshot:[/dim] "
                            + ", ".join(f"{k}={v:.2f}" for k, v in reliability.items())
                        )
                        phoenix_trace_metadata["domain_memory.reliability"] = reliability
                _log_duration(console, verbose, "Domain Memory 초기화 완료", memory_started_at)
            except Exception as exc:  # pragma: no cover - best-effort memory hookup
                _log_duration(console, verbose, "Domain Memory 초기화 실패", memory_started_at)
                print_cli_warning(
                    console,
                    "Domain Memory 초기화에 실패했습니다.",
                    tips=[str(exc)],
                )
                memory_evaluator = None
                memory_adapter = None

        if memory_evaluator and memory_augment_context:
            memory_enrich_started_at = datetime.now()
            _log_timestamp(console, verbose, "Domain Memory 컨텍스트 보강 시작")
            enriched = enrich_dataset_with_memory(
                dataset=ds,
                memory_evaluator=memory_evaluator,
                domain=memory_domain_name,
                language=memory_language,
            )
            enriched_count = enriched or 0
            _log_duration(
                console,
                verbose,
                f"Domain Memory 컨텍스트 보강 완료 (count={enriched_count})",
                memory_enrich_started_at,
            )
            if enriched:
                console.print(
                    f"[dim]Appended Domain Memory facts to {enriched} test case(s).[/dim]"
                )

        if resolved_thresholds:
            if ds.thresholds and not threshold_profile:
                console.print("[dim]Thresholds from dataset:[/dim]")
                thresholds_to_show = ds.thresholds
            else:
                console.print("[dim]Thresholds in use:[/dim]")
                thresholds_to_show = resolved_thresholds
            for metric, threshold in thresholds_to_show.items():
                console.print(f"  [dim]{metric}: {threshold}[/dim]")
            console.print()

        # Apply preset parallelization settings if not explicitly overridden
        final_parallel = parallel
        final_batch_size = batch_size
        if eval_preset_config:
            if not _option_was_provided(ctx, "parallel"):
                final_parallel = eval_preset_config.parallel
            if not _option_was_provided(ctx, "batch_size"):
                final_batch_size = eval_preset_config.batch_size
            if final_parallel != parallel or final_batch_size != batch_size:
                console.print(
                    f"[dim]Preset parallelization: parallel={final_parallel}, batch_size={final_batch_size}[/dim]"
                )

        if stream:
            status_msg = f"📡 Streaming evaluation (chunk_size={stream_chunk_size})"
        elif final_parallel:
            status_msg = f"⚡ Parallel evaluation (batch_size={final_batch_size})"
        else:
            status_msg = "🤖 Evaluation in progress"
        evaluation_started_at = datetime.now()
        if stream:
            eval_mode_label = f"stream(chunk_size={stream_chunk_size})"
            _log_timestamp(
                console,
                verbose,
                f"평가 시작 (mode={eval_mode_label}, metrics={', '.join(metric_list)})",
            )
        else:
            eval_mode_label = (
                f"parallel(batch_size={final_batch_size})" if final_parallel else "sequential"
            )
            _log_timestamp(
                console,
                verbose,
                "평가 시작 "
                f"(mode={eval_mode_label}, cases={len(ds)}, metrics={', '.join(metric_list)})",
            )
        if stream:
            with streaming_progress(console, description=status_msg) as update_progress:
                stream_update = cast(Callable[[int, int | None, str | None], None], update_progress)
                try:
                    result = asyncio.run(
                        _evaluate_streaming_run(
                            dataset_path=dataset,
                            dataset_template=ds,
                            metrics=metric_list,
                            thresholds=resolved_thresholds,
                            evaluator=evaluator,
                            llm=llm_adapter,
                            chunk_size=stream_chunk_size,
                            parallel=final_parallel,
                            batch_size=final_batch_size,
                            prompt_overrides=ragas_prompt_overrides or None,
                            on_progress=lambda c, t, msg: stream_update(c, t, msg),
                        )
                    )
                    _log_duration(console, verbose, "평가 완료", evaluation_started_at)
                except Exception as exc:  # pragma: no cover - surfaced to CLI
                    _log_duration(console, verbose, "평가 실패", evaluation_started_at)
                    print_cli_error(
                        console,
                        "평가 실행 중 오류가 발생했습니다.",
                        details=str(exc),
                        fixes=[
                            "LLM API 키/쿼터 상태와 dataset 스키마를 확인하세요.",
                            "추가 로그는 --verbose 옵션으로 확인할 수 있습니다.",
                        ],
                    )
                    raise typer.Exit(1) from exc
        else:
            with evaluation_progress(console, len(ds), description=status_msg) as update_progress:
                eval_update = cast(Callable[[int, str | None], None], update_progress)
                try:
                    if memory_evaluator and use_domain_memory:
                        eval_update(0, "🔁 Domain Memory와 병렬로 실행 중...")
                        result = asyncio.run(
                            memory_evaluator.evaluate_with_memory(
                                dataset=ds,
                                metrics=metric_list,
                                llm=llm_adapter,
                                thresholds=resolved_thresholds,
                                parallel=final_parallel,
                                batch_size=final_batch_size,
                                domain=memory_domain_name,
                                language=memory_language,
                                retriever=retriever_instance,
                                retriever_top_k=retriever_top_k,
                                retriever_doc_ids=retriever_doc_ids,
                                prompt_overrides=ragas_prompt_overrides or None,
                                on_progress=lambda c, _t, msg: eval_update(c, msg),
                                claim_level=claim_level,
                            )
                        )
                    else:
                        result = asyncio.run(
                            evaluator.evaluate(
                                dataset=ds,
                                metrics=metric_list,
                                llm=llm_adapter,
                                thresholds=resolved_thresholds,
                                parallel=final_parallel,
                                batch_size=final_batch_size,
                                retriever=retriever_instance,
                                retriever_top_k=retriever_top_k,
                                retriever_doc_ids=retriever_doc_ids,
                                prompt_overrides=ragas_prompt_overrides or None,
                                on_progress=lambda c, _t, msg: eval_update(c, msg),
                                claim_level=claim_level,
                            )
                        )
                    _log_duration(console, verbose, "평가 완료", evaluation_started_at)
                except Exception as exc:  # pragma: no cover - surfaced to CLI
                    _log_duration(console, verbose, "평가 실패", evaluation_started_at)
                    print_cli_error(
                        console,
                        "평가 실행 중 오류가 발생했습니다.",
                        details=str(exc),
                        fixes=[
                            "LLM API 키/쿼터 상태와 dataset 스키마를 확인하세요.",
                            "추가 로그는 --verbose 옵션으로 확인할 수 있습니다.",
                        ],
                    )
                    raise typer.Exit(1) from exc

        phoenix_trace_metadata["dataset.test_cases"] = result.total_test_cases

        if prefilled_retriever_metadata:
            merged_retriever_metadata = dict(result.retrieval_metadata or {})
            merged_retriever_metadata.update(prefilled_retriever_metadata)
            result.retrieval_metadata = merged_retriever_metadata

        result.tracker_metadata.setdefault("run_mode", preset.name)
        tracker_meta = result.tracker_metadata or {}
        result.tracker_metadata = tracker_meta
        ragas_snapshots = tracker_meta.get("ragas_prompt_snapshots")
        ragas_snapshot_inputs = build_prompt_inputs_from_snapshots(
            ragas_snapshots if isinstance(ragas_snapshots, dict) else None,
        )
        override_status: dict[str, str] = {}
        raw_override = tracker_meta.get("ragas_prompt_overrides")
        if isinstance(raw_override, dict):
            override_status = cast(dict[str, str], raw_override)
        if override_status:
            prompt_inputs = [
                entry
                for entry in prompt_inputs
                if not (
                    entry.kind == "ragas"
                    and override_status.get(entry.role) is not None
                    and override_status.get(entry.role) != "applied"
                )
            ]

        if ragas_snapshot_inputs:
            existing_roles = {entry.role for entry in prompt_inputs if entry.kind == "ragas"}
            for entry in ragas_snapshot_inputs:
                if entry.role in existing_roles and override_status.get(entry.role) == "applied":
                    continue
                prompt_inputs.append(entry)
        if prompt_inputs and not db_path:
            print_cli_warning(
                console,
                "Prompt snapshot은 --db 저장 시에만 DB에 기록됩니다.",
                tips=["--db data/db/evalvault.db 옵션을 추가하세요."],
            )

        if prompt_inputs:
            prompt_bundle = build_prompt_bundle(
                run_id=result.run_id,
                prompt_set_name=prompt_set_name,
                prompt_set_description=prompt_set_description,
                prompt_inputs=prompt_inputs,
                metadata={
                    "run_id": result.run_id,
                    "dataset": result.dataset_name,
                    "model": result.model_name,
                    "metrics": metric_list,
                },
            )
            if prompt_bundle:
                result.tracker_metadata["prompt_set"] = build_prompt_summary(prompt_bundle)

        if retriever_instance or used_versioned_prefill:
            retriever_tracker_meta: dict[str, Any] = {
                "mode": retriever,
                "docs_path": str(retriever_docs) if retriever_docs else None,
                "top_k": retriever_top_k,
                "versioned_docs": used_versioned_prefill,
            }
            if versioned_prefill_stats:
                retriever_tracker_meta["versioned_docs_stats"] = versioned_prefill_stats
            result.tracker_metadata["retriever"] = retriever_tracker_meta
        if memory_required:
            result.tracker_metadata["domain_memory"] = {
                "enabled": memory_required,
                "domain": memory_domain_name,
                "language": memory_language,
                "augment_context": memory_augment_context,
            }

        preprocess_summary = format_dataset_preprocess_summary(
            result.tracker_metadata.get("dataset_preprocess")
        )
        if preprocess_summary:
            console.print(f"[dim]{preprocess_summary}[/dim]")

        retriever_metadata: dict[str, dict[str, Any]] | None = result.retrieval_metadata or None
        if (retriever_instance or used_versioned_prefill) and retriever_metadata:
            console.print(
                f"[dim]Applied {retriever} retriever to "
                f"{len(retriever_metadata)} test case(s).[/dim]"
            )

        _display_results(result, console, verbose)

        if threshold_profile:
            result.tracker_metadata["threshold_profile"] = str(threshold_profile).strip().lower()

        if memory_adapter and memory_required:
            analyzer = MemoryBasedAnalysis(memory_port=memory_adapter)
            insights = analyzer.generate_insights(
                evaluation_run=result,
                domain=memory_domain_name,
                language=memory_language,
            )
            _display_memory_insights(insights, console)

        if phoenix_sync_service:
            phoenix_meta = result.tracker_metadata.setdefault("phoenix", {})
            phoenix_meta.setdefault("schema_version", 2)
            if phoenix_dataset_name:
                try:
                    dataset_info = phoenix_sync_service.upload_dataset(
                        dataset=ds,
                        dataset_name=phoenix_dataset_name,
                        description=phoenix_dataset_description_value,
                    )
                    phoenix_dataset_result = dataset_info.to_dict()
                    phoenix_meta["dataset"] = phoenix_dataset_result
                    phoenix_trace_metadata["phoenix.dataset_id"] = dataset_info.dataset_id
                    phoenix_meta["embedding_export"] = {
                        "dataset_id": dataset_info.dataset_id,
                        "cli": (
                            "uv run evalvault phoenix export-embeddings "
                            f"--dataset {dataset_info.dataset_id}"
                        ),
                        "endpoint": getattr(settings, "phoenix_endpoint", None),
                    }
                    console.print(
                        "[green]Uploaded dataset to Phoenix:[/green] "
                        f"{dataset_info.dataset_name} ({dataset_info.dataset_id})"
                    )
                    console.print(f"[dim]View datasets: {dataset_info.url}[/dim]")
                except PhoenixSyncError as exc:
                    print_cli_warning(
                        console,
                        "Phoenix Dataset 업로드에 실패했습니다.",
                        tips=[str(exc)],
                    )
            if phoenix_experiment:
                if not phoenix_dataset_result:
                    print_cli_warning(
                        console,
                        "Dataset 업로드에 실패해 Phoenix Experiment 생성을 건너뜁니다.",
                        tips=["`--phoenix-dataset` 업로드가 성공한 뒤 실험을 생성하세요."],
                    )
                else:
                    experiment_name = (
                        phoenix_experiment or f"{result.model_name}-{result.run_id[:8]}"
                    )
                    experiment_description = (
                        phoenix_experiment_description
                        or f"EvalVault run {result.run_id} ({result.model_name})"
                    )
                    extra_meta = {
                        "domain_memory": {
                            "enabled": memory_required,
                            "domain": memory_domain_name,
                            "language": memory_language,
                        }
                    }
                    experiment_metadata = build_experiment_metadata(
                        run=result,
                        dataset=ds,
                        reliability_snapshot=reliability_snapshot,
                        extra=extra_meta,
                    )
                    try:
                        dataset_info_obj = PhoenixDatasetInfo(
                            dataset_id=phoenix_dataset_result["dataset_id"],
                            dataset_name=phoenix_dataset_result["dataset_name"],
                            dataset_version_id=phoenix_dataset_result["dataset_version_id"],
                            url=phoenix_dataset_result["url"],
                        )
                        exp_info = phoenix_sync_service.create_experiment_record(
                            dataset_info=dataset_info_obj,
                            experiment_name=experiment_name,
                            description=experiment_description,
                            metadata=experiment_metadata,
                        )
                        phoenix_experiment_result = exp_info.to_dict()
                        phoenix_meta["experiment"] = phoenix_experiment_result
                        console.print(
                            "[green]Created Phoenix experiment:[/green] "
                            f"{experiment_name} ({exp_info.experiment_id})"
                        )
                        console.print(f"[dim]View experiment: {exp_info.url}[/dim]")
                    except PhoenixSyncError as exc:
                        print_cli_warning(
                            console,
                            "Phoenix Experiment 생성에 실패했습니다.",
                            tips=[str(exc)],
                        )

        if prompt_metadata_entries:
            phoenix_meta = result.tracker_metadata.setdefault("phoenix", {})
            phoenix_meta.setdefault("schema_version", 2)
            phoenix_meta["prompts"] = prompt_metadata_entries

        if stage_events or stage_store:
            stage_event_builder = StageEventBuilder()
            stage_event_payload = stage_event_builder.build_for_run(
                result,
                prompt_metadata=prompt_metadata_entries or None,
                retrieval_metadata=retriever_metadata,
            )
            if stage_events:
                stored = _write_stage_events_jsonl(stage_events, stage_event_payload)
                console.print(f"[green]Saved {stored} stage event(s).[/green]")
            if stage_store:
                if db_path:
                    storage = SQLiteStorageAdapter(db_path=db_path)
                    stored = storage.save_stage_events(stage_event_payload)
                    console.print(f"[green]Stored {stored} stage event(s).[/green]")
                else:
                    print_cli_warning(
                        console,
                        "Stage 이벤트를 저장하려면 --db 경로가 필요합니다.",
                        tips=["--db <sqlite_path> 옵션을 함께 지정하세요."],
                    )

        if effective_tracker != "none":
            phoenix_opts = None
            if effective_tracker == "phoenix":
                phoenix_opts = {
                    "max_traces": phoenix_max_traces,
                    "metadata": phoenix_trace_metadata or None,
                }
            tracker_started_at = datetime.now()
            _log_timestamp(
                console,
                verbose,
                f"Tracker 로깅 시작 ({effective_tracker})",
            )
            _log_to_tracker(
                settings,
                result,
                console,
                effective_tracker,
                phoenix_options=phoenix_opts,
                log_phoenix_traces_fn=log_phoenix_traces,
            )
            _log_duration(console, verbose, "Tracker 로깅 완료", tracker_started_at)
        if db_path:
            db_started_at = datetime.now()
            _log_timestamp(console, verbose, f"DB 저장 시작 ({db_path})")
            _save_to_db(
                db_path,
                result,
                console,
                storage_cls=SQLiteStorageAdapter,
                prompt_bundle=prompt_bundle,
            )
            _log_duration(console, verbose, "DB 저장 완료", db_started_at)
        if output:
            output_started_at = datetime.now()
            _log_timestamp(console, verbose, f"결과 저장 시작 ({output})")
            _save_results(output, result, console)
            _log_duration(console, verbose, "결과 저장 완료", output_started_at)

        if auto_analyze:
            if not result.results:
                print_cli_warning(
                    console,
                    "평가 결과가 없어 자동 분석을 건너뜁니다.",
                    tips=["테스트 케이스가 포함된 데이터셋인지 확인하세요."],
                )
            else:
                analysis_prefix = f"analysis_{result.run_id}"
                analysis_output_path, analysis_report_path = resolve_output_paths(
                    base_dir=analysis_dir,
                    output_path=analysis_output,
                    report_path=analysis_report,
                    prefix=analysis_prefix,
                )
                console.print("\n[bold]자동 분석 실행[/bold]")
                storage = SQLiteStorageAdapter(db_path=db_path) if db_path else None
                pipeline_service = build_analysis_pipeline_service(
                    storage=storage,
                    llm_adapter=llm_adapter,
                )
                with console.status("[bold green]분석 파이프라인 실행 중..."):
                    pipeline_result = pipeline_service.analyze_intent(
                        AnalysisIntent.GENERATE_DETAILED,
                        run_id=result.run_id,
                        evaluation_run=result,
                        report_type="analysis",
                        use_llm_report=True,
                    )
                artifacts_dir = resolve_artifact_dir(
                    base_dir=analysis_dir,
                    output_path=analysis_output_path,
                    report_path=analysis_report_path,
                    prefix=analysis_prefix,
                )
                artifact_index = write_pipeline_artifacts(
                    pipeline_result,
                    artifacts_dir=artifacts_dir,
                )
                payload = serialize_pipeline_result(pipeline_result)
                payload["run_id"] = result.run_id
                payload["artifacts"] = artifact_index
                write_json(analysis_output_path, payload)

                report_text = extract_markdown_report(pipeline_result.final_output)
                if not report_text:
                    report_text = "# 자동 분석 보고서\n\n보고서 본문을 찾지 못했습니다.\n"
                analysis_report_path.write_text(report_text, encoding="utf-8")
                _display_pipeline_analysis_summary(console, pipeline_result, result)
                console.print(f"[green]자동 분석 결과 저장:[/green] {analysis_output_path}")
                console.print(f"[green]자동 분석 보고서 저장:[/green] {analysis_report_path}\n")
                console.print(
                    "[green]자동 분석 상세 결과 저장:[/green] "
                    f"{artifact_index['dir']} (index: {artifact_index['index']})\n"
                )

    @app.command(
        name="run-simple",
        help="Shortcut for 초보자용 간편 모드. `evalvault run --mode simple`과 동일합니다.",
    )
    def run_simple(  # noqa: PLR0913 - CLI arguments intentionally flat
        dataset: Path = typer.Argument(
            ...,
            help="Path to dataset file (CSV, Excel, or JSON).",
            exists=True,
            readable=True,
        ),
        summary: bool = typer.Option(
            False,
            "--summary",
            help=(
                "Enable summarization evaluation preset "
                "(summary_score, summary_faithfulness, entity_preservation)."
            ),
        ),
        metrics: str = typer.Option(
            "faithfulness,answer_relevancy",
            "--metrics",
            "-m",
            help="Comma-separated list of metrics to evaluate.",
        ),
        threshold_profile: str | None = typer.Option(
            None,
            "--threshold-profile",
            help="Apply a threshold profile (summary/qa) to matching metrics.",
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
        auto_analyze: bool = typer.Option(
            False,
            "--auto-analyze",
            help="평가 완료 후 통합 분석을 자동 실행하고 보고서를 저장합니다.",
        ),
        analysis_output: Path | None = typer.Option(
            None,
            "--analysis-json",
            help="자동 분석 JSON 결과 파일 경로 (기본값: reports/analysis).",
        ),
        analysis_report: Path | None = typer.Option(
            None,
            "--analysis-report",
            help="자동 분석 Markdown 보고서 경로 (기본값: reports/analysis).",
        ),
        analysis_dir: Path | None = typer.Option(
            None,
            "--analysis-dir",
            help="자동 분석 결과 저장 디렉터리 (기본: reports/analysis).",
        ),
        retriever: str | None = typer.Option(
            None,
            "--retriever",
            help="Retriever to fill empty contexts (bm25, dense, hybrid, graphrag).",
        ),
        retriever_docs: Path | None = typer.Option(
            None,
            "--retriever-docs",
            help="Documents file for retriever (.json/.jsonl/.txt).",
        ),
        kg: Path | None = typer.Option(
            None,
            "--kg",
            help="Knowledge graph JSON file for GraphRAG retriever.",
        ),
        retriever_top_k: int = typer.Option(
            5,
            "--retriever-top-k",
            help="Top-K documents to retrieve (default: 5).",
        ),
        stage_events: Path | None = typer.Option(
            None,
            "--stage-events",
            help="Write stage events as JSONL for later ingestion.",
        ),
        stage_store: bool = typer.Option(
            False,
            "--stage-store/--no-stage-store",
            help="Store stage events in the SQLite database (requires --db).",
        ),
        tracker: str = typer.Option(
            "none",
            "--tracker",
            "-t",
            help="Tracker to log results: 'langfuse', 'mlflow', 'phoenix', or 'none'.",
        ),
        langfuse: bool = typer.Option(
            False,
            "--langfuse",
            "-l",
            help="[Deprecated] Use --tracker langfuse instead.",
            hidden=True,
        ),
        phoenix_max_traces: int | None = typer.Option(
            None,
            "--phoenix-max-traces",
            help="Max per-test-case traces to send to Phoenix (default: send all).",
        ),
        phoenix_dataset: str | None = typer.Option(
            None,
            "--phoenix-dataset",
            help="Upload the dataset/test cases to Phoenix under this name.",
        ),
        phoenix_dataset_description: str | None = typer.Option(
            None,
            "--phoenix-dataset-description",
            help="Description stored on the Phoenix dataset (default: dataset metadata).",
        ),
        phoenix_experiment: str | None = typer.Option(
            None,
            "--phoenix-experiment",
            help="Create a Phoenix experiment record for this run (requires dataset upload).",
        ),
        phoenix_experiment_description: str | None = typer.Option(
            None,
            "--phoenix-experiment-description",
            help="Description stored on the Phoenix experiment.",
        ),
        prompt_manifest: Path | None = typer.Option(
            Path("agent/prompts/prompt_manifest.json"),
            "--prompt-manifest",
            help="Path to Phoenix prompt manifest JSON.",
        ),
        prompt_files: str | None = typer.Option(
            None,
            "--prompt-files",
            help="Comma-separated prompt files to capture in Phoenix metadata.",
        ),
        prompt_set_name: str | None = typer.Option(
            None,
            "--prompt-set-name",
            help="Name for the prompt set snapshot stored in the DB.",
        ),
        prompt_set_description: str | None = typer.Option(
            None,
            "--prompt-set-description",
            help="Description for the prompt set snapshot.",
        ),
        system_prompt: str | None = typer.Option(
            None,
            "--system-prompt",
            help="System prompt text for the target LLM (stored for comparison).",
        ),
        system_prompt_file: Path | None = typer.Option(
            None,
            "--system-prompt-file",
            help="Path to a system prompt file to store alongside this run.",
        ),
        system_prompt_name: str | None = typer.Option(
            None,
            "--system-prompt-name",
            help="Optional name for the system prompt snapshot.",
        ),
        ragas_prompts: Path | None = typer.Option(
            None,
            "--ragas-prompts",
            help="YAML file with Ragas metric prompt overrides.",
        ),
        db_path: Path | None = db_option(
            help_text="Path to SQLite database file for storing results.",
        ),
        use_domain_memory: bool = typer.Option(
            False,
            "--use-domain-memory",
            help="Leverage Domain Memory for threshold adjustment and insights.",
        ),
        memory_domain: str | None = typer.Option(
            None,
            "--memory-domain",
            help="Domain name for Domain Memory (defaults to dataset metadata).",
        ),
        memory_language: str = typer.Option(
            "ko",
            "--memory-language",
            help="Language code for Domain Memory lookups (default: ko).",
        ),
        memory_db: Path | None = memory_db_option(
            help_text="Path to Domain Memory database (default: data/db/evalvault_memory.db).",
        ),
        memory_augment_context: bool = typer.Option(
            False,
            "--augment-context",
            help="Append retrieved factual memories to each test case context.",
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
            "-b",
            help="Batch size for parallel evaluation (default: 5).",
        ),
        stream: bool = typer.Option(
            False,
            "--stream",
            help="Enable streaming evaluation for large datasets (process file in chunks).",
        ),
        stream_chunk_size: int = typer.Option(
            200,
            "--stream-chunk-size",
            help="Chunk size when streaming evaluation is enabled (default: 200).",
        ),
    ) -> None:
        """Alias for simple mode presets."""
        try:
            ctx = click.get_current_context()
        except RuntimeError:
            ctx = None
        if ctx:
            ctx.meta["run_mode_alias"] = "run-simple"
        try:
            run(
                dataset=dataset,
                evaluation_preset=None,
                summary=summary,
                metrics=metrics,
                threshold_profile=threshold_profile,
                profile=profile,
                model=model,
                output=output,
                auto_analyze=auto_analyze,
                analysis_output=analysis_output,
                analysis_report=analysis_report,
                analysis_dir=analysis_dir,
                retriever=retriever,
                retriever_docs=retriever_docs,
                kg=kg,
                retriever_top_k=retriever_top_k,
                stage_events=stage_events,
                stage_store=stage_store,
                tracker=tracker,
                langfuse=langfuse,
                phoenix_max_traces=phoenix_max_traces,
                phoenix_dataset=phoenix_dataset,
                phoenix_dataset_description=phoenix_dataset_description,
                phoenix_experiment=phoenix_experiment,
                phoenix_experiment_description=phoenix_experiment_description,
                prompt_manifest=prompt_manifest,
                prompt_files=prompt_files,
                prompt_set_name=prompt_set_name,
                prompt_set_description=prompt_set_description,
                system_prompt=system_prompt,
                system_prompt_file=system_prompt_file,
                system_prompt_name=system_prompt_name,
                ragas_prompts=ragas_prompts,
                db_path=db_path,
                use_domain_memory=use_domain_memory,
                memory_domain=memory_domain,
                memory_language=memory_language,
                memory_db=memory_db,
                memory_augment_context=memory_augment_context,
                verbose=verbose,
                parallel=parallel,
                batch_size=batch_size,
                stream=stream,
                stream_chunk_size=stream_chunk_size,
                mode="simple",
            )
        finally:
            if ctx:
                ctx.meta.pop("run_mode_alias", None)

    @app.command(
        name="run-full",
        help="전문가용 전체 모드를 바로 실행합니다. `evalvault run --mode full` 별칭.",
    )
    def run_full(  # noqa: PLR0913 - CLI arguments intentionally flat
        dataset: Path = typer.Argument(
            ...,
            help="Path to dataset file (CSV, Excel, or JSON).",
            exists=True,
            readable=True,
        ),
        summary: bool = typer.Option(
            False,
            "--summary",
            help=(
                "Enable summarization evaluation preset "
                "(summary_score, summary_faithfulness, entity_preservation)."
            ),
        ),
        metrics: str = typer.Option(
            "faithfulness,answer_relevancy",
            "--metrics",
            "-m",
            help="Comma-separated list of metrics to evaluate.",
        ),
        threshold_profile: str | None = typer.Option(
            None,
            "--threshold-profile",
            help="Apply a threshold profile (summary/qa) to matching metrics.",
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
        auto_analyze: bool = typer.Option(
            False,
            "--auto-analyze",
            help="평가 완료 후 통합 분석을 자동 실행하고 보고서를 저장합니다.",
        ),
        analysis_output: Path | None = typer.Option(
            None,
            "--analysis-json",
            help="자동 분석 JSON 결과 파일 경로 (기본값: reports/analysis).",
        ),
        analysis_report: Path | None = typer.Option(
            None,
            "--analysis-report",
            help="자동 분석 Markdown 보고서 경로 (기본값: reports/analysis).",
        ),
        analysis_dir: Path | None = typer.Option(
            None,
            "--analysis-dir",
            help="자동 분석 결과 저장 디렉터리 (기본: reports/analysis).",
        ),
        retriever: str | None = typer.Option(
            None,
            "--retriever",
            help="Retriever to fill empty contexts (bm25, dense, hybrid, graphrag).",
        ),
        retriever_docs: Path | None = typer.Option(
            None,
            "--retriever-docs",
            help="Documents file for retriever (.json/.jsonl/.txt).",
        ),
        kg: Path | None = typer.Option(
            None,
            "--kg",
            help="Knowledge graph JSON file for GraphRAG retriever.",
        ),
        retriever_top_k: int = typer.Option(
            5,
            "--retriever-top-k",
            help="Top-K documents to retrieve (default: 5).",
        ),
        stage_events: Path | None = typer.Option(
            None,
            "--stage-events",
            help="Write stage events as JSONL for later ingestion.",
        ),
        stage_store: bool = typer.Option(
            False,
            "--stage-store/--no-stage-store",
            help="Store stage events in the SQLite database (requires --db).",
        ),
        tracker: str = typer.Option(
            "none",
            "--tracker",
            "-t",
            help="Tracker to log results: 'langfuse', 'mlflow', 'phoenix', or 'none'.",
        ),
        langfuse: bool = typer.Option(
            False,
            "--langfuse",
            "-l",
            help="[Deprecated] Use --tracker langfuse instead.",
            hidden=True,
        ),
        phoenix_max_traces: int | None = typer.Option(
            None,
            "--phoenix-max-traces",
            help="Max per-test-case traces to send to Phoenix (default: send all).",
        ),
        phoenix_dataset: str | None = typer.Option(
            None,
            "--phoenix-dataset",
            help="Upload the dataset/test cases to Phoenix under this name.",
        ),
        phoenix_dataset_description: str | None = typer.Option(
            None,
            "--phoenix-dataset-description",
            help="Description stored on the Phoenix dataset (default: dataset metadata).",
        ),
        phoenix_experiment: str | None = typer.Option(
            None,
            "--phoenix-experiment",
            help="Create a Phoenix experiment record for this run (requires dataset upload).",
        ),
        phoenix_experiment_description: str | None = typer.Option(
            None,
            "--phoenix-experiment-description",
            help="Description stored on the Phoenix experiment.",
        ),
        prompt_manifest: Path | None = typer.Option(
            Path("agent/prompts/prompt_manifest.json"),
            "--prompt-manifest",
            help="Path to Phoenix prompt manifest JSON.",
        ),
        prompt_files: str | None = typer.Option(
            None,
            "--prompt-files",
            help="Comma-separated prompt files to capture in Phoenix metadata.",
        ),
        prompt_set_name: str | None = typer.Option(
            None,
            "--prompt-set-name",
            help="Name for the prompt set snapshot stored in the DB.",
        ),
        prompt_set_description: str | None = typer.Option(
            None,
            "--prompt-set-description",
            help="Description for the prompt set snapshot.",
        ),
        system_prompt: str | None = typer.Option(
            None,
            "--system-prompt",
            help="System prompt text for the target LLM (stored for comparison).",
        ),
        system_prompt_file: Path | None = typer.Option(
            None,
            "--system-prompt-file",
            help="Path to a system prompt file to store alongside this run.",
        ),
        system_prompt_name: str | None = typer.Option(
            None,
            "--system-prompt-name",
            help="Optional name for the system prompt snapshot.",
        ),
        ragas_prompts: Path | None = typer.Option(
            None,
            "--ragas-prompts",
            help="YAML file with Ragas metric prompt overrides.",
        ),
        db_path: Path | None = db_option(
            help_text="Path to SQLite database file for storing results.",
        ),
        use_domain_memory: bool = typer.Option(
            False,
            "--use-domain-memory",
            help="Leverage Domain Memory for threshold adjustment and insights.",
        ),
        memory_domain: str | None = typer.Option(
            None,
            "--memory-domain",
            help="Domain name for Domain Memory (defaults to dataset metadata).",
        ),
        memory_language: str = typer.Option(
            "ko",
            "--memory-language",
            help="Language code for Domain Memory lookups (default: ko).",
        ),
        memory_db: Path | None = memory_db_option(
            help_text="Path to Domain Memory database (default: data/db/evalvault_memory.db).",
        ),
        memory_augment_context: bool = typer.Option(
            False,
            "--augment-context",
            help="Append retrieved factual memories to each test case context.",
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
            "-b",
            help="Batch size for parallel evaluation (default: 5).",
        ),
        stream: bool = typer.Option(
            False,
            "--stream",
            help="Enable streaming evaluation for large datasets (process file in chunks).",
        ),
        stream_chunk_size: int = typer.Option(
            200,
            "--stream-chunk-size",
            help="Chunk size when streaming evaluation is enabled (default: 200).",
        ),
    ) -> None:
        """Alias for full mode presets."""
        try:
            ctx = click.get_current_context()
        except RuntimeError:
            ctx = None
        if ctx:
            ctx.meta["run_mode_alias"] = "run-full"
        try:
            run(
                dataset=dataset,
                evaluation_preset=None,
                summary=summary,
                metrics=metrics,
                threshold_profile=threshold_profile,
                profile=profile,
                model=model,
                output=output,
                auto_analyze=auto_analyze,
                analysis_output=analysis_output,
                analysis_report=analysis_report,
                analysis_dir=analysis_dir,
                retriever=retriever,
                retriever_docs=retriever_docs,
                kg=kg,
                retriever_top_k=retriever_top_k,
                stage_events=stage_events,
                stage_store=stage_store,
                tracker=tracker,
                langfuse=langfuse,
                phoenix_max_traces=phoenix_max_traces,
                phoenix_dataset=phoenix_dataset,
                phoenix_dataset_description=phoenix_dataset_description,
                phoenix_experiment=phoenix_experiment,
                phoenix_experiment_description=phoenix_experiment_description,
                prompt_manifest=prompt_manifest,
                prompt_files=prompt_files,
                prompt_set_name=prompt_set_name,
                prompt_set_description=prompt_set_description,
                system_prompt=system_prompt,
                system_prompt_file=system_prompt_file,
                system_prompt_name=system_prompt_name,
                ragas_prompts=ragas_prompts,
                db_path=db_path,
                use_domain_memory=use_domain_memory,
                memory_domain=memory_domain,
                memory_language=memory_language,
                memory_db=memory_db,
                memory_augment_context=memory_augment_context,
                verbose=verbose,
                parallel=parallel,
                batch_size=batch_size,
                stream=stream,
                stream_chunk_size=stream_chunk_size,
                mode="full",
            )
        finally:
            if ctx:
                ctx.meta.pop("run_mode_alias", None)


def _display_pipeline_analysis_summary(
    console: Console,
    pipeline_result,
    run,
) -> None:
    """Display a concise auto-analysis summary."""

    stats_output = get_node_output(pipeline_result, "statistics")
    ragas_output = get_node_output(pipeline_result, "ragas_eval")
    priority_output = get_node_output(pipeline_result, "priority_summary")
    time_series_output = get_node_output(pipeline_result, "time_series")

    scorecard = build_metric_scorecard(run, stats_output, ragas_output)
    quality = build_quality_summary(run, ragas_output, time_series_output, {})
    priority = build_priority_highlights(priority_output)

    console.print("\n[bold]자동 분석 요약[/bold]")
    console.print(f"- Run ID: {getattr(run, 'run_id', '-')}")
    console.print(f"- 데이터셋: {getattr(run, 'dataset_name', '-')}")
    console.print(f"- 모델: {getattr(run, 'model_name', '-')}")
    console.print(f"- 테스트 케이스: {getattr(run, 'total_test_cases', 0)}")
    console.print(f"- 통과율: {_format_percent(getattr(run, 'pass_rate', None))}")

    if scorecard:
        table = Table(title="지표 스코어카드", show_header=True, header_style="bold cyan")
        table.add_column("Metric")
        table.add_column("Mean", justify="right")
        table.add_column("Threshold", justify="right")
        table.add_column("Pass Rate", justify="right")
        table.add_column("Status")

        for row in scorecard:
            table.add_row(
                str(row.get("metric") or "-"),
                _format_float(row.get("mean")),
                _format_float(row.get("threshold")),
                _format_percent(row.get("pass_rate")),
                str(row.get("status") or "-"),
            )

        console.print(table)

    console.print("\n[bold]데이터 품질/신뢰도[/bold]")
    console.print(f"- 전체 케이스: {quality.get('total_cases', '-')}")
    console.print(f"- 평가 샘플: {quality.get('sample_count', '-')}")
    console.print(f"- 커버리지: {_format_percent(quality.get('coverage'))}")
    for flag in quality.get("flags", []):
        console.print(f"- 주의: {flag}")

    cases = _merge_priority_cases(priority)
    if cases:
        table = Table(title="우선순위 케이스", show_header=True, header_style="bold cyan")
        table.add_column("Type")
        table.add_column("Case")
        table.add_column("Avg", justify="right")
        table.add_column("Impact", justify="right")
        table.add_column("Failed")
        table.add_column("Question")

        for item in cases:
            table.add_row(
                item["type"],
                str(item.get("test_case_id") or "-"),
                _format_float(item.get("avg_score")),
                _format_float(item.get("impact_score")),
                ", ".join(item.get("failed_metrics") or []) or "-",
                _truncate_preview(item.get("question_preview")),
            )
        console.print(table)


def _merge_priority_cases(priority: dict[str, Any]) -> list[dict[str, Any]]:
    """Merge bottom/impact cases into a single list."""
    merged = []
    seen = set()
    for tag, cases in (
        ("bottom", priority.get("bottom_cases", [])),
        ("impact", priority.get("impact_cases", [])),
    ):
        for item in cases:
            case_id = item.get("test_case_id")
            key = (tag, case_id)
            if key in seen:
                continue
            seen.add(key)
            merged.append(
                {
                    "type": tag,
                    "test_case_id": case_id,
                    "avg_score": item.get("avg_score"),
                    "impact_score": item.get("impact_score"),
                    "failed_metrics": item.get("failed_metrics"),
                    "question_preview": item.get("question_preview"),
                }
            )
    return merged


def _truncate_preview(text: str | None, max_len: int = 60) -> str:
    if not text:
        return "-"
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _format_float(value: float | None, precision: int = 3) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{precision}f}"
    except (TypeError, ValueError):
        return "-"


def _format_percent(value: float | None, precision: int = 1) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{precision}%}"
    except (TypeError, ValueError):
        return "-"


__all__ = [
    "register_run_commands",
    "enrich_dataset_with_memory",
    "apply_retriever_to_dataset",
    "load_retriever_documents",
    "log_phoenix_traces",
]
