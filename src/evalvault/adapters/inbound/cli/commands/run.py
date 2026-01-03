"""`evalvault run` 명령 전용 Typer 등록 모듈."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any, Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from evalvault.adapters.outbound.dataset import (
    StreamingConfig,
    StreamingDatasetLoader,
    get_loader,
)
from evalvault.adapters.outbound.domain_memory.sqlite_adapter import SQLiteDomainMemoryAdapter
from evalvault.adapters.outbound.llm import get_llm_adapter
from evalvault.adapters.outbound.phoenix.sync_service import (
    PhoenixDatasetInfo,
    PhoenixSyncError,
    PhoenixSyncService,
    build_experiment_metadata,
)
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.config.phoenix_support import (
    ensure_phoenix_instrumentation,
    get_phoenix_trace_url,
    instrumentation_span,
    set_span_attributes,
)
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.entities import (
    Dataset,
    EvaluationRun,
    GenerationData,
    RAGTraceData,
    RetrievalData,
    RetrievedDocument,
)
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.domain.services.memory_aware_evaluator import MemoryAwareEvaluator
from evalvault.domain.services.memory_based_analysis import MemoryBasedAnalysis
from evalvault.domain.services.prompt_manifest import (
    PromptDiffSummary,
    load_prompt_manifest,
    summarize_prompt_entry,
)
from evalvault.ports.outbound.llm_port import LLMPort
from evalvault.ports.outbound.tracker_port import TrackerPort

from ..utils.formatters import format_score, format_status
from ..utils.options import db_option, memory_db_option, profile_option
from ..utils.validators import parse_csv_option, validate_choices

TrackerType = Literal["langfuse", "mlflow", "phoenix", "none"]


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
        db_path: Path | None = db_option(
            default=None,
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
        memory_db: Path = memory_db_option(
            help_text="Path to Domain Memory database (default: evalvault_memory.db).",
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
        """Run RAG evaluation on a dataset."""
        metric_list = parse_csv_option(metrics)
        validate_choices(metric_list, available_metrics, console, value_label="metric")

        prompt_manifest_path = prompt_manifest.expanduser() if prompt_manifest else None
        prompt_file_list = [Path(item).expanduser() for item in parse_csv_option(prompt_files)]
        prompt_metadata_entries: list[dict[str, Any]] = []
        if prompt_file_list:
            prompt_metadata_entries = _collect_prompt_metadata(
                manifest_path=prompt_manifest_path,
                prompt_files=prompt_file_list,
                console=console,
            )
            if prompt_metadata_entries:
                console.print(
                    f"[dim]Collected Phoenix prompt metadata for {len(prompt_metadata_entries)} file(s).[/dim]"
                )
                unsynced = [
                    entry for entry in prompt_metadata_entries if entry.get("status") != "synced"
                ]
                if unsynced:
                    console.print(
                        "[yellow]Warning:[/yellow] Prompt files differ from manifest. "
                        "Run `evalvault phoenix prompt-diff` to review changes."
                    )

        if stream_chunk_size <= 0:
            console.print("[red]Error:[/red] --stream-chunk-size must be greater than 0.")
            raise typer.Exit(1)

        domain_memory_requested = (
            use_domain_memory or memory_domain is not None or memory_augment_context
        )

        if stream and domain_memory_requested:
            console.print(
                "[red]Error:[/red] --stream mode does not support Domain Memory options yet."
            )
            raise typer.Exit(1)
        if stream and (phoenix_dataset or phoenix_experiment):
            console.print(
                "[red]Error:[/red] Streaming mode cannot upload Phoenix datasets/experiments."
            )
            raise typer.Exit(1)

        settings = Settings()

        # Apply profile (CLI > .env > default)
        profile_name = profile or settings.evalvault_profile
        if profile_name:
            settings = apply_profile(settings, profile_name)

        # Override model if specified
        if model:
            if _is_oss_open_model(model):
                settings.llm_provider = "ollama"
                settings.ollama_model = model
                console.print(
                    "[dim]OSS model detected. Routing request through Ollama backend.[/dim]"
                )
            elif settings.llm_provider == "ollama":
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

        phoenix_trace_metadata: dict[str, Any] = {
            "dataset.path": str(dataset),
            "metrics": metric_list,
        }

        # Load dataset or configure streaming metadata
        if stream:
            ds = _build_streaming_dataset_template(dataset)
            console.print(
                f"[dim]Streaming evaluation enabled (chunk size={stream_chunk_size}).[/dim]"
            )
            phoenix_trace_metadata["dataset.stream"] = True
            phoenix_trace_metadata["dataset.template_version"] = ds.version
        else:
            with console.status("[bold green]Loading dataset..."):
                try:
                    loader = get_loader(dataset)
                    ds = loader.load(dataset)
                    console.print(f"[green]Loaded {len(ds)} test cases[/green]")
                    phoenix_trace_metadata["dataset.test_cases"] = len(ds)
                    if ds.metadata:
                        for key, value in ds.metadata.items():
                            phoenix_trace_metadata[f"dataset.meta.{key}"] = str(value)
                except Exception as exc:  # pragma: no cover - user feedback path
                    console.print(f"[red]Error loading dataset:[/red] {exc}")
                    raise typer.Exit(1) from exc

        resolved_thresholds = _resolve_thresholds(metric_list, ds)

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
                console.print(f"[yellow]Warning:[/yellow] {exc}")
                phoenix_sync_service = None

        effective_tracker = tracker
        if langfuse and tracker == "none":
            effective_tracker = "langfuse"
            console.print(
                "[yellow]Warning:[/yellow] --langfuse is deprecated. Use --tracker langfuse instead."
            )

        config_wants_phoenix = getattr(settings, "phoenix_enabled", False)
        if not isinstance(config_wants_phoenix, bool):
            config_wants_phoenix = False
        should_enable_phoenix = effective_tracker == "phoenix" or config_wants_phoenix
        if should_enable_phoenix:
            ensure_phoenix_instrumentation(settings, console=console, force=True)

        evaluator = RagasEvaluator()
        llm_adapter = get_llm_adapter(settings)

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
            try:
                memory_adapter = SQLiteDomainMemoryAdapter(memory_db)
                memory_evaluator = MemoryAwareEvaluator(
                    evaluator=evaluator, memory_port=memory_adapter
                )
                console.print(
                    f"[dim]Domain Memory enabled for '{memory_domain_name}' ({memory_language}).[/dim]"
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
            except Exception as exc:  # pragma: no cover - best-effort memory hookup
                console.print(
                    f"[yellow]Warning:[/yellow] Domain Memory initialization failed: {exc}"
                )
                memory_evaluator = None
                memory_adapter = None

        if memory_evaluator and memory_augment_context:
            enriched = enrich_dataset_with_memory(
                dataset=ds,
                memory_evaluator=memory_evaluator,
                domain=memory_domain_name,
                language=memory_language,
            )
            if enriched:
                console.print(
                    f"[dim]Appended Domain Memory facts to {enriched} test case(s).[/dim]"
                )

        if ds.thresholds:
            console.print("[dim]Thresholds from dataset:[/dim]")
            for metric, threshold in ds.thresholds.items():
                console.print(f"  [dim]{metric}: {threshold}[/dim]")
            console.print()
        elif resolved_thresholds:
            console.print("[dim]Thresholds in use:[/dim]")
            for metric, threshold in resolved_thresholds.items():
                console.print(f"  [dim]{metric}: {threshold}[/dim]")
            console.print()

        if stream:
            status_msg = (
                f"[bold green]Running streaming evaluation (chunk_size={stream_chunk_size})..."
            )
        elif parallel:
            status_msg = f"[bold green]Running parallel evaluation (batch_size={batch_size})..."
        else:
            status_msg = "[bold green]Running evaluation..."
        with console.status(status_msg):
            try:
                if stream:
                    result = asyncio.run(
                        _evaluate_streaming_run(
                            dataset_path=dataset,
                            dataset_template=ds,
                            metrics=metric_list,
                            thresholds=resolved_thresholds,
                            evaluator=evaluator,
                            llm=llm_adapter,
                            chunk_size=stream_chunk_size,
                            parallel=parallel,
                            batch_size=batch_size,
                        )
                    )
                elif memory_evaluator and use_domain_memory:
                    result = asyncio.run(
                        memory_evaluator.evaluate_with_memory(
                            dataset=ds,
                            metrics=metric_list,
                            llm=llm_adapter,
                            thresholds=resolved_thresholds,
                            parallel=parallel,
                            batch_size=batch_size,
                            domain=memory_domain_name,
                            language=memory_language,
                        )
                    )
                else:
                    result = asyncio.run(
                        evaluator.evaluate(
                            dataset=ds,
                            metrics=metric_list,
                            llm=llm_adapter,
                            thresholds=resolved_thresholds,
                            parallel=parallel,
                            batch_size=batch_size,
                        )
                    )
            except Exception as exc:  # pragma: no cover - surfaced to CLI
                console.print(f"[red]Error during evaluation:[/red] {exc}")
                raise typer.Exit(1) from exc

        phoenix_trace_metadata["dataset.test_cases"] = result.total_test_cases

        _display_results(result, console, verbose)

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
                    console.print(
                        f"[yellow]Warning:[/yellow] Failed to upload dataset to Phoenix: {exc}"
                    )
            if phoenix_experiment:
                if not phoenix_dataset_result:
                    console.print(
                        "[yellow]Warning:[/yellow] Skipping Phoenix experiment creation "
                        "because the dataset was not uploaded."
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
                        console.print(
                            f"[yellow]Warning:[/yellow] Failed to create Phoenix experiment: {exc}"
                        )

        if prompt_metadata_entries:
            phoenix_meta = result.tracker_metadata.setdefault("phoenix", {})
            phoenix_meta.setdefault("schema_version", 2)
            phoenix_meta["prompts"] = prompt_metadata_entries

        if effective_tracker != "none":
            phoenix_opts = None
            if effective_tracker == "phoenix":
                phoenix_opts = {
                    "max_traces": phoenix_max_traces,
                    "metadata": phoenix_trace_metadata or None,
                }
            _log_to_tracker(
                settings,
                result,
                console,
                effective_tracker,
                phoenix_options=phoenix_opts,
            )
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

    def _get_tracker(settings: Settings, tracker_type: str, console: Console) -> TrackerPort | None:
        """Get the appropriate tracker adapter based on type."""
        if tracker_type == "langfuse":
            if not settings.langfuse_public_key or not settings.langfuse_secret_key:
                console.print(
                    "[yellow]Warning:[/yellow] Langfuse credentials not configured. Skipping."
                )
                return None
            from evalvault.adapters.outbound.tracker.langfuse_adapter import LangfuseAdapter

            return LangfuseAdapter(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )

        elif tracker_type == "mlflow":
            if not settings.mlflow_tracking_uri:
                console.print(
                    "[yellow]Warning:[/yellow] MLflow tracking URI not configured. Skipping."
                )
                return None
            try:
                from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

                return MLflowAdapter(
                    tracking_uri=settings.mlflow_tracking_uri,
                    experiment_name=settings.mlflow_experiment_name,
                )
            except ImportError:
                console.print(
                    "[yellow]Warning:[/yellow] MLflow not installed. "
                    "Install with: uv sync --extra mlflow"
                )
                return None

        elif tracker_type == "phoenix":
            try:
                from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

                return PhoenixAdapter(
                    endpoint=settings.phoenix_endpoint,
                    service_name="evalvault",
                )
            except ImportError:
                console.print(
                    "[yellow]Warning:[/yellow] Phoenix not installed. "
                    "Install with: uv sync --extra phoenix"
                )
                return None

        else:
            console.print(f"[yellow]Warning:[/yellow] Unknown tracker type: {tracker_type}")
            return None

    def _build_phoenix_trace_url(endpoint: str, trace_id: str) -> str:
        """Build a Phoenix UI URL for the given trace ID."""

        base = endpoint.rstrip("/")
        suffix = "/v1/traces"
        if base.endswith(suffix):
            base = base[: -len(suffix)]
        return f"{base.rstrip('/')}/#/traces/{trace_id}"

    def _log_to_tracker(
        settings: Settings,
        result,
        console: Console,
        tracker_type: str,
        *,
        phoenix_options: dict[str, Any] | None = None,
    ) -> None:
        """Log evaluation results to the specified tracker."""
        tracker = _get_tracker(settings, tracker_type, console)
        if tracker is None:
            return

        tracker_name = tracker_type.capitalize()
        trace_id: str | None = None
        with console.status(f"[bold green]Logging to {tracker_name}..."):
            try:
                trace_id = tracker.log_evaluation_run(result)
                console.print(f"[green]Logged to {tracker_name}[/green] (trace_id: {trace_id})")
                if trace_id and tracker_type == "phoenix":
                    endpoint = getattr(
                        settings, "phoenix_endpoint", "http://localhost:6006/v1/traces"
                    )
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
            except Exception as exc:  # pragma: no cover - telemetry best-effort
                console.print(f"[yellow]Warning:[/yellow] Failed to log to {tracker_name}: {exc}")
                return

        if tracker_type == "phoenix":
            options = phoenix_options or {}
            extra = log_phoenix_traces(
                tracker,
                result,
                max_traces=options.get("max_traces"),
                metadata=options.get("metadata"),
            )
            if extra:
                console.print(
                    f"[dim]Recorded {extra} Phoenix RAG trace(s) for detailed observability.[/dim]"
                )

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


def _resolve_thresholds(metrics: list[str], dataset: Dataset) -> dict[str, float]:
    """Resolve thresholds by preferring dataset values and falling back to defaults."""

    base_thresholds = dataset.thresholds or {}
    resolved: dict[str, float] = {}
    for metric in metrics:
        if metric in base_thresholds:
            resolved[metric] = base_thresholds[metric]
        else:
            resolved[metric] = 0.7
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

    merged.dataset_name = dataset_name
    merged.dataset_version = dataset_version
    merged.metrics_evaluated = list(metrics)
    merged.thresholds = dict(thresholds)
    return merged


async def _evaluate_streaming_run(
    *,
    dataset_path: Path,
    dataset_template: Dataset,
    metrics: list[str],
    thresholds: dict[str, float],
    evaluator: RagasEvaluator,
    llm: LLMPort,
    chunk_size: int,
    parallel: bool,
    batch_size: int,
) -> EvaluationRun:
    """Evaluate a dataset in streaming mode, chunk by chunk."""

    config = StreamingConfig(chunk_size=chunk_size)
    loader = StreamingDatasetLoader(config)
    merged_run: EvaluationRun | None = None
    metadata_template = dict(dataset_template.metadata or {})
    threshold_template = dict(dataset_template.thresholds or {})
    source_file = dataset_template.source_file or str(dataset_path)

    for chunk in loader.load_chunked(dataset_path, chunk_size=chunk_size):
        if not chunk:
            continue
        chunk_dataset = Dataset(
            name=dataset_template.name,
            version=dataset_template.version,
            test_cases=list(chunk),
            metadata=dict(metadata_template),
            source_file=source_file,
            thresholds=dict(threshold_template),
        )
        chunk_run = await evaluator.evaluate(
            dataset=chunk_dataset,
            metrics=metrics,
            llm=llm,
            thresholds=thresholds,
            parallel=parallel,
            batch_size=batch_size,
        )
        merged_run = _merge_evaluation_runs(
            merged_run,
            chunk_run,
            dataset_name=dataset_template.name,
            dataset_version=dataset_template.version,
            metrics=metrics,
            thresholds=thresholds,
        )

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
                console.print(
                    f"[yellow]Warning:[/yellow] Failed to load prompt manifest {manifest_path}: {exc}"
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
                console.print(f"[yellow]Warning:[/yellow] Prompt file not found: {target}")
            continue

        summary = summarize_prompt_entry(
            manifest_data,
            prompt_path=target,
            content=content,
        )
        summary.content_preview = _build_content_preview(content)
        summaries.append(asdict(summary))

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


__all__ = ["register_run_commands", "enrich_dataset_with_memory", "log_phoenix_traces"]
