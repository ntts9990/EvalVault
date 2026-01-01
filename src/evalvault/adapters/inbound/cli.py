"""CLI interface for EvalVault using Typer."""

# Fix SSL certificate issues on macOS with uv-managed Python
try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass  # truststore not installed, use default SSL

import asyncio
import base64
import json
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from evalvault.adapters.outbound.analysis import (
    CausalAnalysisAdapter,
    NLPAnalysisAdapter,
    StatisticalAnalysisAdapter,
)
from evalvault.adapters.outbound.cache import MemoryCacheAdapter
from evalvault.adapters.outbound.dataset import get_loader
from evalvault.adapters.outbound.llm import LLMRelationAugmenter, get_llm_adapter
from evalvault.adapters.outbound.report import MarkdownReportAdapter
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.adapters.outbound.tracker.langfuse_adapter import LangfuseAdapter
from evalvault.config.domain_config import (
    generate_domain_template,
    list_domains,
    load_domain_config,
    save_domain_config,
)
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.services.analysis_service import AnalysisService
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.domain.services.experiment_manager import ExperimentManager
from evalvault.domain.services.kg_generator import KnowledgeGraphGenerator
from evalvault.domain.services.testset_generator import (
    BasicTestsetGenerator,
    GenerationConfig,
)

app = typer.Typer(
    name="evalvault",
    help="RAG evaluation system using Ragas with Langfuse tracing.",
    add_completion=False,
)
kg_app = typer.Typer(name="kg", help="Knowledge graph utilities.")
app.add_typer(kg_app, name="kg")
domain_app = typer.Typer(name="domain", help="Domain memory management.")
app.add_typer(domain_app, name="domain")
pipeline_app = typer.Typer(name="pipeline", help="Query-based analysis pipeline.")
app.add_typer(pipeline_app, name="pipeline")
benchmark_app = typer.Typer(name="benchmark", help="Korean RAG benchmark utilities.")
app.add_typer(benchmark_app, name="benchmark")
console = Console()

