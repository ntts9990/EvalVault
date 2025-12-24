"""CLI interface for EvalVault using Typer."""

import asyncio
from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from evalvault.adapters.outbound.dataset import get_loader
from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.adapters.outbound.tracker.langfuse_adapter import LangfuseAdapter
from evalvault.config.settings import Settings
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.domain.services.experiment_manager import ExperimentManager
from evalvault.domain.services.testset_generator import (
    BasicTestsetGenerator,
    GenerationConfig,
)

app = typer.Typer(
    name="evalvault",
    help="RAG evaluation system using Ragas with Langfuse tracing.",
    add_completion=False,
)
console = Console()

# Available metrics
AVAILABLE_METRICS = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
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
    model: str | None = typer.Option(
        None,
        "--model",
        help="Model to use for evaluation (overrides settings).",
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
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed output.",
    ),
):
    """Run RAG evaluation on a dataset."""
    # Parse metrics
    metric_list = [m.strip() for m in metrics.split(",")]

    # Validate metrics
    invalid_metrics = [m for m in metric_list if m not in AVAILABLE_METRICS]
    if invalid_metrics:
        console.print(
            f"[red]Error:[/red] Invalid metrics: {', '.join(invalid_metrics)}"
        )
        console.print(f"Available metrics: {', '.join(AVAILABLE_METRICS)}")
        raise typer.Exit(1)

    # Load settings
    settings = Settings()
    if model:
        settings.openai_model = model

    # Check for API key
    if not settings.openai_api_key:
        console.print("[red]Error:[/red] OPENAI_API_KEY not set.")
        console.print("Set it in your environment or .env file.")
        raise typer.Exit(1)

    console.print("\n[bold]EvalVault[/bold] - RAG Evaluation")
    console.print(f"Dataset: [cyan]{dataset}[/cyan]")
    console.print(f"Metrics: [cyan]{', '.join(metric_list)}[/cyan]")
    console.print(f"Model: [cyan]{settings.openai_model}[/cyan]\n")

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
    llm = OpenAIAdapter(settings)
    evaluator = RagasEvaluator()
    thresholds = settings.get_all_thresholds()

    # Run evaluation
    with console.status("[bold green]Running evaluation..."):
        try:
            result = asyncio.run(
                evaluator.evaluate(
                    dataset=ds,
                    metrics=metric_list,
                    llm=llm,
                    thresholds=thresholds,
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
  Pass Rate: {'[green]' if result.pass_rate >= 0.7 else '[red]'}{result.pass_rate:.1%}[/]
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

    console.print(table)
    console.print(
        "\n[dim]Use --metrics flag with 'run' command to specify metrics.[/dim]"
    )
    console.print("[dim]Example: evalvault run data.csv --metrics faithfulness,answer_relevancy[/dim]\n")


@app.command()
def config():
    """Show current configuration."""
    settings = Settings()

    console.print("\n[bold]Current Configuration[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    # OpenAI settings
    api_key_status = "[green]Set[/green]" if settings.openai_api_key else "[red]Not set[/red]"
    table.add_row("OpenAI API Key", api_key_status)
    table.add_row("OpenAI Model", settings.openai_model)
    table.add_row("OpenAI Base URL", settings.openai_base_url or "[dim]Default[/dim]")

    # Langfuse settings
    langfuse_status = (
        "[green]Configured[/green]"
        if settings.langfuse_public_key and settings.langfuse_secret_key
        else "[yellow]Not configured[/yellow]"
    )
    table.add_row("Langfuse", langfuse_status)
    table.add_row("Langfuse Host", settings.langfuse_host)

    console.print(table)

    # Thresholds
    console.print("\n[bold]Metric Thresholds[/bold]\n")

    threshold_table = Table(show_header=True, header_style="bold cyan")
    threshold_table.add_column("Metric", style="bold")
    threshold_table.add_column("Threshold", justify="right")

    thresholds = settings.get_all_thresholds()
    for metric, threshold in thresholds.items():
        threshold_table.add_row(metric, f"{threshold:.2f}")

    console.print(threshold_table)
    console.print(
        "\n[dim]Set thresholds via environment variables:[/dim]"
    )
    console.print("[dim]  THRESHOLD_FAITHFULNESS=0.8[/dim]")
    console.print("[dim]  THRESHOLD_ANSWER_RELEVANCY=0.7[/dim]\n")


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

    console.print("\n[bold]EvalVault[/bold] - Testset Generation")
    console.print(f"Documents: [cyan]{len(documents)}[/cyan]")
    console.print(f"Target questions: [cyan]{num_questions}[/cyan]\n")

    # Read documents
    with console.status("[bold green]Reading documents..."):
        doc_texts = []
        for doc_path in documents:
            with open(doc_path, encoding="utf-8") as f:
                doc_texts.append(f.read())
        console.print(f"[green]Loaded {len(doc_texts)} documents[/green]")

    # Generate testset
    with console.status("[bold green]Generating testset..."):
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
        experiment = manager.get_experiment(experiment_id)
        experiment.add_group(group_name, description)
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
        experiment = manager.get_experiment(experiment_id)
        experiment.add_run_to_group(group_name, run_id)
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

        if summary['description']:
            console.print(f"\n[bold]Description:[/bold]\n{summary['description']}")

        if summary['hypothesis']:
            console.print(f"\n[bold]Hypothesis:[/bold]\n{summary['hypothesis']}")

        if summary['metrics_to_compare']:
            console.print(f"\n[bold]Metrics to Compare:[/bold]")
            console.print(f"  {', '.join(summary['metrics_to_compare'])}")

        console.print(f"\n[bold]Groups:[/bold]")
        for group_name, group_data in summary['groups'].items():
            console.print(f"\n  [cyan]{group_name}[/cyan]")
            if group_data['description']:
                console.print(f"    Description: {group_data['description']}")
            console.print(f"    Runs: {group_data['num_runs']}")
            if group_data['run_ids']:
                for run_id in group_data['run_ids']:
                    console.print(f"      - {run_id}")

        if summary['conclusion']:
            console.print(f"\n[bold]Conclusion:[/bold]\n{summary['conclusion']}")

        console.print()

    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
