"""`evalvault run` 명령 전용 Typer 등록 모듈."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from evalvault.adapters.outbound.dataset import get_loader
from evalvault.adapters.outbound.domain_memory.sqlite_adapter import SQLiteDomainMemoryAdapter
from evalvault.adapters.outbound.llm import get_llm_adapter
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
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
    ) -> None:
        """Run RAG evaluation on a dataset."""
        metric_list = parse_csv_option(metrics)
        validate_choices(metric_list, available_metrics, console, value_label="metric")

        settings = Settings()

        # Apply profile (CLI > .env > default)
        profile_name = profile or settings.evalvault_profile
        if profile_name:
            settings = apply_profile(settings, profile_name)

        # Override model if specified
        if model:
            if settings.llm_provider == "ollama":
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

        # Load dataset
        with console.status("[bold green]Loading dataset..."):
            try:
                loader = get_loader(dataset)
                ds = loader.load(dataset)
                console.print(f"[green]Loaded {len(ds)} test cases[/green]")
            except Exception as exc:  # pragma: no cover - user feedback path
                console.print(f"[red]Error loading dataset:[/red] {exc}")
                raise typer.Exit(1) from exc

        evaluator = RagasEvaluator()
        llm_adapter = get_llm_adapter(settings)

        memory_adapter: SQLiteDomainMemoryAdapter | None = None
        memory_evaluator: MemoryAwareEvaluator | None = None
        memory_domain_name = memory_domain or ds.metadata.get("domain") or "default"
        memory_required = use_domain_memory or memory_domain is not None or memory_augment_context

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
                    if reliability:
                        console.print(
                            "[dim]Reliability snapshot:[/dim] "
                            + ", ".join(f"{k}={v:.2f}" for k, v in reliability.items())
                        )
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

        status_msg = "[bold green]Running evaluation..."
        if parallel:
            status_msg = f"[bold green]Running parallel evaluation (batch_size={batch_size})..."
        with console.status(status_msg):
            try:
                if memory_evaluator and use_domain_memory:
                    result = asyncio.run(
                        memory_evaluator.evaluate_with_memory(
                            dataset=ds,
                            metrics=metric_list,
                            llm=llm_adapter,
                            thresholds=None,
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
                            thresholds=None,
                            parallel=parallel,
                            batch_size=batch_size,
                        )
                    )
            except Exception as exc:  # pragma: no cover - surfaced to CLI
                console.print(f"[red]Error during evaluation:[/red] {exc}")
                raise typer.Exit(1) from exc

        _display_results(result, console, verbose)

        if memory_adapter and memory_required:
            analyzer = MemoryBasedAnalysis(memory_port=memory_adapter)
            insights = analyzer.generate_insights(
                evaluation_run=result,
                domain=memory_domain_name,
                language=memory_language,
            )
            _display_memory_insights(insights, console)

        # Handle deprecated --langfuse flag
        effective_tracker = tracker
        if langfuse and tracker == "none":
            effective_tracker = "langfuse"
            console.print(
                "[yellow]Warning:[/yellow] --langfuse is deprecated. Use --tracker langfuse instead."
            )

        if effective_tracker != "none":
            _log_to_tracker(settings, result, console, effective_tracker)
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

    def _log_to_tracker(
        settings: Settings,
        result,
        console: Console,
        tracker_type: str,
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
            except Exception as exc:  # pragma: no cover - telemetry best-effort
                console.print(f"[yellow]Warning:[/yellow] Failed to log to {tracker_name}: {exc}")
                return

        if tracker_type == "phoenix":
            extra = log_phoenix_traces(tracker, result)
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

    enriched = 0
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
    return enriched


def log_phoenix_traces(
    tracker: TrackerPort,
    run: EvaluationRun,
    max_traces: int = 20,
) -> int:
    """Log per-test-case RAG traces when Phoenix adapter supports it."""

    log_trace = getattr(tracker, "log_rag_trace", None)
    if not callable(log_trace):
        return 0

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

        rag_trace = RAGTraceData(
            query=result.question or "",
            retrieval=retrieval_data,
            generation=generation_data,
            final_answer=result.answer or "",
            total_time_ms=result.latency_ms or 0,
            metadata={"run_id": run.run_id, "test_case_id": result.test_case_id},
        )

        try:
            log_trace(rag_trace)
            count += 1
        except Exception:  # pragma: no cover - telemetry best effort
            break

        if count >= max_traces:
            break

    return count


__all__ = ["register_run_commands", "enrich_dataset_with_memory", "log_phoenix_traces"]