# Available metrics
AVAILABLE_METRICS = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "factual_correctness",
    "semantic_similarity",
    "insurance_term_accuracy",
]


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        rprint("[bold]EvalVault[/bold] version [cyan]0.1.0[/cyan]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    """EvalVault - RAG evaluation system."""
    pass


@app.command()
def run(
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
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="Model profile (dev, prod, openai). Overrides .env setting.",
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
    langfuse: bool = typer.Option(
        False,
        "--langfuse",
        "-l",
        help="Log results to Langfuse.",
    ),
    db_path: Path | None = typer.Option(
        None,
        "--db",
        help="Path to SQLite database file for storing results.",
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
):
    """Run RAG evaluation on a dataset."""
    # Parse metrics
    metric_list = [m.strip() for m in metrics.split(",")]

    # Validate metrics
    invalid_metrics = [m for m in metric_list if m not in AVAILABLE_METRICS]
    if invalid_metrics:
        console.print(f"[red]Error:[/red] Invalid metrics: {', '.join(invalid_metrics)}")
        console.print(f"Available metrics: {', '.join(AVAILABLE_METRICS)}")
        raise typer.Exit(1)

    # Load settings
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

    # Validate provider-specific requirements
    if settings.llm_provider == "openai" and not settings.openai_api_key:
        console.print("[red]Error:[/red] OPENAI_API_KEY not set.")
        console.print("Set it in your .env file or use --profile dev for Ollama.")
        raise typer.Exit(1)

    # Get model name for display
    if settings.llm_provider == "ollama":
        display_model = f"ollama/{settings.ollama_model}"
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

    # Load dataset
    with console.status("[bold green]Loading dataset..."):
        try:
            loader = get_loader(dataset)
            ds = loader.load(dataset)
            console.print(f"[green]Loaded {len(ds)} test cases[/green]")
        except Exception as e:
            console.print(f"[red]Error loading dataset:[/red] {e}")
            raise typer.Exit(1)

    # Initialize components
    llm = get_llm_adapter(settings)
    evaluator = RagasEvaluator()

    # Show thresholds from dataset if present
    if ds.thresholds:
        console.print("[dim]Thresholds from dataset:[/dim]")
        for metric, threshold in ds.thresholds.items():
            console.print(f"  [dim]{metric}: {threshold}[/dim]")
        console.print()

    # Run evaluation (thresholds resolved from dataset or default 0.7)
    status_msg = "[bold green]Running evaluation..."
    if parallel:
        status_msg = f"[bold green]Running parallel evaluation (batch_size={batch_size})..."
    with console.status(status_msg):
        try:
            result = asyncio.run(
                evaluator.evaluate(
                    dataset=ds,
                    metrics=metric_list,
                    llm=llm,
                    thresholds=None,  # Let evaluator use dataset.thresholds
                    parallel=parallel,
                    batch_size=batch_size,
                )
            )
        except Exception as e:
            console.print(f"[red]Error during evaluation:[/red] {e}")
            raise typer.Exit(1)

    # Display results
    _display_results(result, verbose)

    # Log to Langfuse if requested
    if langfuse:
        _log_to_langfuse(settings, result)

    # Save to database if requested
    if db_path:
        _save_to_db(db_path, result)

    # Save to file if requested
    if output:
        _save_results(output, result)


def _display_results(result, verbose: bool = False):
    """Display evaluation results in a formatted table."""
    # Calculate duration safely
    duration = result.duration_seconds
    duration_str = f"{duration:.2f}s" if duration is not None else "N/A"

    # Summary panel
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

    # Metrics table
    table = Table(title="Metric Scores", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Average Score", justify="right")
    table.add_column("Threshold", justify="right")
    table.add_column("Status", justify="center")

    for metric in result.metrics_evaluated:
        avg_score = result.get_avg_score(metric)
        threshold = result.thresholds.get(metric, 0.7)
        passed = avg_score >= threshold

        status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
        score_color = "green" if passed else "red"

        table.add_row(
            metric,
            f"[{score_color}]{avg_score:.3f}[/{score_color}]",
            f"{threshold:.2f}",
            status,
        )

    console.print(table)

    # Detailed results if verbose
    if verbose:
        console.print("\n[bold]Detailed Results[/bold]\n")
        for tc_result in result.results:
            status = "[green]PASS[/green]" if tc_result.all_passed else "[red]FAIL[/red]"
            console.print(f"  {tc_result.test_case_id}: {status}")
            for metric in tc_result.metrics:
                m_status = "[green]+[/green]" if metric.passed else "[red]-[/red]"
                console.print(
                    f"    {m_status} {metric.name}: {metric.score:.3f} (threshold: {metric.threshold})"
                )


def _log_to_langfuse(settings: Settings, result):
    """Log results to Langfuse."""
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        console.print(
            "[yellow]Warning:[/yellow] Langfuse credentials not configured. "
            "Skipping Langfuse logging."
        )
        return

    with console.status("[bold green]Logging to Langfuse..."):
        try:
            tracker = LangfuseAdapter(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
            trace_id = tracker.log_evaluation_run(result)
            console.print(f"[green]Logged to Langfuse[/green] (trace_id: {trace_id})")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Failed to log to Langfuse: {e}")


def _save_to_db(db_path: Path, result):
    """Save results to SQLite database."""
    with console.status(f"[bold green]Saving to database {db_path}..."):
        try:
            storage = SQLiteStorageAdapter(db_path=db_path)
            storage.save_run(result)
            console.print(f"[green]Results saved to database: {db_path}[/green]")
            console.print(f"[dim]Run ID: {result.run_id}[/dim]")
        except Exception as e:
            console.print(f"[red]Error saving to database:[/red] {e}")


def _save_results(output: Path, result):
    """Save results to JSON file."""
    import json

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
        except Exception as e:
            console.print(f"[red]Error saving results:[/red] {e}")


@kg_app.command("stats")
def kg_stats(
    source: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="단일 파일 또는 디렉터리. 디렉터리는 .txt/.md 파일을 재귀적으로 읽습니다.",
    ),
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="LLM 프로필 (필요 시).",
    ),
    use_llm: bool = typer.Option(
        False,
        "--use-llm",
        help="LLM 보강기를 사용해 저신뢰 관계를 검증합니다.",
    ),
    threshold: float = typer.Option(
        0.6,
        "--threshold",
        help="LLM 보강을 트리거할 confidence 임계값 (0~1).",
    ),
    log_langfuse: bool = typer.Option(
        True,
        "--langfuse/--no-langfuse",
        help="Langfuse에 그래프 통계를 기록할지 여부.",
    ),
    report_file: Path | None = typer.Option(
        None,
        "--report-file",
        help="그래프 통계를 JSON 파일로 저장.",
    ),
):
    """문서 집합으로 지식그래프를 구축하고 통계를 출력."""
    if not 0 < threshold <= 1:
        console.print("[red]Error:[/red] threshold는 0~1 사이여야 합니다.")
        raise typer.Exit(1)

    settings = Settings()
    profile_name = profile or settings.evalvault_profile
    if profile_name:
        settings = apply_profile(settings, profile_name)

    relation_augmenter = None
    if use_llm:
        if settings.llm_provider == "openai" and not settings.openai_api_key:
            console.print("[red]Error:[/red] OPENAI_API_KEY not set for LLM augmentation.")
            raise typer.Exit(1)
        relation_augmenter = LLMRelationAugmenter(get_llm_adapter(settings))

    try:
        documents = _load_documents_from_source(source)
    except Exception as exc:
        console.print(f"[red]Error loading documents:[/red] {exc}")
        raise typer.Exit(1)

    if not documents:
        console.print("[red]Error:[/red] 문서를 읽을 수 없습니다. 파일 내용을 확인하세요.")
        raise typer.Exit(1)

    console.print(f"[bold]Building knowledge graph from {len(documents)} documents...[/bold]")
    generator = KnowledgeGraphGenerator(
        relation_augmenter=relation_augmenter,
        low_confidence_threshold=threshold,
    )
    generator.build_graph(documents)
    stats = generator.get_statistics()
    _display_kg_stats(stats)
    if report_file:
        _save_kg_report(report_file, stats, source, profile_name, use_llm)
        console.print(f"[green]Saved KG report to {report_file}[/green]")

    trace_id = None
    if log_langfuse:
        trace_id = _log_kg_stats_to_langfuse(
            settings=settings,
            stats=stats,
            source=source,
            profile=profile_name,
            use_llm=use_llm,
        )
    if trace_id:
        console.print(f"[cyan]Langfuse trace ID:[/cyan] {trace_id}")


@app.command()
def metrics():
    """List available evaluation metrics."""
    console.print("\n[bold]Available Metrics[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Description")
    table.add_column("Requires Ground Truth", justify="center")

    table.add_row(
        "faithfulness",
        "Measures factual accuracy of the answer based on contexts",
        "[red]No[/red]",
    )
    table.add_row(
        "answer_relevancy",
        "Measures how relevant the answer is to the question",
        "[red]No[/red]",
    )
    table.add_row(
        "context_precision",
        "Measures ranking quality of retrieved contexts",
        "[green]Yes[/green]",
    )
    table.add_row(
        "context_recall",
        "Measures if all relevant info is in retrieved contexts",
        "[green]Yes[/green]",
    )
    table.add_row(
        "insurance_term_accuracy",
        "Measures if insurance terms in answer are grounded in contexts",
        "[red]No[/red]",
    )

    console.print(table)
    console.print("\n[dim]Use --metrics flag with 'run' command to specify metrics.[/dim]")
    console.print(
        "[dim]Example: evalvault run data.csv --metrics faithfulness,answer_relevancy[/dim]\n"
    )


@app.command("langfuse-dashboard")
def langfuse_dashboard(
    limit: int = typer.Option(5, help="표시할 Langfuse trace 개수"),
    event_type: str = typer.Option("ragas_evaluation", help="필터링할 event_type"),
):
    """Langfuse에서 평가/그래프 trace를 조회해 요약."""
    settings = Settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        console.print("[red]Langfuse credentials not configured.[/red]")
        raise typer.Exit(1)

    try:
        traces = _fetch_langfuse_traces(
            host=settings.langfuse_host,
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            event_type=event_type,
            limit=limit,
        )
    except HTTPError as exc:
        console.print(
            f"[yellow]Langfuse public API not available (HTTP {exc.code}). "
            "Skipping dashboard output.[/yellow]"
        )
        return
    except Exception as exc:
        console.print(f"[red]Failed to fetch Langfuse traces:[/red] {exc}")
        raise typer.Exit(1)

    if not traces:
        console.print("[yellow]No traces found for the given event_type.[/yellow]")
        return

    table = Table(
        title=f"Langfuse Traces ({event_type})", show_header=True, header_style="bold cyan"
    )
    table.add_column("Trace ID")
    table.add_column("Dataset")
    table.add_column("Model")
    table.add_column("Pass Rate", justify="right")
    table.add_column("Total Cases", justify="right")
    table.add_column("Created At")

    for trace in traces:
        metadata = trace.get("metadata", {})
        dataset_name = metadata.get("dataset_name") or metadata.get("source", "N/A")
        model_name = metadata.get("model_name", "N/A")
        pass_rate = metadata.get("pass_rate")
        total_cases = metadata.get("total_test_cases") or metadata.get("documents_processed")
        created_at = trace.get("createdAt") or trace.get("created_at", "")
        table.add_row(
            trace.get("id", "unknown"),
            str(dataset_name),
            str(model_name),
            f"{pass_rate:.2f}" if isinstance(pass_rate, int | float) else "N/A",
            str(total_cases) if total_cases is not None else "N/A",
            created_at,
        )

    console.print(table)


def _load_documents_from_source(source: Path) -> list[str]:
    """입력 경로에서 문서 리스트를 로드."""
    if source.is_dir():
        documents = []
        for path in sorted(source.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".txt", ".md"}:
                text = path.read_text(encoding="utf-8").strip()
                if text:
                    documents.append(text)
        return documents

    text = source.read_text(encoding="utf-8").strip()
    suffix = source.suffix.lower()

    if suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            pass
        else:
            documents: list[str] = []
            if isinstance(data, list):
                documents.extend(_extract_texts_from_sequence(data))
            elif isinstance(data, dict):
                documents.extend(_extract_texts_from_mapping(data))
            if documents:
                return documents

    if suffix in {".csv", ".tsv"}:
        return [line for line in text.splitlines() if line.strip()]

    paragraphs = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
    if len(paragraphs) > 1:
        return paragraphs
    return [text] if text else []


def _extract_texts_from_sequence(items) -> list[str]:
    """JSON 시퀀스에서 텍스트 필드 추출."""
    documents: list[str] = []
    for item in items:
        if isinstance(item, str):
            documents.append(item)
        elif isinstance(item, dict):
            for key in ("content", "text", "body"):
                value = item.get(key)
                if isinstance(value, str):
                    documents.append(value)
                    break
    return documents


def _extract_texts_from_mapping(data: dict) -> list[str]:
    """JSON 매핑에서 텍스트 필드 추출."""
    documents: list[str] = []
    for key in ("content", "text", "body"):
        value = data.get(key)
        if isinstance(value, str):
            documents.append(value)
    if "documents" in data and isinstance(data["documents"], list):
        documents.extend(_extract_texts_from_sequence(data["documents"]))
    return documents


def _display_kg_stats(stats: dict) -> None:
    """Rich 테이블로 그래프 통계를 출력."""
    summary = Table(title="Knowledge Graph Overview", show_header=False)
    summary.add_column("Metric", style="bold", justify="left")
    summary.add_column("Value", justify="right")

    summary.add_row("Entities", str(stats.get("num_entities", 0)))
    summary.add_row("Relations", str(stats.get("num_relations", 0)))
    isolated = stats.get("isolated_entities", [])
    summary.add_row("Isolated Entities", str(len(isolated)))

    build_metrics = stats.get("build_metrics", {})
    summary.add_row("Documents Processed", str(build_metrics.get("documents_processed", 0)))
    summary.add_row("Entities Added", str(build_metrics.get("entities_added", 0)))
    summary.add_row("Relations Added", str(build_metrics.get("relations_added", 0)))
    console.print(summary)

    if stats.get("entity_types"):
        entity_table = Table(title="Entity Types", show_header=True, header_style="bold cyan")
        entity_table.add_column("Type")
        entity_table.add_column("Count", justify="right")
        for entity_type, count in sorted(stats["entity_types"].items()):
            entity_table.add_row(entity_type, str(count))
        console.print(entity_table)

    if stats.get("relation_types"):
        relation_table = Table(title="Relation Types", show_header=True, header_style="bold cyan")
        relation_table.add_column("Type")
        relation_table.add_column("Count", justify="right")
        for relation_type, count in sorted(stats["relation_types"].items()):
            relation_table.add_row(relation_type, str(count))
        console.print(relation_table)

    if isolated:
        preview = ", ".join(isolated[:5])
        console.print(
            f"[yellow]Isolated entities ({len(isolated)}):[/yellow] "
            f"{preview}{'...' if len(isolated) > 5 else ''}"
        )

    if stats.get("sample_entities"):
        sample_table = Table(title="Sample Entities", show_header=True, header_style="bold magenta")
        sample_table.add_column("Name")
        sample_table.add_column("Type")
        sample_table.add_column("Confidence", justify="right")
        sample_table.add_column("Source")
        for entity in stats["sample_entities"]:
            sample_table.add_row(
                entity.get("name", ""),
                entity.get("entity_type", ""),
                f"{entity.get('confidence', 0):.2f}",
                entity.get("provenance", ""),
            )
        console.print(sample_table)

    if stats.get("sample_relations"):
        rel_table = Table(title="Sample Relations", show_header=True, header_style="bold magenta")
        rel_table.add_column("Source")
        rel_table.add_column("Relation")
        rel_table.add_column("Target")
        rel_table.add_column("Confidence", justify="right")
        for relation in stats["sample_relations"]:
            rel_table.add_row(
                relation.get("source", ""),
                relation.get("relation_type", ""),
                relation.get("target", ""),
                f"{relation.get('confidence', 0):.2f}",
            )
        console.print(rel_table)


def _log_kg_stats_to_langfuse(
    settings: Settings,
    stats: dict,
    source: Path,
    profile: str | None,
    use_llm: bool,
) -> str | None:
    """Langfuse에 그래프 통계를 전송."""
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        console.print("[yellow]Langfuse credentials not set; skipping logging.[/yellow]")
        return

    try:
        tracker = LangfuseAdapter(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        metadata = {
            "source": str(source),
            "profile": profile,
            "use_llm": use_llm,
            "num_entities": stats.get("num_entities"),
            "num_relations": stats.get("num_relations"),
            "documents_processed": stats.get("build_metrics", {}).get("documents_processed"),
            "event_type": "kg_stats",
        }
        trace_id = tracker.start_trace(name="kg_stats", metadata=metadata)
        payload = {
            "type": "kg_stats",
            "context": {
                "source": str(source),
                "profile": profile,
                "use_llm": use_llm,
            },
            "stats": stats,
        }
        tracker.save_artifact(trace_id, "kg_statistics", payload, artifact_type="json")
        tracker.add_span(
            trace_id=trace_id,
            name="entity_type_distribution",
            output_data=stats.get("entity_types"),
        )
        tracker.add_span(
            trace_id=trace_id,
            name="relation_type_distribution",
            output_data=stats.get("relation_types"),
        )
        if stats.get("isolated_entities"):
            tracker.add_span(
                trace_id=trace_id,
                name="isolated_entities",
                output_data=stats.get("isolated_entities"),
            )
        tracker.end_trace(trace_id)
        console.print("[green]Logged knowledge graph stats to Langfuse[/green]")
        return trace_id
    except Exception as exc:
        console.print(f"[yellow]Warning:[/yellow] Failed to log to Langfuse: {exc}")
        return None


def _save_kg_report(
    output: Path,
    stats: dict,
    source: Path,
    profile: str | None,
    use_llm: bool,
) -> None:
    """kg stats 결과를 JSON 파일로 저장."""
    payload = {
        "type": "kg_stats_report",
        "generated_at": datetime.now().isoformat(),
        "source": str(source),
        "profile": profile,
        "use_llm": use_llm,
        "stats": stats,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _fetch_langfuse_traces(
    host: str,
    public_key: str,
    secret_key: str,
    event_type: str,
    limit: int,
) -> list[dict]:
    """Langfuse Public API를 호출해 trace 리스트를 가져온다."""
    base = host.rstrip("/")
    url = f"{base}/api/public/traces/search"
    payload = {
        "query": {"metadata.event_type": {"equals": event_type}},
        "limit": limit,
        "orderBy": {"createdAt": "desc"},
    }
    auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode("utf-8")
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth}",
        },
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("data", data if isinstance(data, list) else [])


@app.command()
def config():
    """Show current configuration."""
    settings = Settings()

    # Apply profile if set
    profile_name = settings.evalvault_profile
    if profile_name:
        settings = apply_profile(settings, profile_name)

    console.print("\n[bold]Current Configuration[/bold]\n")

    # Profile section
    console.print("[bold cyan]Profile[/bold cyan]")
    table_profile = Table(show_header=False, box=None, padding=(0, 2))
    table_profile.add_column("Setting", style="bold")
    table_profile.add_column("Value")

    table_profile.add_row(
        "Active Profile",
        f"[cyan]{profile_name}[/cyan]" if profile_name else "[dim]None (using defaults)[/dim]",
    )
    table_profile.add_row("LLM Provider", settings.llm_provider)

    console.print(table_profile)
    console.print()

    # Provider-specific settings
    console.print("[bold cyan]LLM Settings[/bold cyan]")
    table_llm = Table(show_header=False, box=None, padding=(0, 2))
    table_llm.add_column("Setting", style="bold")
    table_llm.add_column("Value")

    if settings.llm_provider == "ollama":
        table_llm.add_row("Ollama Model", settings.ollama_model)
        table_llm.add_row("Ollama Embedding", settings.ollama_embedding_model)
        table_llm.add_row("Ollama URL", settings.ollama_base_url)
        table_llm.add_row("Ollama Timeout", f"{settings.ollama_timeout}s")
        if settings.ollama_think_level:
            table_llm.add_row("Think Level", settings.ollama_think_level)
    else:
        api_key_status = "[green]Set[/green]" if settings.openai_api_key else "[red]Not set[/red]"
        table_llm.add_row("OpenAI API Key", api_key_status)
        table_llm.add_row("OpenAI Model", settings.openai_model)
        table_llm.add_row("OpenAI Embedding", settings.openai_embedding_model)
        table_llm.add_row(
            "OpenAI Base URL",
            settings.openai_base_url or "[dim]Default[/dim]",
        )

    console.print(table_llm)
    console.print()

    # Langfuse settings
    console.print("[bold cyan]Tracking[/bold cyan]")
    table_tracking = Table(show_header=False, box=None, padding=(0, 2))
    table_tracking.add_column("Setting", style="bold")
    table_tracking.add_column("Value")

    langfuse_status = (
        "[green]Configured[/green]"
        if settings.langfuse_public_key and settings.langfuse_secret_key
        else "[yellow]Not configured[/yellow]"
    )
    table_tracking.add_row("Langfuse", langfuse_status)
    table_tracking.add_row("Langfuse Host", settings.langfuse_host)

    console.print(table_tracking)
    console.print()

    # Available profiles
    console.print("[bold cyan]Available Profiles[/bold cyan]")
    try:
        from evalvault.config.model_config import get_model_config

        model_config = get_model_config()
        table_profiles = Table(show_header=True, header_style="bold")
        table_profiles.add_column("Profile")
        table_profiles.add_column("LLM")
        table_profiles.add_column("Embedding")
        table_profiles.add_column("Description")

        for name, prof in model_config.profiles.items():
            is_active = name == profile_name
            prefix = "[cyan]* " if is_active else "  "
            suffix = "[/cyan]" if is_active else ""
            table_profiles.add_row(
                f"{prefix}{name}{suffix}",
                prof.llm.model,
                prof.embedding.model,
                prof.description,
            )

        console.print(table_profiles)
    except FileNotFoundError:
        console.print("[yellow]  config/models.yaml not found[/yellow]")

    console.print()
    console.print("[dim]Tip: Use --profile to override, e.g.:[/dim]")
    console.print("[dim]  evalvault run data.json --profile prod --metrics faithfulness[/dim]\n")


@app.command()
def generate(
    documents: list[Path] = typer.Argument(
        ...,
        help="Path(s) to document file(s) for testset generation.",
        exists=True,
        readable=True,
    ),
    num_questions: int = typer.Option(
        10,
        "--num",
        "-n",
        help="Number of test questions to generate.",
    ),
    method: str = typer.Option(
        "basic",
        "--method",
        "-m",
        help="Generation method: 'basic' or 'knowledge_graph'.",
    ),
    output: Path = typer.Option(
        "generated_testset.json",
        "--output",
        "-o",
        help="Output file for generated testset (JSON format).",
    ),
    chunk_size: int = typer.Option(
        500,
        "--chunk-size",
        help="Chunk size for document splitting.",
    ),
    name: str = typer.Option(
        "generated-testset",
        "--name",
        help="Dataset name.",
    ),
):
    """Generate test dataset from documents."""
    import json

    # Validate method
    if method not in ["basic", "knowledge_graph"]:
        console.print(f"[red]Error:[/red] Invalid method: {method}")
        console.print("Available methods: basic, knowledge_graph")
        raise typer.Exit(1)

    console.print("\n[bold]EvalVault[/bold] - Testset Generation")
    console.print(f"Documents: [cyan]{len(documents)}[/cyan]")
    console.print(f"Target questions: [cyan]{num_questions}[/cyan]")
    console.print(f"Method: [cyan]{method}[/cyan]\n")

    # Read documents
    with console.status("[bold green]Reading documents..."):
        doc_texts = []
        for doc_path in documents:
            with open(doc_path, encoding="utf-8") as f:
                doc_texts.append(f.read())
        console.print(f"[green]Loaded {len(doc_texts)} documents[/green]")

    # Generate testset based on method
    with console.status("[bold green]Generating testset..."):
        if method == "knowledge_graph":
            generator = KnowledgeGraphGenerator()
            generator.build_graph(doc_texts)

            # Show graph statistics
            stats = generator.get_statistics()
            console.print(
                f"[dim]Knowledge Graph: {stats['num_entities']} entities, {stats['num_relations']} relations[/dim]"
            )

            dataset = generator.generate_dataset(
                num_questions=num_questions,
                name=name,
                version="1.0.0",
            )
        else:  # basic method
            generator = BasicTestsetGenerator()
            config = GenerationConfig(
                num_questions=num_questions,
                chunk_size=chunk_size,
                dataset_name=name,
            )
            dataset = generator.generate(doc_texts, config)

        console.print(f"[green]Generated {len(dataset.test_cases)} test cases[/green]")

    # Save to file
    with console.status(f"[bold green]Saving to {output}..."):
        data = {
            "name": dataset.name,
            "version": dataset.version,
            "metadata": dataset.metadata,
            "test_cases": [
                {
                    "id": tc.id,
                    "question": tc.question,
                    "answer": tc.answer,
                    "contexts": tc.contexts,
                    "ground_truth": tc.ground_truth,
                    "metadata": tc.metadata,
                }
                for tc in dataset.test_cases
            ],
        }

        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        console.print(f"[green]Testset saved to {output}[/green]\n")


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
        "evalvault.db",
        "--db",
        help="Path to database file.",
    ),
):
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
    run_id1: str = typer.Argument(
        ...,
        help="First run ID to compare.",
    ),
    run_id2: str = typer.Argument(
        ...,
        help="Second run ID to compare.",
    ),
    db_path: Path = typer.Option(
        "evalvault.db",
        "--db",
        help="Path to database file.",
    ),
):
    """Compare two evaluation runs."""
    console.print("\n[bold]Comparing Evaluation Runs[/bold]\n")

    storage = SQLiteStorageAdapter(db_path=db_path)

    try:
        run1 = storage.get_run(run_id1)
        run2 = storage.get_run(run_id2)
    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    # Comparison table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    table.add_column(f"Run 1\n{run_id1[:12]}...", justify="right")
    table.add_column(f"Run 2\n{run_id2[:12]}...", justify="right")
    table.add_column("Difference", justify="right")

    # Basic metrics
    table.add_row(
        "Dataset",
        run1.dataset_name,
        run2.dataset_name,
        "-",
    )
    table.add_row(
        "Model",
        run1.model_name,
        run2.model_name,
        "-",
    )
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

    # Metric scores
    for metric in run1.metrics_evaluated:
        if metric in run2.metrics_evaluated:
            score1 = run1.get_avg_score(metric)
            score2 = run2.get_avg_score(metric)
            diff = score2 - score1 if score1 and score2 else None

            diff_str = f"[{diff_color}]{diff:+.3f}[/{diff_color}]" if diff else "-"
            table.add_row(
                f"Avg {metric}",
                f"{score1:.3f}" if score1 else "-",
                f"{score2:.3f}" if score2 else "-",
                diff_str,
            )

    console.print(table)
    console.print()


@app.command(name="export")
def export_cmd(
    run_id: str = typer.Argument(
        ...,
        help="Run ID to export.",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output file path (JSON format).",
    ),
    db_path: Path = typer.Option(
        "evalvault.db",
        "--db",
        help="Path to database file.",
    ),
):
    """Export evaluation run to JSON file."""
    import json

    console.print(f"\n[bold]Exporting Run {run_id}[/bold]\n")

    storage = SQLiteStorageAdapter(db_path=db_path)

    try:
        run = storage.get_run(run_id)
    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    # Prepare export data
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

        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        console.print(f"[green]Exported to {output}[/green]\n")


@app.command()
def experiment_create(
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Experiment name.",
    ),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Experiment description.",
    ),
    hypothesis: str = typer.Option(
        "",
        "--hypothesis",
        "-h",
        help="Experiment hypothesis.",
    ),
    metrics: str | None = typer.Option(
        None,
        "--metrics",
        "-m",
        help="Comma-separated list of metrics to compare.",
    ),
    db_path: Path = typer.Option(
        "evalvault.db",
        "--db",
        help="Path to database file.",
    ),
):
    """Create a new experiment for A/B testing."""
    console.print("\n[bold]Creating Experiment[/bold]\n")

    storage = SQLiteStorageAdapter(db_path=db_path)
    manager = ExperimentManager(storage)

    metric_list = [m.strip() for m in metrics.split(",")] if metrics else None

    experiment = manager.create_experiment(
        name=name,
        description=description,
        hypothesis=hypothesis,
        metrics=metric_list,
    )

    console.print(f"[green]Created experiment:[/green] {experiment.experiment_id}")
    console.print(f"  Name: {experiment.name}")
    console.print(f"  Status: {experiment.status}")
    if experiment.hypothesis:
        console.print(f"  Hypothesis: {experiment.hypothesis}")
    if experiment.metrics_to_compare:
        console.print(f"  Metrics: {', '.join(experiment.metrics_to_compare)}")
    console.print()


@app.command()
def experiment_add_group(
    experiment_id: str = typer.Option(
        ...,
        "--id",
        help="Experiment ID.",
    ),
    group_name: str = typer.Option(
        ...,
        "--group",
        "-g",
        help="Group name (e.g., control, variant_a).",
    ),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Group description.",
    ),
    db_path: Path = typer.Option(
        "evalvault.db",
        "--db",
        help="Path to database file.",
    ),
):
    """Add a group to an experiment."""
    storage = SQLiteStorageAdapter(db_path=db_path)
    manager = ExperimentManager(storage)

    try:
        manager.add_group_to_experiment(experiment_id, group_name, description)
        console.print(f"[green]Added group '{group_name}' to experiment {experiment_id}[/green]\n")
    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def experiment_add_run(
    experiment_id: str = typer.Option(
        ...,
        "--id",
        help="Experiment ID.",
    ),
    group_name: str = typer.Option(
        ...,
        "--group",
        "-g",
        help="Group name.",
    ),
    run_id: str = typer.Option(
        ...,
        "--run",
        "-r",
        help="Run ID to add to the group.",
    ),
    db_path: Path = typer.Option(
        "evalvault.db",
        "--db",
        help="Path to database file.",
    ),
):
    """Add an evaluation run to an experiment group."""
    storage = SQLiteStorageAdapter(db_path=db_path)
    manager = ExperimentManager(storage)

    try:
        manager.add_run_to_experiment_group(experiment_id, group_name, run_id)
        console.print(
            f"[green]Added run {run_id} to group '{group_name}' in experiment {experiment_id}[/green]\n"
        )
    except (KeyError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def experiment_list(
    status: str | None = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status (draft, running, completed, archived).",
    ),
    db_path: Path = typer.Option(
        "evalvault.db",
        "--db",
        help="Path to database file.",
    ),
):
    """List all experiments."""
    console.print("\n[bold]Experiments[/bold]\n")

    storage = SQLiteStorageAdapter(db_path=db_path)
    manager = ExperimentManager(storage)

    experiments = manager.list_experiments(status=status)

    if not experiments:
        console.print("[yellow]No experiments found.[/yellow]\n")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Experiment ID", style="dim")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Groups", justify="right")
    table.add_column("Created At")

    for exp in experiments:
        status_color = {
            "draft": "yellow",
            "running": "blue",
            "completed": "green",
            "archived": "dim",
        }.get(exp.status, "white")

        table.add_row(
            exp.experiment_id[:12] + "...",
            exp.name,
            f"[{status_color}]{exp.status}[/{status_color}]",
            str(len(exp.groups)),
            exp.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)
    console.print(f"\n[dim]Showing {len(experiments)} experiments[/dim]\n")


@app.command()
def experiment_compare(
    experiment_id: str = typer.Option(
        ...,
        "--id",
        help="Experiment ID.",
    ),
    db_path: Path = typer.Option(
        "evalvault.db",
        "--db",
        help="Path to database file.",
    ),
):
    """Compare groups in an experiment."""
    console.print("\n[bold]Experiment Comparison[/bold]\n")

    storage = SQLiteStorageAdapter(db_path=db_path)
    manager = ExperimentManager(storage)

    try:
        experiment = manager.get_experiment(experiment_id)
        comparisons = manager.compare_groups(experiment_id)

        if not comparisons:
            console.print("[yellow]No comparison data available.[/yellow]")
            console.print("Make sure groups have evaluation runs added.\n")
            return

        # Summary
        console.print(f"[bold]{experiment.name}[/bold]")
        if experiment.hypothesis:
            console.print(f"Hypothesis: [dim]{experiment.hypothesis}[/dim]")
        console.print()

        # Comparison table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="bold")

        # Add columns for each group
        for group in experiment.groups:
            table.add_column(group.name, justify="right")

        table.add_column("Best Group", justify="center")
        table.add_column("Improvement", justify="right")

        for comp in comparisons:
            row = [comp.metric_name]

            # Add scores for each group
            for group in experiment.groups:
                score = comp.group_scores.get(group.name)
                if score is not None:
                    color = "green" if group.name == comp.best_group else "white"
                    row.append(f"[{color}]{score:.3f}[/{color}]")
                else:
                    row.append("-")

            # Best group and improvement
            row.append(f"[green]{comp.best_group}[/green]")
            row.append(f"[cyan]{comp.improvement:+.1f}%[/cyan]")

            table.add_row(*row)

        console.print(table)
        console.print()

    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def experiment_conclude(
    experiment_id: str = typer.Option(
        ...,
        "--id",
        help="Experiment ID.",
    ),
    conclusion: str = typer.Option(
        ...,
        "--conclusion",
        "-c",
        help="Experiment conclusion.",
    ),
    db_path: Path = typer.Option(
        "evalvault.db",
        "--db",
        help="Path to database file.",
    ),
):
    """Conclude an experiment and record findings."""
    storage = SQLiteStorageAdapter(db_path=db_path)
    manager = ExperimentManager(storage)

    try:
        manager.conclude_experiment(experiment_id, conclusion)
        console.print(f"[green]Experiment {experiment_id} concluded.[/green]")
        console.print(f"Conclusion: {conclusion}\n")
    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def experiment_summary(
    experiment_id: str = typer.Option(
        ...,
        "--id",
        help="Experiment ID.",
    ),
    db_path: Path = typer.Option(
        "evalvault.db",
        "--db",
        help="Path to database file.",
    ),
):
    """Show experiment summary."""
    storage = SQLiteStorageAdapter(db_path=db_path)
    manager = ExperimentManager(storage)

    try:
        summary = manager.get_summary(experiment_id)

        # Display summary
        console.print(f"\n[bold]{summary['name']}[/bold]")
        console.print(f"ID: [dim]{summary['experiment_id']}[/dim]")
        console.print(f"Status: [{summary['status']}]{summary['status']}[/{summary['status']}]")
        console.print(f"Created: {summary['created_at']}")

        if summary["description"]:
            console.print(f"\n[bold]Description:[/bold]\n{summary['description']}")

        if summary["hypothesis"]:
            console.print(f"\n[bold]Hypothesis:[/bold]\n{summary['hypothesis']}")

        if summary["metrics_to_compare"]:
            console.print("\n[bold]Metrics to Compare:[/bold]")
            console.print(f"  {', '.join(summary['metrics_to_compare'])}")

        console.print("\n[bold]Groups:[/bold]")
        for group_name, group_data in summary["groups"].items():
            console.print(f"\n  [cyan]{group_name}[/cyan]")
            if group_data["description"]:
                console.print(f"    Description: {group_data['description']}")
            console.print(f"    Runs: {group_data['num_runs']}")
            if group_data["run_ids"]:
                for run_id in group_data["run_ids"]:
                    console.print(f"      - {run_id}")

        if summary["conclusion"]:
            console.print(f"\n[bold]Conclusion:[/bold]\n{summary['conclusion']}")

        console.print()

    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# Domain Memory Commands


@domain_app.command("init")
def domain_init(
    domain: str = typer.Argument(..., help="Domain name (e.g., 'insurance', 'medical')"),
    languages: str = typer.Option(
        "ko,en",
        "--languages",
        "-l",
        help="Supported languages (comma-separated)",
    ),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Domain description",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing config",
    ),
):
    """Initialize domain memory configuration.

    Creates a new domain configuration with memory.yaml and
    template term dictionaries for each language.

    Example:
        evalvault domain init insurance --languages ko,en
        evalvault domain init medical -l ko -d "의료 도메인"
    """
    lang_list = [lang.strip() for lang in languages.split(",")]

    # Validate languages
    valid_languages = {"ko", "en"}
    invalid_langs = [lang for lang in lang_list if lang not in valid_languages]
    if invalid_langs:
        console.print(f"[red]Error:[/red] Invalid languages: {', '.join(invalid_langs)}")
        console.print(f"Supported languages: {', '.join(valid_languages)}")
        raise typer.Exit(1)

    # Check if domain already exists
    config_dir = Path("config/domains")
    domain_dir = config_dir / domain

    if domain_dir.exists() and not force:
        console.print(f"[yellow]Domain '{domain}' already exists.[/yellow]")
        console.print("Use --force to overwrite.")
        raise typer.Exit(1)

    console.print(f"\n[bold]Initializing domain:[/bold] {domain}")
    console.print(f"Languages: [cyan]{', '.join(lang_list)}[/cyan]")
    if description:
        console.print(f"Description: [dim]{description}[/dim]")
    console.print()

    # Generate and save config
    with console.status("[bold green]Creating domain configuration..."):
        template = generate_domain_template(
            domain=domain,
            languages=lang_list,
            description=description,
        )
        config_path = save_domain_config(domain, template, config_dir)

        # Create empty term dictionaries for each language
        for lang in lang_list:
            terms_file = domain_dir / f"terms_dictionary_{lang}.json"
            if not terms_file.exists():
                terms_template = {
                    "version": "1.0.0",
                    "language": lang,
                    "domain": domain,
                    "description": f"{domain.capitalize()} domain {lang} terminology",
                    "terms": {},
                    "categories": {},
                }
                with open(terms_file, "w", encoding="utf-8") as f:
                    json.dump(terms_template, f, indent=2, ensure_ascii=False)

    console.print(f"[green]Domain '{domain}' initialized successfully.[/green]")
    console.print("\n[bold]Created files:[/bold]")
    console.print(f"  Config: {config_path}")
    for lang in lang_list:
        console.print(f"  Terms ({lang}): {domain_dir / f'terms_dictionary_{lang}.json'}")

    console.print("\n[dim]Next steps:[/dim]")
    console.print(f"  1. Edit {config_path} to customize settings")
    console.print("  2. Add terms to terms_dictionary_*.json files")
    console.print(f"  3. Use 'evalvault domain show {domain}' to view config\n")


@domain_app.command("list")
def domain_list():
    """List all configured domains.

    Shows all domains with memory.yaml configuration files.
    """
    console.print("\n[bold]Configured Domains[/bold]\n")

    domains = list_domains()

    if not domains:
        console.print("[yellow]No domains configured.[/yellow]")
        console.print("[dim]Use 'evalvault domain init <name>' to create one.[/dim]\n")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Domain", style="bold")
    table.add_column("Languages")
    table.add_column("Learning")
    table.add_column("Description")

    for domain_name in domains:
        try:
            config = load_domain_config(domain_name)
            langs = ", ".join(config.metadata.supported_languages)
            learning = (
                "[green]Enabled[/green]" if config.learning.enabled else "[dim]Disabled[/dim]"
            )
            desc = (
                config.metadata.description[:40] + "..."
                if len(config.metadata.description) > 40
                else config.metadata.description
            )
            table.add_row(domain_name, langs, learning, desc)
        except Exception as e:
            table.add_row(domain_name, "[red]Error[/red]", "-", str(e)[:30])

    console.print(table)
    console.print(f"\n[dim]Found {len(domains)} domain(s)[/dim]\n")


@domain_app.command("show")
def domain_show(
    domain: str = typer.Argument(..., help="Domain name to show"),
):
    """Show domain configuration details.

    Displays the full configuration for a domain including
    memory layers and learning settings.
    """
    console.print(f"\n[bold]Domain Configuration: {domain}[/bold]\n")

    try:
        config = load_domain_config(domain)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Domain '{domain}' not found.")
        console.print(f"[dim]Use 'evalvault domain init {domain}' to create it.[/dim]\n")
        raise typer.Exit(1)

    # Metadata section
    console.print("[bold cyan]Metadata[/bold cyan]")
    table_meta = Table(show_header=False, box=None, padding=(0, 2))
    table_meta.add_column("Setting", style="bold")
    table_meta.add_column("Value")

    table_meta.add_row("Domain", config.metadata.domain)
    table_meta.add_row("Version", config.metadata.version)
    table_meta.add_row("Languages", ", ".join(config.metadata.supported_languages))
    table_meta.add_row("Default Language", config.metadata.default_language)
    table_meta.add_row("Description", config.metadata.description or "[dim]None[/dim]")

    console.print(table_meta)
    console.print()

    # Factual Layer section
    console.print("[bold cyan]Factual Layer[/bold cyan]")
    table_factual = Table(show_header=False, box=None, padding=(0, 2))
    table_factual.add_column("Setting", style="bold")
    table_factual.add_column("Value")

    for lang in config.metadata.supported_languages:
        glossary = config.factual.glossary.get(lang)
        if glossary:
            table_factual.add_row(f"Glossary ({lang})", glossary)

    if config.factual.shared:
        for name, path in config.factual.shared.items():
            table_factual.add_row(f"Shared ({name})", path)

    console.print(table_factual)
    console.print()

    # Experiential Layer section
    console.print("[bold cyan]Experiential Layer[/bold cyan]")
    table_exp = Table(show_header=False, box=None, padding=(0, 2))
    table_exp.add_column("Setting", style="bold")
    table_exp.add_column("Value")

    table_exp.add_row("Failure Modes", config.experiential.failure_modes)
    table_exp.add_row("Behavior Handbook", config.experiential.behavior_handbook)

    for lang in config.metadata.supported_languages:
        rel_path = config.experiential.reliability_scores.get(lang)
        if rel_path:
            table_exp.add_row(f"Reliability ({lang})", rel_path)

    console.print(table_exp)
    console.print()

    # Working Layer section
    console.print("[bold cyan]Working Layer[/bold cyan]")
    table_work = Table(show_header=False, box=None, padding=(0, 2))
    table_work.add_column("Setting", style="bold")
    table_work.add_column("Value")

    table_work.add_row("Run Cache", config.working.run_cache)
    table_work.add_row("KG Binding", config.working.kg_binding or "[dim]None[/dim]")
    table_work.add_row("Max Cache Size", f"{config.working.max_cache_size_mb} MB")

    console.print(table_work)
    console.print()

    # Learning section
    console.print("[bold cyan]Learning Settings[/bold cyan]")
    table_learn = Table(show_header=False, box=None, padding=(0, 2))
    table_learn.add_column("Setting", style="bold")
    table_learn.add_column("Value")

    status = "[green]Enabled[/green]" if config.learning.enabled else "[red]Disabled[/red]"
    table_learn.add_row("Status", status)
    table_learn.add_row("Min Confidence", f"{config.learning.min_confidence_to_store:.2f}")
    table_learn.add_row(
        "Behavior Extraction", "Yes" if config.learning.behavior_extraction else "No"
    )
    table_learn.add_row("Auto Apply", "Yes" if config.learning.auto_apply else "No")
    table_learn.add_row("Decay Rate", f"{config.learning.decay_rate:.2f}")
    table_learn.add_row("Forget Threshold", f"{config.learning.forget_threshold_days} days")

    console.print(table_learn)
    console.print()


@domain_app.command("terms")
def domain_terms(
    domain: str = typer.Argument(..., help="Domain name"),
    language: str = typer.Option(
        None,
        "--language",
        "-l",
        help="Language code (ko, en). Uses default if not specified.",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Number of terms to show",
    ),
):
    """Show domain terminology dictionary.

    Displays terms from the domain's terminology dictionary
    for the specified language.
    """
    try:
        config = load_domain_config(domain)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Domain '{domain}' not found.")
        raise typer.Exit(1)

    lang = language or config.metadata.default_language

    if not config.supports_language(lang):
        console.print(f"[red]Error:[/red] Language '{lang}' not supported by domain '{domain}'.")
        console.print(f"Supported: {', '.join(config.metadata.supported_languages)}")
        raise typer.Exit(1)

    glossary_path = config.get_glossary_path(lang)
    if not glossary_path:
        console.print(f"[yellow]No glossary configured for language '{lang}'[/yellow]")
        raise typer.Exit(1)

    config_dir = Path("config/domains")
    terms_file = config_dir / domain / glossary_path

    if not terms_file.exists():
        console.print(f"[yellow]Glossary file not found:[/yellow] {terms_file}")
        raise typer.Exit(1)

    with open(terms_file, encoding="utf-8") as f:
        terms_data = json.load(f)

    console.print(f"\n[bold]Terminology Dictionary: {domain} ({lang})[/bold]\n")

    terms = terms_data.get("terms", {})
    if not terms:
        console.print("[yellow]No terms defined.[/yellow]\n")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Term", style="bold")
    table.add_column("Definition")
    table.add_column("Category")
    table.add_column("Aliases")

    for count, (term, info) in enumerate(terms.items()):
        if count >= limit:
            break
        definition = info.get("definition", "")
        if len(definition) > 50:
            definition = definition[:50] + "..."
        category = info.get("category", "-")
        aliases = ", ".join(info.get("aliases", [])[:2])
        if len(info.get("aliases", [])) > 2:
            aliases += "..."

        table.add_row(term, definition, category, aliases)

    console.print(table)

    total = len(terms)
    if total > limit:
        console.print(f"\n[dim]Showing {limit} of {total} terms. Use --limit to show more.[/dim]")
    console.print()


# ============================================================================
# Analysis Commands
# ============================================================================


@app.command()
def gate(
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
    db_path: Path = typer.Option("evalvault.db", "--db", help="Database path"),
):
    """Quality gate check for CI/CD pipelines.

    Checks if evaluation results meet thresholds and detects regressions.

    Exit codes:
      0 - All checks passed
      1 - Threshold check failed
      2 - Regression detected (when --baseline is specified)
      3 - Run not found

    Examples:
        evalvault gate abc123
        evalvault gate abc123 -t faithfulness:0.8 -t context_precision:0.7
        evalvault gate abc123 --baseline baseline123 --fail-on-regression 0.03
        evalvault gate abc123 --format github-actions
        evalvault gate abc123 --format json
    """
    storage = SQLiteStorageAdapter(db_path=db_path)

    # Load run
    try:
        run = storage.get_run(run_id)
    except KeyError:
        if output_format == "json":
            import json

            console.print(json.dumps({"status": "error", "message": f"Run not found: {run_id}"}))
        elif output_format == "github-actions":
            console.print(f"::error::Run not found: {run_id}")
        else:
            console.print(f"[red]Error: Run not found: {run_id}[/red]")
        raise typer.Exit(3)

    # Parse custom thresholds
    custom_thresholds = {}
    if threshold:
        for t in threshold:
            if ":" not in t:
                console.print(f"[red]Error: Invalid threshold format: {t}[/red]")
                console.print("[dim]Use format: metric:value (e.g., faithfulness:0.8)[/dim]")
                raise typer.Exit(1)
            metric, value = t.split(":", 1)
            try:
                custom_thresholds[metric.strip()] = float(value.strip())
            except ValueError:
                console.print(f"[red]Error: Invalid threshold value: {value}[/red]")
                raise typer.Exit(1)

    # Merge thresholds (custom > run > default)
    thresholds = dict.fromkeys(run.metrics_evaluated, 0.7)
    thresholds.update(run.thresholds or {})
    thresholds.update(custom_thresholds)

    # Load baseline if specified
    baseline_run = None
    if baseline:
        try:
            baseline_run = storage.get_run(baseline)
        except KeyError:
            if output_format == "json":
                import json

                console.print(
                    json.dumps(
                        {"status": "error", "message": f"Baseline run not found: {baseline}"}
                    )
                )
            elif output_format == "github-actions":
                console.print(f"::error::Baseline run not found: {baseline}")
            else:
                console.print(f"[red]Error: Baseline run not found: {baseline}[/red]")
            raise typer.Exit(3)

    # Check thresholds
    results = []
    all_passed = True
    regression_detected = False

    for metric in run.metrics_evaluated:
        avg_score = run.get_avg_score(metric)
        thresh = thresholds.get(metric, 0.7)
        passed = avg_score >= thresh

        result = {
            "metric": metric,
            "score": avg_score,
            "threshold": thresh,
            "passed": passed,
        }

        if not passed:
            all_passed = False

        # Check regression if baseline exists
        if baseline_run and metric in baseline_run.metrics_evaluated:
            baseline_score = baseline_run.get_avg_score(metric)
            diff = avg_score - baseline_score
            result["baseline_score"] = baseline_score
            result["diff"] = diff
            result["regression"] = diff < -fail_on_regression

            if result["regression"]:
                regression_detected = True

        results.append(result)

    # Output results
    if output_format == "json":
        import json

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
        console.print(json.dumps(output_data, indent=2))

    elif output_format == "github-actions":
        # GitHub Actions output format
        for r in results:
            status = "✅" if r["passed"] else "❌"
            reg_status = ""
            if "regression" in r:
                reg_status = " (📉 REGRESSION)" if r["regression"] else ""
            console.print(
                f"{status} {r['metric']}: {r['score']:.3f} (threshold: {r['threshold']:.2f}){reg_status}"
            )

        # Set output variables
        console.print(
            f"::set-output name=passed::{str(all_passed and not regression_detected).lower()}"
        )
        console.print(f"::set-output name=pass_rate::{run.pass_rate:.3f}")

        if not all_passed:
            failed_metrics = [r["metric"] for r in results if not r["passed"]]
            console.print(
                f"::error::Quality gate failed. Metrics below threshold: {', '.join(failed_metrics)}"
            )

        if regression_detected:
            regressed_metrics = [r["metric"] for r in results if r.get("regression")]
            console.print(f"::warning::Regression detected in: {', '.join(regressed_metrics)}")

    else:  # table format
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

        for r in results:
            status = "[green]PASS[/green]" if r["passed"] else "[red]FAIL[/red]"
            score_color = "green" if r["passed"] else "red"

            if baseline_run:
                baseline_score = r.get("baseline_score", "-")
                diff = r.get("diff", 0)
                diff_str = (
                    f"[{'green' if diff >= 0 else 'red'}]{diff:+.3f}[/]"
                    if isinstance(diff, float)
                    else "-"
                )
                reg_status = "[red]YES[/red]" if r.get("regression") else "[green]NO[/green]"
                table.add_row(
                    r["metric"],
                    f"[{score_color}]{r['score']:.3f}[/{score_color}]",
                    f"{r['threshold']:.2f}",
                    status,
                    f"{baseline_score:.3f}"
                    if isinstance(baseline_score, float)
                    else baseline_score,
                    diff_str,
                    reg_status,
                )
            else:
                table.add_row(
                    r["metric"],
                    f"[{score_color}]{r['score']:.3f}[/{score_color}]",
                    f"{r['threshold']:.2f}",
                    status,
                )

        console.print(table)

        # Summary
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

    # Exit with appropriate code
    if not all_passed:
        raise typer.Exit(1)
    if regression_detected:
        raise typer.Exit(2)


@app.command()
def analyze(
    run_id: str = typer.Argument(..., help="Run ID to analyze"),
    nlp: bool = typer.Option(False, "--nlp", help="Include NLP analysis"),
    causal: bool = typer.Option(False, "--causal", help="Include causal analysis"),
    playbook: bool = typer.Option(
        False, "--playbook", help="Include playbook-based improvement analysis"
    ),
    enable_llm: bool = typer.Option(
        False, "--enable-llm", help="Enable LLM-based insight generation for playbook analysis"
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output JSON file"),
    report: Path | None = typer.Option(
        None, "--report", "-r", help="Output report file (*.md or *.html)"
    ),
    save: bool = typer.Option(False, "--save", help="Save analysis to database"),
    db_path: Path = typer.Option("evalvault.db", "--db", help="Database path"),
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="Model profile for NLP embeddings (dev, prod, openai)",
    ),
):
    """Analyze an evaluation run and show statistical insights.

    Examples:
        evalvault analyze abc123
        evalvault analyze abc123 --nlp --profile dev
        evalvault analyze abc123 --causal
        evalvault analyze abc123 --nlp --causal
        evalvault analyze abc123 --playbook
        evalvault analyze abc123 --playbook --enable-llm
        evalvault analyze abc123 --output analysis.json
        evalvault analyze abc123 --report report.md
        evalvault analyze abc123 --nlp --causal --report report.html
        evalvault analyze abc123 --playbook --report improvement.md
        evalvault analyze abc123 --save --db evalvault.db
    """
    storage = SQLiteStorageAdapter(db_path=db_path)

    try:
        run = storage.get_run(run_id)
    except KeyError:
        console.print(f"[red]Error: Run not found: {run_id}[/red]")
        raise typer.Exit(1)

    if not run.results:
        console.print("[yellow]Warning: No test case results to analyze.[/yellow]")
        raise typer.Exit(0)

    # Create analysis service
    analysis_adapter = StatisticalAnalysisAdapter()
    cache_adapter = MemoryCacheAdapter()

    # Create NLP adapter if requested
    nlp_adapter = None
    if nlp:
        settings = Settings()
        profile_name = profile or settings.evalvault_profile
        if profile_name:
            settings = apply_profile(settings, profile_name)

        # Get LLM adapter for embeddings
        llm_adapter = get_llm_adapter(settings)
        nlp_adapter = NLPAnalysisAdapter(
            llm_adapter=llm_adapter,
            use_embeddings=True,
        )

    # Create causal adapter if requested
    causal_adapter = None
    if causal:
        causal_adapter = CausalAnalysisAdapter()

    service = AnalysisService(
        analysis_adapter=analysis_adapter,
        nlp_adapter=nlp_adapter,
        causal_adapter=causal_adapter,
        cache_adapter=cache_adapter,
    )

    # Perform analysis
    console.print(f"\n[bold]Analyzing run: {run_id}[/bold]\n")
    bundle = service.analyze_run(run, include_nlp=nlp, include_causal=causal)

    if not bundle.statistical:
        console.print("[yellow]No statistical analysis available.[/yellow]")
        raise typer.Exit(0)

    analysis = bundle.statistical

    # Display results
    _display_analysis_summary(analysis)
    _display_metric_stats(analysis)
    _display_correlations(analysis)
    _display_low_performers(analysis)
    _display_insights(analysis)

    # Display NLP analysis if available
    if bundle.has_nlp and bundle.nlp:
        _display_nlp_analysis(bundle.nlp)

    # Display causal analysis if available
    if bundle.has_causal and bundle.causal:
        _display_causal_analysis(bundle.causal)

    # Perform playbook-based improvement analysis if requested
    improvement_report = None
    if playbook:
        improvement_report = _perform_playbook_analysis(run, enable_llm, profile)

    # Save to database if requested
    if save:
        storage.save_analysis(analysis)
        console.print(f"\n[green]Analysis saved to database: {db_path}[/green]")

    # Export to JSON if requested
    if output:
        _export_analysis_json(analysis, output, bundle.nlp if nlp else None, improvement_report)
        console.print(f"\n[green]Analysis exported to: {output}[/green]")

    # Generate report if requested
    if report:
        _generate_report(bundle, report, include_nlp=nlp, improvement_report=improvement_report)
        console.print(f"\n[green]Report generated: {report}[/green]")


@app.command(name="analyze-compare")
def analyze_compare(
    run_id1: str = typer.Argument(..., help="First run ID"),
    run_id2: str = typer.Argument(..., help="Second run ID"),
    metrics: str | None = typer.Option(
        None, "--metrics", "-m", help="Comma-separated metrics to compare"
    ),
    test: str = typer.Option(
        "t-test", "--test", "-t", help="Statistical test (t-test, mann-whitney)"
    ),
    db_path: Path = typer.Option("evalvault.db", "--db", help="Database path"),
):
    """Compare two evaluation runs statistically.

    Examples:
        evalvault analyze-compare run1 run2
        evalvault analyze-compare run1 run2 --metrics faithfulness,answer_relevancy
        evalvault analyze-compare run1 run2 --test mann-whitney
    """
    storage = SQLiteStorageAdapter(db_path=db_path)

    try:
        run_a = storage.get_run(run_id1)
        run_b = storage.get_run(run_id2)
    except KeyError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    # Parse metrics
    metric_list = None
    if metrics:
        metric_list = [m.strip() for m in metrics.split(",")]

    # Create analysis service
    analysis_adapter = StatisticalAnalysisAdapter()
    service = AnalysisService(analysis_adapter)

    # Perform comparison
    console.print("\n[bold]Comparing runs:[/bold]")
    console.print(f"  Run A: {run_id1}")
    console.print(f"  Run B: {run_id2}")
    console.print(f"  Test: {test}\n")

    comparisons = service.compare_runs(run_a, run_b, metrics=metric_list, test_type=test)

    if not comparisons:
        console.print("[yellow]No common metrics to compare.[/yellow]")
        raise typer.Exit(0)

    # Display comparison table
    table = Table(title="Statistical Comparison", show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Run A (Mean)", justify="right")
    table.add_column("Run B (Mean)", justify="right")
    table.add_column("Diff (%)", justify="right")
    table.add_column("p-value", justify="right")
    table.add_column("Effect Size", justify="right")
    table.add_column("Significant")
    table.add_column("Winner")

    for c in comparisons:
        sig_style = "green" if c.is_significant else "dim"
        winner = c.winner[:8] if c.winner else "-"

        table.add_row(
            c.metric,
            f"{c.mean_a:.3f}",
            f"{c.mean_b:.3f}",
            f"{c.diff_percent:+.1f}%",
            f"{c.p_value:.4f}",
            f"{c.effect_size:.2f} ({c.effect_level.value})",
            f"[{sig_style}]{'Yes' if c.is_significant else 'No'}[/{sig_style}]",
            winner,
        )

    console.print(table)
    console.print()


def _display_analysis_summary(analysis) -> None:
    """Display analysis summary panel."""
    panel = Panel(
        f"""[bold]Analysis Summary[/bold]
Run ID: {analysis.run_id}
Analysis Type: {analysis.analysis_type.value}
Created: {analysis.created_at.strftime("%Y-%m-%d %H:%M:%S")}

Overall Pass Rate: [{"green" if analysis.overall_pass_rate >= 0.7 else "yellow" if analysis.overall_pass_rate >= 0.5 else "red"}]{analysis.overall_pass_rate:.1%}[/]
Metrics Analyzed: {len(analysis.metrics_summary)}
Significant Correlations: {len(analysis.significant_correlations)}
Low Performers Found: {len(analysis.low_performers)}""",
        title="[bold cyan]Statistical Analysis[/bold cyan]",
        border_style="cyan",
    )
    console.print(panel)


def _display_metric_stats(analysis) -> None:
    """Display metric statistics table."""
    if not analysis.metrics_summary:
        return

    table = Table(title="Metric Statistics", show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Mean", justify="right")
    table.add_column("Std", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Median", justify="right")
    table.add_column("Pass Rate", justify="right")

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

    console.print(table)
    console.print()


def _display_correlations(analysis) -> None:
    """Display significant correlations."""
    if not analysis.significant_correlations:
        return

    console.print("[bold]Significant Correlations:[/bold]")
    for corr in analysis.significant_correlations[:5]:  # Top 5
        direction = "[green]+" if corr.correlation > 0 else "[red]-"
        console.print(
            f"  {direction}{abs(corr.correlation):.2f}[/] "
            f"{corr.variable1} ↔ {corr.variable2} "
            f"(p={corr.p_value:.4f}, {corr.interpretation})"
        )
    console.print()


def _display_low_performers(analysis) -> None:
    """Display low performing test cases."""
    if not analysis.low_performers:
        return

    console.print(f"[bold]Low Performing Test Cases ({len(analysis.low_performers)}):[/bold]")

    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("Test Case")
    table.add_column("Metric")
    table.add_column("Score", justify="right")
    table.add_column("Threshold", justify="right")
    table.add_column("Potential Causes")

    for lp in analysis.low_performers[:10]:  # Top 10
        causes = ", ".join(lp.potential_causes[:2]) if lp.potential_causes else "-"
        table.add_row(
            lp.test_case_id[:12] + "..." if len(lp.test_case_id) > 15 else lp.test_case_id,
            lp.metric_name,
            f"[red]{lp.score:.3f}[/red]",
            f"{lp.threshold:.2f}",
            causes[:40] + "..." if len(causes) > 40 else causes,
        )

    console.print(table)
    console.print()


def _display_insights(analysis) -> None:
    """Display analysis insights."""
    if not analysis.insights:
        return

    console.print("[bold]Insights:[/bold]")
    for insight in analysis.insights:
        console.print(f"  • {insight}")
    console.print()


def _display_nlp_analysis(nlp_analysis) -> None:
    """Display NLP analysis results."""
    console.print("\n[bold cyan]NLP Analysis[/bold cyan]\n")

    # Text Statistics
    if nlp_analysis.question_stats:
        console.print("[bold]Text Statistics (Questions):[/bold]")
        stats = nlp_analysis.question_stats
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Total Characters", str(stats.char_count))
        table.add_row("Total Words", str(stats.word_count))
        table.add_row("Total Sentences", str(stats.sentence_count))
        table.add_row("Avg Word Length", f"{stats.avg_word_length:.2f}")
        table.add_row("Vocabulary Diversity", f"{stats.unique_word_ratio:.1%}")
        table.add_row("Avg Sentence Length", f"{stats.avg_sentence_length:.1f} words")

        console.print(table)
        console.print()

    # Question Types
    if nlp_analysis.question_types:
        console.print("[bold]Question Type Distribution:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Type")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")
        table.add_column("Avg Scores")

        for qt in nlp_analysis.question_types:
            avg_scores_str = ", ".join(f"{k}: {v:.2f}" for k, v in (qt.avg_scores or {}).items())
            table.add_row(
                qt.question_type.value.capitalize(),
                str(qt.count),
                f"{qt.percentage:.1%}",
                avg_scores_str or "-",
            )

        console.print(table)
        console.print()

    # Keywords
    if nlp_analysis.top_keywords:
        console.print("[bold]Top Keywords:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Keyword")
        table.add_column("Frequency", justify="right")
        table.add_column("TF-IDF Score", justify="right")

        for kw in nlp_analysis.top_keywords[:10]:  # Show top 10
            table.add_row(
                kw.keyword,
                str(kw.frequency),
                f"{kw.tfidf_score:.3f}",
            )

        console.print(table)
        console.print()

    # NLP Insights
    if nlp_analysis.insights:
        console.print("[bold]NLP Insights:[/bold]")
        for insight in nlp_analysis.insights:
            console.print(f"  • {insight}")
        console.print()


def _display_causal_analysis(causal_analysis) -> None:
    """Display causal analysis results."""
    console.print("\n[bold magenta]Causal Analysis[/bold magenta]\n")

    # Factor Impacts
    significant_impacts = causal_analysis.significant_impacts
    if significant_impacts:
        console.print("[bold]Significant Factor-Metric Relationships:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Factor")
        table.add_column("Metric")
        table.add_column("Direction")
        table.add_column("Strength")
        table.add_column("Correlation", justify="right")
        table.add_column("p-value", justify="right")

        for impact in significant_impacts[:10]:  # Show top 10
            direction_style = "green" if impact.direction.value == "positive" else "red"
            table.add_row(
                impact.factor_type.value,
                impact.metric_name,
                f"[{direction_style}]{impact.direction.value}[/{direction_style}]",
                impact.strength.value,
                f"{impact.correlation:.3f}",
                f"{impact.p_value:.4f}",
            )

        console.print(table)
        console.print()

    # Causal Relationships
    strong_relationships = causal_analysis.strong_relationships
    if strong_relationships:
        console.print("[bold]Strong Causal Relationships (confidence > 0.7):[/bold]")
        for rel in strong_relationships[:5]:
            direction_arrow = "↑" if rel.direction.value == "positive" else "↓"
            console.print(
                f"  • {rel.cause.value} → {rel.effect_metric} {direction_arrow} "
                f"(confidence: {rel.confidence:.2f})"
            )
        console.print()

    # Root Causes
    if causal_analysis.root_causes:
        console.print("[bold]Root Cause Analysis:[/bold]")
        for rc in causal_analysis.root_causes:
            primary_str = ", ".join(f.value for f in rc.primary_causes)
            console.print(f"  [bold]{rc.metric_name}:[/bold]")
            console.print(f"    Primary causes: {primary_str}")
            if rc.contributing_factors:
                contributing_str = ", ".join(f.value for f in rc.contributing_factors)
                console.print(f"    Contributing factors: {contributing_str}")
            if rc.explanation:
                console.print(f"    Explanation: {rc.explanation}")
        console.print()

    # Intervention Suggestions
    if causal_analysis.interventions:
        console.print("[bold]Recommended Interventions:[/bold]")
        for intervention in causal_analysis.interventions[:5]:  # Show top 5
            priority_str = {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}.get(
                intervention.priority, f"Priority {intervention.priority}"
            )
            console.print(f"  [{priority_str}] {intervention.intervention}")
            console.print(f"      Target: {intervention.target_metric}")
            console.print(f"      Expected: {intervention.expected_impact}")
        console.print()

    # Causal Insights
    if causal_analysis.insights:
        console.print("[bold]Causal Insights:[/bold]")
        for insight in causal_analysis.insights:
            console.print(f"  • {insight}")
        console.print()


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

    # Add NLP analysis if available
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

    # Add improvement report if available
    if improvement_report:
        data["improvement_report"] = improvement_report.to_dict()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _perform_playbook_analysis(run, enable_llm: bool, profile: str | None):
    """Perform playbook-based improvement analysis.

    Args:
        run: EvaluationRun to analyze
        enable_llm: Whether to enable LLM-based insight generation
        profile: Model profile for LLM

    Returns:
        ImprovementReport with guides and recommendations
    """
    from evalvault.adapters.outbound.improvement.insight_generator import InsightGenerator
    from evalvault.adapters.outbound.improvement.pattern_detector import PatternDetector
    from evalvault.adapters.outbound.improvement.playbook_loader import get_default_playbook
    from evalvault.domain.services.improvement_guide_service import ImprovementGuideService

    console.print("\n[bold cyan]Playbook-based Improvement Analysis[/bold cyan]\n")

    playbook = get_default_playbook()
    detector = PatternDetector(playbook=playbook)

    # Create insight generator if LLM is enabled
    insight_generator = None
    if enable_llm:
        settings = Settings()
        profile_name = profile or settings.evalvault_profile
        if profile_name:
            settings = apply_profile(settings, profile_name)

        llm_adapter = get_llm_adapter(settings)
        insight_generator = InsightGenerator(llm_adapter=llm_adapter)
        console.print("[dim]LLM-based insight generation enabled[/dim]")

    # Create improvement guide service
    service = ImprovementGuideService(
        pattern_detector=detector,
        insight_generator=insight_generator,
        playbook=playbook,
        enable_llm_enrichment=enable_llm,
    )

    # Generate improvement report
    with console.status("[bold green]Analyzing patterns and generating recommendations..."):
        report = service.generate_report(run, include_llm_analysis=enable_llm)

    # Display improvement report
    _display_improvement_report(report)

    return report


def _display_improvement_report(report) -> None:
    """Display improvement report in console."""
    from evalvault.domain.entities.improvement import ImprovementPriority

    # Summary panel
    summary = f"""[bold]Improvement Analysis Summary[/bold]
Run ID: {report.run_id}
Total Test Cases: {report.total_test_cases}
Guides Generated: {len(report.guides)}
Analysis Methods: {", ".join(m.value for m in report.analysis_methods_used)}

[bold]Metric Performance vs Thresholds[/bold]"""

    for metric, score in report.metric_scores.items():
        gap = report.metric_gaps.get(metric, 0)
        status = "[red]Below threshold[/red]" if gap > 0 else "[green]Meeting threshold[/green]"
        summary += f"\n  {metric}: {score:.3f} ({status})"
        if gap > 0:
            summary += f" [dim](gap: -{gap:.3f})[/dim]"

    console.print(
        Panel(summary, title="[bold cyan]Improvement Analysis[/bold cyan]", border_style="cyan")
    )

    # Display guides by priority
    if not report.guides:
        console.print("[yellow]No improvement guides generated.[/yellow]")
        return

    critical_guides = report.get_critical_guides()
    if critical_guides:
        console.print("\n[bold red]Critical Issues (P0)[/bold red]")
        for guide in critical_guides:
            _display_guide(guide)

    high_priority = [g for g in report.guides if g.priority == ImprovementPriority.P1_HIGH]
    if high_priority:
        console.print("\n[bold yellow]High Priority (P1)[/bold yellow]")
        for guide in high_priority[:3]:  # Top 3
            _display_guide(guide)

    medium_priority = [g for g in report.guides if g.priority == ImprovementPriority.P2_MEDIUM]
    if medium_priority:
        console.print("\n[bold blue]Medium Priority (P2)[/bold blue]")
        for guide in medium_priority[:2]:  # Top 2
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
    console.print(
        f"\n  {icon} [bold]{guide.component.value.upper()}[/bold] - {', '.join(guide.target_metrics)}"
    )

    if guide.evidence:
        # Display primary pattern if available
        primary = guide.evidence.primary_pattern
        if primary:
            console.print(f"     Pattern: {primary.pattern_type.value}")
            console.print(
                f"     Affected: {primary.affected_count}/{primary.total_count} test cases ({primary.affected_ratio:.1%})"
            )
        elif guide.evidence.total_failures > 0:
            console.print(f"     Failures: {guide.evidence.total_failures} test cases")
            console.print(f"     Avg Score (failures): {guide.evidence.avg_score_failures:.3f}")

    if guide.actions:
        console.print("     [bold]Recommended Actions:[/bold]")
        for action in guide.actions[:3]:  # Top 3 actions
            effort_color = {"low": "green", "medium": "yellow", "high": "red"}.get(
                action.effort, "white"
            )
            console.print(f"       • {action.title}")
            if action.description:
                console.print(
                    f"         [dim]{action.description[:60]}...[/dim]"
                    if len(action.description) > 60
                    else f"         [dim]{action.description}[/dim]"
                )
            console.print(
                f"         Expected: +{action.expected_improvement:.1%} | Effort: [{effort_color}]{action.effort}[/{effort_color}]"
            )

    if guide.verification_command:
        console.print(f"     [dim]Verify: {guide.verification_command}[/dim]")


def _generate_report(
    bundle, output_path: Path, include_nlp: bool = True, improvement_report=None
) -> None:
    """Generate analysis report (Markdown or HTML).

    Args:
        bundle: AnalysisBundle containing analysis results
        output_path: Output file path (*.md or *.html)
        include_nlp: Whether to include NLP analysis section
        improvement_report: Optional ImprovementReport to include
    """
    adapter = MarkdownReportAdapter()

    # Determine format from file extension
    suffix = output_path.suffix.lower()

    if suffix == ".html":
        content = adapter.generate_html(bundle, include_nlp=include_nlp)
    else:
        # Default to markdown
        content = adapter.generate_markdown(bundle, include_nlp=include_nlp)

    # Append improvement report if available
    if improvement_report:
        content += "\n\n" + improvement_report.to_markdown()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


# ============================================================================
# Web UI Command
# ============================================================================


@app.command()
def web(
    port: int = typer.Option(
        8501,
        "--port",
        "-p",
        help="Port to run the web server on.",
    ),
    host: str = typer.Option(
        "localhost",
        "--host",
        "-h",
        help="Host to bind the web server to.",
    ),
    db_path: Path = typer.Option(
        "evalvault.db",
        "--db",
        help="Path to SQLite database file.",
    ),
):
    """Launch the EvalVault Web UI (Streamlit dashboard).

    Examples:
        evalvault web
        evalvault web --port 8502
        evalvault web --host 0.0.0.0 --port 8080
    """
    import subprocess
    import sys

    console.print("\n[bold]EvalVault Web UI[/bold]\n")
    console.print(f"Starting server at [cyan]http://{host}:{port}[/cyan]")
    console.print(f"Database: [dim]{db_path}[/dim]")
    console.print("\n[dim]Press Ctrl+C to stop the server.[/dim]\n")

    try:
        # Get the path to the Streamlit app
        from evalvault.adapters.inbound.web import app as web_app_module

        app_path = Path(web_app_module.__file__).parent / "app.py"

        # Run Streamlit
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(app_path),
                "--server.port",
                str(port),
                "--server.address",
                host,
                "--",
                "--db",
                str(db_path),
            ],
            check=True,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped.[/yellow]")
    except ImportError:
        console.print("[red]Error:[/red] Streamlit not installed.")
        console.print("Install with: [cyan]uv add streamlit[/cyan]")
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error starting web server:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# Pipeline Commands (Phase 14)
# ============================================================================


@pipeline_app.command("analyze")
def pipeline_analyze(
    query: str = typer.Argument(..., help="Analysis query in natural language."),
    run_id: str | None = typer.Option(
        None,
        "--run",
        "-r",
        help="Run ID to analyze (optional).",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for results (JSON format).",
    ),
    db_path: Path = typer.Option(
        "evalvault.db",
        "--db",
        help="Path to database file.",
    ),
):
    """Analyze evaluation results using natural language query.

    The system automatically classifies your intent and builds
    an appropriate analysis pipeline.

    Examples:
        evalvault pipeline analyze "형태소 분석이 제대로 되고 있는지 확인해줘"
        evalvault pipeline analyze "결과를 요약해줘" --run run-123
        evalvault pipeline analyze "BM25와 Dense 검색을 비교해줘"
    """
    from evalvault.adapters.outbound.analysis import (
        DataLoaderModule,
        StatisticalAnalyzerModule,
        SummaryReportModule,
    )
    from evalvault.domain.entities.analysis import StatisticalAnalysis
    from evalvault.domain.services.pipeline_orchestrator import AnalysisPipelineService

    console.print("\n[bold]Pipeline Analysis[/bold]\n")
    console.print(f"Query: [cyan]{query}[/cyan]")

    # Initialize service
    service = AnalysisPipelineService()

    # Register modules
    storage = SQLiteStorageAdapter(db_path=db_path)
    service.register_module(DataLoaderModule(storage=storage))
    service.register_module(StatisticalAnalyzerModule())
    service.register_module(SummaryReportModule())

    # Classify intent
    intent = service.get_intent(query)
    console.print(f"Detected Intent: [green]{intent.value}[/green]\n")

    # Execute pipeline
    with console.status("[bold green]Running analysis pipeline..."):
        result = service.analyze(query, run_id=run_id)

    saved_analysis_id: str | None = None
    stats_node = result.get_node_result("statistical_analyzer")
    if stats_node and isinstance(stats_node.output, dict):
        analysis_obj = stats_node.output.get("analysis")
        if isinstance(analysis_obj, StatisticalAnalysis):
            try:
                saved_analysis_id = storage.save_analysis(analysis_obj)
            except Exception as exc:  # pragma: no cover - best effort for CLI UX
                console.print(f"[yellow]Warning: Failed to store analysis result ({exc})[/yellow]")

    # Display results
    if result.is_complete:
        console.print("[green]Pipeline completed successfully![/green]")
        console.print(f"Duration: {result.total_duration_ms}ms")
        console.print(f"Nodes executed: {len(result.node_results)}")
        if saved_analysis_id:
            console.print(f"Analysis saved as [blue]{saved_analysis_id}[/blue]")

        # Show final output
        if result.final_output:
            console.print("\n[bold]Results:[/bold]")
            for node_id, node_output in result.final_output.items():
                if isinstance(node_output, dict) and "report" in node_output:
                    console.print(Panel(node_output["report"], title=node_id))
                else:
                    console.print(f"  {node_id}: {node_output}")
    else:
        console.print("[red]Pipeline failed.[/red]")
        for node_id, node_result in result.node_results.items():
            if node_result.error:
                console.print(f"  [red]{node_id}:[/red] {node_result.error}")

    output_path = output

    # Save to file if requested
    if output_path:
        import json

        data = {
            "query": query,
            "intent": result.intent.value if result.intent else None,
            "is_complete": result.is_complete,
            "duration_ms": result.total_duration_ms,
            "final_output": result.final_output,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        console.print(f"\n[green]Results saved to {output_path}[/green]")

    console.print()


@pipeline_app.command("intents")
def pipeline_intents():
    """List all available analysis intents.

    Shows all intent types that can be automatically detected
    from user queries.
    """
    from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

    console.print("\n[bold]Available Analysis Intents[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Intent", style="bold")
    table.add_column("Category")
    table.add_column("Description")

    intent_descriptions = {
        AnalysisIntent.VERIFY_MORPHEME: ("Verification", "형태소 분석 검증"),
        AnalysisIntent.VERIFY_EMBEDDING: ("Verification", "임베딩 품질 검증"),
        AnalysisIntent.VERIFY_RETRIEVAL: ("Verification", "검색 품질 검증"),
        AnalysisIntent.COMPARE_SEARCH_METHODS: ("Comparison", "검색 방식 비교 (BM25/Dense/Hybrid)"),
        AnalysisIntent.COMPARE_MODELS: ("Comparison", "LLM 모델 비교"),
        AnalysisIntent.COMPARE_RUNS: ("Comparison", "평가 결과 비교"),
        AnalysisIntent.ANALYZE_LOW_METRICS: ("Analysis", "낮은 메트릭 원인 분석"),
        AnalysisIntent.ANALYZE_PATTERNS: ("Analysis", "패턴 분석"),
        AnalysisIntent.ANALYZE_TRENDS: ("Analysis", "추세 분석"),
        AnalysisIntent.GENERATE_SUMMARY: ("Report", "요약 보고서 생성"),
        AnalysisIntent.GENERATE_DETAILED: ("Report", "상세 보고서 생성"),
        AnalysisIntent.GENERATE_COMPARISON: ("Report", "비교 보고서 생성"),
    }

    for intent in AnalysisIntent:
        category, desc = intent_descriptions.get(intent, ("Other", intent.value))
        table.add_row(intent.value, category, desc)

    console.print(table)
    console.print("\n[dim]Use 'evalvault pipeline analyze \"<query>\"' to run analysis.[/dim]\n")


@pipeline_app.command("templates")
def pipeline_templates():
    """List available pipeline templates for each intent.

    Shows the pre-defined node configurations for each analysis intent.
    """
    from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
    from evalvault.domain.services.pipeline_template_registry import PipelineTemplateRegistry

    console.print("\n[bold]Pipeline Templates[/bold]\n")

    registry = PipelineTemplateRegistry()

    for intent in AnalysisIntent:
        template = registry.get_template(intent)
        if template and template.nodes:
            console.print(f"[bold cyan]{intent.value}[/bold cyan]")
            for node in template.nodes:
                deps = f" (depends: {', '.join(node.depends_on)})" if node.depends_on else ""
                console.print(f"  • {node.name} [{node.module}]{deps}")
            console.print()

    console.print("[dim]Templates define the DAG structure for each analysis intent.[/dim]\n")


# ============================================================================
# Benchmark Commands (Phase 9.5)
# ============================================================================


@benchmark_app.command("run")
def benchmark_run(
    name: str = typer.Option(
        "korean-rag",
        "--name",
        "-n",
        help="Benchmark name to run.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for results (JSON format).",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output.",
    ),
):
    """Run a benchmark suite.

    Examples:
        evalvault benchmark run
        evalvault benchmark run --name korean-rag --output results.json
    """
    console.print(f"\n[bold]Running Benchmark: {name}[/bold]\n")

    try:
        from evalvault.domain.services.benchmark_runner import KoreanRAGBenchmarkRunner

        toolkit = None
        if name == "korean-rag":
            try:
                from evalvault.adapters.outbound.nlp.korean import KoreanNLPToolkit

                toolkit = KoreanNLPToolkit()
            except ImportError:
                console.print(
                    "[yellow]Warning:[/yellow] Korean NLP extras not installed. "
                    "Falling back to baseline algorithms."
                )

        runner = KoreanRAGBenchmarkRunner(nlp_toolkit=toolkit)

        with console.status("[bold green]Running benchmark..."):
            results = runner.run_all()

        # Display results
        table = Table(title="Benchmark Results", show_header=True, header_style="bold cyan")
        table.add_column("Test Case")
        table.add_column("Status")
        table.add_column("Score", justify="right")
        table.add_column("Details")

        passed = 0
        for result in results:
            status = "[green]PASS[/green]" if result.passed else "[red]FAIL[/red]"
            if result.passed:
                passed += 1
            score = f"{result.score:.2f}" if result.score is not None else "-"
            details = result.details[:40] + "..." if len(result.details) > 40 else result.details
            table.add_row(result.name, status, score, details)

        console.print(table)
        console.print(f"\n[bold]Summary:[/bold] {passed}/{len(results)} tests passed")

        # Save to file if requested
        if output:
            import json

            data = {
                "benchmark": name,
                "total": len(results),
                "passed": passed,
                "results": [
                    {
                        "name": r.name,
                        "passed": r.passed,
                        "score": r.score,
                        "details": r.details,
                    }
                    for r in results
                ],
            }
            with open(output, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            console.print(f"[green]Results saved to {output}[/green]")

    except ImportError as e:
        console.print(f"[red]Error:[/red] Benchmark dependencies not available: {e}")
        console.print("[dim]Some benchmarks require additional packages (kiwipiepy, etc.)[/dim]")
        raise typer.Exit(1)

    console.print()


@benchmark_app.command("list")
def benchmark_list():
    """List available benchmarks.

    Shows all benchmark suites that can be run.
    """
    console.print("\n[bold]Available Benchmarks[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Test Cases")
    table.add_column("Requirements")

    table.add_row(
        "korean-rag",
        "Korean RAG system benchmark",
        "~10",
        "kiwipiepy, rank-bm25, sentence-transformers (install with --extra korean)",
    )

    console.print(table)
    console.print("\n[dim]Use 'evalvault benchmark run --name <name>' to run a benchmark.[/dim]\n")


if __name__ == "__main__":
    app()
