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

from evalvault.adapters.outbound.dataset import get_loader
from evalvault.adapters.outbound.llm import LLMRelationAugmenter, get_llm_adapter
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.adapters.outbound.tracker.langfuse_adapter import LangfuseAdapter
from evalvault.config.domain_config import (
    generate_domain_template,
    list_domains,
    load_domain_config,
    save_domain_config,
)
from evalvault.config.settings import Settings, apply_profile
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


if __name__ == "__main__":
    app()
