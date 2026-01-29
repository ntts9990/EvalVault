"""Benchmark subcommands for EvalVault CLI."""

from __future__ import annotations

import csv
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from evalvault.domain.services.retrieval_metrics import (
    average_retrieval_metrics,
    compute_retrieval_metrics,
    resolve_doc_id,
)

from ..utils.formatters import format_score, format_status
from ..utils.progress import evaluation_progress


def create_benchmark_app(console: Console) -> typer.Typer:
    """Create the Typer sub-application for benchmark commands."""

    benchmark_app = typer.Typer(name="benchmark", help="Korean RAG benchmark utilities.")

    @benchmark_app.command("run")
    def benchmark_run(
        name: str = typer.Option(
            "korean-rag",
            "--name",
            "-n",
            help="Benchmark name to run. Use 'evalvault benchmark list' to see available benchmarks.",
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
    ) -> None:
        """Run a benchmark suite.

        \b
        Examples:
          # Run the Korean RAG benchmark
          evalvault benchmark run -n korean-rag

          # Save results to a file
          evalvault benchmark run -n korean-rag -o results.json

        \b
        See also:
          evalvault benchmark list       — List available benchmarks
          evalvault benchmark retrieval  — Run retrieval-specific benchmarks
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

            table = Table(title="Benchmark Results", show_header=True, header_style="bold cyan")
            table.add_column("Test Case")
            table.add_column("Status")
            table.add_column("Score", justify="right")
            table.add_column("Details")

            passed = 0
            for result in results:
                status = format_status(result.passed)
                if result.passed:
                    passed += 1
                score = format_score(
                    result.score, result.passed if result.score is not None else None, precision=2
                )
                details = (
                    result.details[:40] + "..." if len(result.details) > 40 else result.details
                )
                table.add_row(result.name, status, score, details)

            console.print(table)
            console.print(f"\n[bold]Summary:[/bold] {passed}/{len(results)} tests passed")

            if output:
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
                with open(output, "w", encoding="utf-8") as file:
                    json.dump(data, file, ensure_ascii=False, indent=2)
                console.print(f"[green]Results saved to {output}[/green]")

        except ImportError as exc:
            console.print(f"[red]Error:[/red] Benchmark dependencies not available: {exc}")
            console.print(
                "[dim]Some benchmarks require additional packages (kiwipiepy, etc.)[/dim]"
            )
            raise typer.Exit(1)

        console.print()

    @benchmark_app.command("retrieval")
    def benchmark_retrieval(
        testset: Path = typer.Argument(..., help="Retrieval ground truth JSON file."),
        methods: str = typer.Option(
            "bm25,dense,hybrid",
            "--methods",
            "-m",
            help="Comma-separated retrieval methods: bm25, dense, hybrid, graphrag.",
        ),
        top_k: int = typer.Option(
            5,
            "--top-k",
            "-k",
            min=1,
            help="Top-K cutoff for Recall@K, Precision@K, and MRR.",
        ),
        ndcg_k: int | None = typer.Option(
            None,
            "--ndcg-k",
            min=1,
            help="Top-K cutoff for nDCG (defaults to --top-k).",
        ),
        embedding_profile: str | None = typer.Option(
            None,
            "--embedding-profile",
            help="Embedding profile for dense/hybrid: 'dev' or 'prod' (Ollama).",
        ),
        embedding_model: str | None = typer.Option(
            None,
            "--embedding-model",
            help="Embedding model override for dense/hybrid retrieval.",
        ),
        kg: Path | None = typer.Option(
            None,
            "--kg",
            help="Knowledge graph JSON file (required for GraphRAG method).",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file for results (.json or .csv format).",
        ),
    ) -> None:
        """Run retrieval benchmark across multiple methods.

        Compare BM25, Dense, Hybrid, and GraphRAG retrieval methods on your
        dataset with standard metrics: Recall@K, Precision@K, MRR, and nDCG@K.

        \b
        Examples:
          # Compare all retrieval methods
          evalvault benchmark retrieval testset.json -m bm25,dense,hybrid

          # Use GraphRAG with knowledge graph
          evalvault benchmark retrieval testset.json -m graphrag --kg graph.json

          # Save results as CSV
          evalvault benchmark retrieval testset.json -o results.csv

          # Custom top-K cutoff
          evalvault benchmark retrieval testset.json -k 10 --ndcg-k 20

          # Use Ollama embeddings for dense retrieval
          evalvault benchmark retrieval testset.json -m dense --embedding-profile dev

        \b
        Testset Format (JSON):
          {
            "documents": [{"doc_id": "d1", "content": "..."}],
            "test_cases": [{"query": "...", "relevant_doc_ids": ["d1"]}]
          }

        \b
        See also:
          evalvault benchmark run   — Run benchmark suites
          evalvault run             — Evaluate with retrievers
        """

        data = _load_retrieval_testset(testset)
        documents = data.get("documents", [])
        test_cases = _normalize_retrieval_test_cases(data.get("test_cases", []))
        if not documents or not test_cases:
            console.print("[red]Error:[/red] documents/test_cases are required.")
            raise typer.Exit(1)

        doc_ids, doc_contents = _normalize_documents(documents)
        doc_id_set = set(doc_ids)
        _warn_missing_relevance(console, test_cases, doc_id_set)

        method_list = _parse_methods(methods)
        if "graphrag" in method_list and kg is None:
            console.print("[red]Error:[/red] GraphRAG requires --kg.")
            raise typer.Exit(1)

        results: dict[str, dict[str, Any]] = {}
        recall_key = f"recall_at_{top_k}"
        precision_key = f"precision_at_{top_k}"
        ndcg_key = f"ndcg_at_{ndcg_k or top_k}"
        normalized_profile = _normalize_embedding_profile(embedding_profile)
        ollama_adapter = _build_ollama_adapter(
            embedding_profile=normalized_profile,
            embedding_model=embedding_model,
            console=console,
        )

        total_operations = len(method_list) * len(test_cases)
        with evaluation_progress(
            console, total_operations, description="Running retrieval benchmark"
        ) as update_progress:
            completed = 0
            for method in method_list:
                search_fn, backend = _build_search_fn(
                    method,
                    doc_contents,
                    doc_ids,
                    console=console,
                    kg_path=kg,
                    embedding_profile=normalized_profile,
                    embedding_model=embedding_model,
                    ollama_adapter=ollama_adapter,
                )
                case_metrics = []
                for tc in test_cases:
                    retrieved = search_fn(tc["query"], top_k)
                    metrics = compute_retrieval_metrics(
                        retrieved,
                        tc["relevant_doc_ids"],
                        recall_k=top_k,
                        ndcg_k=ndcg_k,
                    )
                    case_metrics.append(metrics)
                    completed += 1
                    update_progress(completed)

                summary = average_retrieval_metrics(case_metrics)
                summary["test_cases"] = len(case_metrics)
                if backend != method:
                    summary["backend"] = backend
                results[method] = summary

        _print_retrieval_table(
            console,
            results,
            recall_key=recall_key,
            precision_key=precision_key,
            ndcg_key=ndcg_key,
        )

        if output:
            payload = {
                "methods_compared": method_list,
                "results": results,
                "overall": _build_overall_summary(
                    results,
                    recall_key,
                    precision_key,
                    ndcg_key,
                ),
            }
            _write_retrieval_output(
                output,
                payload,
                results,
                recall_key,
                precision_key,
                ndcg_key,
            )
            console.print(f"[green]Results saved to {output}[/green]")

    @benchmark_app.command("kmmlu")
    def benchmark_kmmlu(
        subjects: str = typer.Option(
            "Insurance",
            "--subjects",
            "-s",
            help="Comma-separated KMMLU subjects (e.g., Insurance,Finance).",
        ),
        backend: str = typer.Option(
            "ollama",
            "--backend",
            "-b",
            help="Model backend: vllm, hf, openai, api, ollama.",
        ),
        model: str | None = typer.Option(
            None,
            "--model",
            "-m",
            help="Model name (uses profile default if not specified).",
        ),
        base_url: str | None = typer.Option(
            None,
            "--base-url",
            help="API base URL for vllm/api/ollama backends.",
        ),
        num_fewshot: int = typer.Option(
            5,
            "--num-fewshot",
            "-f",
            help="Number of few-shot examples.",
        ),
        limit: int | None = typer.Option(
            None,
            "--limit",
            "-l",
            help="Limit samples per task (for testing).",
        ),
        db: Path = typer.Option(
            Path("data/db/evalvault.db"),
            "--db",
            help="Database path for storing results.",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file for results (JSON format).",
        ),
        phoenix: bool = typer.Option(
            False,
            "--phoenix",
            help="Enable Phoenix tracing.",
        ),
    ) -> None:
        """Run KMMLU benchmark via lm-evaluation-harness.

        Results are automatically saved to the database and can be viewed with
        'evalvault benchmark history'.

        \b
        Examples:
          # Run KMMLU Insurance with Ollama (default)
          evalvault benchmark kmmlu -s Insurance -m gemma3:1b

          # Run with vLLM backend
          evalvault benchmark kmmlu -s Insurance --backend vllm

          # Run multiple subjects
          evalvault benchmark kmmlu -s "Insurance,Finance" -m gemma3:1b

          # Quick test with limited samples
          evalvault benchmark kmmlu -s Insurance -m gemma3:1b --limit 10

        \b
        See also:
          evalvault benchmark list       — List available benchmarks
          evalvault benchmark history    — View past benchmark runs
        """
        try:
            from evalvault.adapters.outbound.benchmark import LMEvalAdapter
            from evalvault.adapters.outbound.storage.factory import build_storage_adapter
            from evalvault.config.settings import get_settings
            from evalvault.domain.services.benchmark_service import BenchmarkService
            from evalvault.ports.outbound.benchmark_port import BenchmarkBackend
        except ImportError as exc:
            console.print(f"[red]Error:[/red] lm-eval not installed: {exc}")
            console.print('[dim]Install with: uv add "lm_eval[api]"[/dim]')
            raise typer.Exit(1)

        backend_map = {
            "vllm": BenchmarkBackend.VLLM,
            "hf": BenchmarkBackend.HF,
            "openai": BenchmarkBackend.OPENAI,
            "api": BenchmarkBackend.API,
            "ollama": BenchmarkBackend.OLLAMA,
        }
        if backend.lower() not in backend_map:
            console.print(f"[red]Error:[/red] Unknown backend: {backend}")
            console.print("[dim]Supported backends: vllm, hf, openai, api, ollama[/dim]")
            raise typer.Exit(1)

        subject_list = [s.strip() for s in subjects.split(",") if s.strip()]

        settings = get_settings()
        if model:
            settings.ollama_model = model
        if base_url:
            settings.ollama_base_url = base_url

        model_args: dict[str, Any] = {}
        if model:
            model_args["model"] = model
        if base_url:
            model_args["base_url"] = base_url

        if phoenix:
            from evalvault.config.phoenix_support import ensure_phoenix_instrumentation

            ensure_phoenix_instrumentation(settings, console=console, force=True)

        benchmark_adapter = LMEvalAdapter(settings=settings)
        storage_adapter = build_storage_adapter(settings=settings, db_path=db)
        tracer_adapter = _create_tracer_adapter(phoenix)
        service = BenchmarkService(
            benchmark_adapter=benchmark_adapter,
            storage_adapter=storage_adapter,
            tracer_adapter=tracer_adapter,
        )

        resolved_model = model or getattr(settings, "ollama_model", "unknown")
        console.print("\n[bold]Running KMMLU Benchmark[/bold]")
        console.print(f"  Subjects: {', '.join(subject_list)}")
        console.print(f"  Model: {resolved_model}")
        console.print(f"  Backend: {backend}")
        console.print(f"  Few-shot: {num_fewshot}")
        if limit:
            console.print(f"  Limit: {limit} samples/task")
        console.print(f"  DB: {db}")
        if phoenix:
            console.print("  Phoenix: enabled")
        console.print()

        with console.status("[bold green]Running lm-eval benchmark..."):
            run = service.run_kmmlu(
                subjects=subject_list,
                model_name=resolved_model,
                backend=backend_map[backend.lower()],
                num_fewshot=num_fewshot,
                limit=limit,
                model_args=model_args,
            )

        if run.error_message:
            console.print(f"[red]Error:[/red] {run.error_message}")
            raise typer.Exit(1)

        table = Table(
            title="KMMLU Benchmark Results",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Task")
        table.add_column("Accuracy", justify="right")
        table.add_column("Samples", justify="right")

        for score in run.task_scores:
            acc_str = f"{score.accuracy:.4f}"
            table.add_row(score.task_name, acc_str, str(score.num_samples))

        console.print(table)
        acc_display = f"{run.overall_accuracy:.4f}" if run.overall_accuracy is not None else "N/A"
        console.print(f"\n[bold]Overall Accuracy:[/bold] {acc_display}")
        console.print(f"[dim]Run ID: {run.run_id}[/dim]")
        console.print(f"[dim]Duration: {run.duration_seconds:.1f}s[/dim]")
        console.print("[green]Results saved to database[/green]")

        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("w", encoding="utf-8") as f:
                json.dump(run.to_dict(), f, ensure_ascii=False, indent=2)
            console.print(f"[green]Results also saved to {output}[/green]")

    @benchmark_app.command("list")
    def benchmark_list() -> None:
        """List available benchmarks.

        \b
        Examples:
          evalvault benchmark list

        \b
        See also:
          evalvault benchmark run        — Run a benchmark suite
          evalvault benchmark retrieval  — Run retrieval benchmarks
          evalvault benchmark kmmlu      — Run KMMLU benchmark
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
        table.add_row(
            "kmmlu",
            "Korean MMLU benchmark (via lm-eval)",
            "~1,000+",
            'lm_eval (install with: pip install "lm_eval[hf,vllm,api]")',
        )

        console.print(table)
        console.print(
            "\n[dim]Use 'evalvault benchmark run --name <name>' to run a benchmark.[/dim]"
        )
        console.print("[dim]Use 'evalvault benchmark kmmlu' to run KMMLU benchmark.[/dim]\n")

    @benchmark_app.command("history")
    def benchmark_history(
        benchmark_type: str | None = typer.Option(
            None,
            "--type",
            "-t",
            help="Filter by benchmark type (kmmlu, mmlu, custom).",
        ),
        model_name: str | None = typer.Option(
            None,
            "--model",
            "-m",
            help="Filter by model name.",
        ),
        limit: int = typer.Option(
            20,
            "--limit",
            "-l",
            help="Maximum number of results.",
        ),
        db: Path = typer.Option(
            Path("data/db/evalvault.db"),
            "--db",
            help="Database path.",
        ),
    ) -> None:
        """View past benchmark runs."""
        from evalvault.adapters.outbound.storage.factory import build_storage_adapter
        from evalvault.config.settings import get_settings

        settings = get_settings()
        storage = build_storage_adapter(settings=settings, db_path=db)
        runs = storage.list_benchmark_runs(
            benchmark_type=benchmark_type,
            model_name=model_name,
            limit=limit,
        )

        if not runs:
            console.print("[dim]No benchmark runs found.[/dim]")
            return

        table = Table(
            title="Benchmark History",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Run ID")
        table.add_column("Type")
        table.add_column("Model")
        table.add_column("Status")
        table.add_column("Accuracy", justify="right")
        table.add_column("Duration", justify="right")
        table.add_column("Date")

        for run in runs:
            status_style = "green" if run.status.value == "completed" else "red"
            acc_str = f"{run.overall_accuracy:.4f}" if run.overall_accuracy else "-"
            duration_str = f"{run.duration_seconds:.1f}s"
            date_str = run.started_at.strftime("%Y-%m-%d %H:%M") if run.started_at else "-"

            table.add_row(
                run.run_id,
                run.benchmark_type.value,
                run.model_name,
                f"[{status_style}]{run.status.value}[/{status_style}]",
                acc_str,
                duration_str,
                date_str,
            )

        console.print(table)
        console.print(f"\n[dim]Showing {len(runs)} runs from {db}[/dim]")

    @benchmark_app.command("report")
    def benchmark_report(
        run_id: str = typer.Argument(..., help="Benchmark run ID to generate report for."),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file for report (markdown format).",
        ),
        db: Path = typer.Option(
            Path("data/db/evalvault.db"),
            "--db",
            help="Database path.",
        ),
        profile: str | None = typer.Option(
            None,
            "--profile",
            "-p",
            help="LLM profile for report generation.",
        ),
    ) -> None:
        """Generate LLM-powered analysis report for a benchmark run.

        \b
        Examples:
          evalvault benchmark report abc123
          evalvault benchmark report abc123 -o report.md -p dev
        """
        from evalvault.adapters.outbound.storage.factory import build_storage_adapter
        from evalvault.config.settings import get_settings
        from evalvault.domain.services.benchmark_report_service import (
            BenchmarkReportService,
        )

        settings = get_settings()
        if profile:
            settings.profile = profile

        storage = build_storage_adapter(settings=settings, db_path=db)
        benchmark_run = storage.get_benchmark_run(run_id)

        if not benchmark_run:
            console.print(f"[red]Error:[/red] Benchmark run not found: {run_id}")
            raise typer.Exit(1)

        try:
            from evalvault.adapters.outbound.llm import create_llm_adapter

            llm_adapter = create_llm_adapter(settings)
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to create LLM adapter: {e}")
            console.print("[dim]Check your profile settings in config/models.yaml[/dim]")
            raise typer.Exit(1)

        service = BenchmarkReportService(llm_adapter)

        console.print("\n[bold]Generating Benchmark Report[/bold]")
        console.print(f"  Run ID: {run_id}")
        console.print(f"  Model: {benchmark_run.model_name}")
        console.print(
            f"  Accuracy: {benchmark_run.overall_accuracy:.1%}"
            if benchmark_run.overall_accuracy
            else ""
        )
        console.print()

        with console.status("[bold green]Generating LLM analysis..."):
            report = service.generate_report_sync(benchmark_run)

        markdown_content = report.to_markdown()

        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown_content, encoding="utf-8")
            console.print(f"[green]Report saved to {output}[/green]")
        else:
            default_output = Path(f"reports/benchmark/benchmark_{run_id[:8]}.md")
            default_output.parent.mkdir(parents=True, exist_ok=True)
            default_output.write_text(markdown_content, encoding="utf-8")
            console.print(f"[green]Report saved to {default_output}[/green]")

        console.print("\n[bold]Report Preview:[/bold]")
        preview_lines = markdown_content.split("\n")[:30]
        console.print("\n".join(preview_lines))
        if len(markdown_content.split("\n")) > 30:
            console.print("\n[dim]... (truncated, see full report in file)[/dim]")

    @benchmark_app.command("compare")
    def benchmark_compare(
        baseline_id: str = typer.Argument(..., help="Baseline benchmark run ID."),
        target_id: str = typer.Argument(..., help="Target benchmark run ID to compare."),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file for comparison report.",
        ),
        db: Path = typer.Option(
            Path("data/db/evalvault.db"),
            "--db",
            help="Database path.",
        ),
        profile: str | None = typer.Option(
            None,
            "--profile",
            "-p",
            help="LLM profile for report generation.",
        ),
    ) -> None:
        """Compare two benchmark runs and generate analysis.

        \b
        Examples:
          evalvault benchmark compare abc123 def456
          evalvault benchmark compare abc123 def456 -o comparison.md
        """
        from evalvault.adapters.outbound.storage.factory import build_storage_adapter
        from evalvault.config.settings import get_settings
        from evalvault.domain.services.benchmark_report_service import (
            BenchmarkReportService,
        )

        settings = get_settings()
        if profile:
            settings.profile = profile

        storage = build_storage_adapter(settings=settings, db_path=db)
        baseline = storage.get_benchmark_run(baseline_id)
        target = storage.get_benchmark_run(target_id)

        if not baseline:
            console.print(f"[red]Error:[/red] Baseline run not found: {baseline_id}")
            raise typer.Exit(1)
        if not target:
            console.print(f"[red]Error:[/red] Target run not found: {target_id}")
            raise typer.Exit(1)

        try:
            from evalvault.adapters.outbound.llm import create_llm_adapter

            llm_adapter = create_llm_adapter(settings)
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to create LLM adapter: {e}")
            raise typer.Exit(1)

        service = BenchmarkReportService(llm_adapter)

        console.print("\n[bold]Generating Comparison Report[/bold]")
        console.print(f"  Baseline: {baseline_id} ({baseline.model_name})")
        console.print(f"  Target: {target_id} ({target.model_name})")
        console.print()

        with console.status("[bold green]Generating comparison analysis..."):
            report = service.generate_comparison_report_sync(baseline, target)

        markdown_content = report.to_markdown()

        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown_content, encoding="utf-8")
            console.print(f"[green]Report saved to {output}[/green]")
        else:
            default_output = Path(
                f"reports/benchmark/comparison_{baseline_id[:8]}_{target_id[:8]}.md"
            )
            default_output.parent.mkdir(parents=True, exist_ok=True)
            default_output.write_text(markdown_content, encoding="utf-8")
            console.print(f"[green]Report saved to {default_output}[/green]")

    return benchmark_app


def _create_tracer_adapter(enabled: bool) -> Any | None:
    if not enabled:
        return None
    try:
        from evalvault.adapters.outbound.tracer.phoenix_tracer_adapter import (
            PhoenixTracerAdapter,
        )

        return PhoenixTracerAdapter()
    except ImportError:
        return None


def _load_retrieval_testset(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise typer.BadParameter(f"Testset file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise typer.BadParameter("Invalid retrieval testset JSON.") from exc


def _normalize_documents(documents: Sequence[dict[str, Any]]) -> tuple[list[str], list[str]]:
    doc_ids: list[str] = []
    contents: list[str] = []
    for idx, doc in enumerate(documents, start=1):
        doc_id = doc.get("doc_id") or doc.get("id") or f"doc_{idx}"
        content = doc.get("content") or doc.get("text") or doc.get("document") or ""
        doc_ids.append(str(doc_id))
        contents.append(str(content))
    return doc_ids, contents


def _normalize_retrieval_test_cases(
    test_cases: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for idx, tc in enumerate(test_cases, start=1):
        query = tc.get("query") or tc.get("question")
        if not query:
            continue
        if "relevant_doc_ids" in tc:
            relevant_doc_ids = tc.get("relevant_doc_ids", [])
        else:
            relevant_doc_ids = tc.get("relevant_docs", [])
        test_id = tc.get("test_id") or tc.get("id") or f"ret-{idx:03d}"
        normalized.append(
            {
                "test_id": str(test_id),
                "query": str(query),
                "relevant_doc_ids": [str(doc_id) for doc_id in relevant_doc_ids],
            }
        )
    return normalized


def _parse_methods(methods: str) -> list[str]:
    aliases = {"graph-rag": "graphrag", "graph": "graphrag"}
    supported = {"bm25", "dense", "hybrid", "graphrag"}
    resolved: list[str] = []
    for raw in methods.split(","):
        candidate = raw.strip().lower()
        if not candidate:
            continue
        method = aliases.get(candidate, candidate)
        if method not in supported:
            raise typer.BadParameter(f"Unsupported retrieval method: {candidate}")
        if method not in resolved:
            resolved.append(method)
    if not resolved:
        raise typer.BadParameter("At least one retrieval method is required.")
    return resolved


def _normalize_embedding_profile(profile: str | None) -> str | None:
    if profile is None:
        return None
    normalized = profile.strip().lower()
    if normalized not in {"dev", "prod"}:
        raise typer.BadParameter("Embedding profile must be 'dev' or 'prod'.")
    return normalized


def _resolve_ollama_embedding_model(
    *,
    embedding_profile: str | None,
    embedding_model: str | None,
) -> str | None:
    if embedding_model:
        return embedding_model
    if embedding_profile == "dev":
        return "qwen3-embedding:0.6b"
    if embedding_profile == "prod":
        return "qwen3-embedding:8b"
    return None


def _build_ollama_adapter(
    *,
    embedding_profile: str | None,
    embedding_model: str | None,
    console: Console,
) -> Any | None:
    resolved_model = _resolve_ollama_embedding_model(
        embedding_profile=embedding_profile,
        embedding_model=embedding_model,
    )
    if not resolved_model:
        return None
    if not _is_ollama_model(resolved_model):
        return None
    try:
        from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter
        from evalvault.config.settings import get_settings

        settings = get_settings()
        settings.ollama_embedding_model = resolved_model
        return OllamaAdapter(settings)
    except Exception as exc:
        console.print(
            f"[yellow]Warning:[/yellow] Ollama adapter 초기화 실패, 키워드 폴백 사용 ({exc})"
        )
        return None


def _is_ollama_model(model_name: str) -> bool:
    return model_name.startswith("qwen3-embedding:")


def _warn_missing_relevance(
    console: Console,
    test_cases: Sequence[dict[str, Any]],
    doc_id_set: set[str],
) -> None:
    missing: list[str] = []
    for tc in test_cases:
        for doc_id in tc["relevant_doc_ids"]:
            if doc_id not in doc_id_set:
                missing.append(doc_id)
                if len(missing) >= 3:
                    break
        if len(missing) >= 3:
            break
    if missing:
        preview = ", ".join(missing)
        console.print(
            f"[yellow]Warning:[/yellow] 일부 relevant_doc_ids가 documents에 없습니다: {preview}"
        )


def _build_search_fn(
    method: str,
    documents: Sequence[str],
    doc_ids: Sequence[str],
    *,
    console: Console,
    kg_path: Path | None,
    embedding_profile: str | None,
    embedding_model: str | None,
    ollama_adapter: Any | None,
) -> tuple[Callable[[str, int], list[str]], str]:
    if method in {"bm25", "hybrid"}:
        retriever = None
        try:
            from evalvault.adapters.outbound.nlp.korean import KoreanNLPToolkit

            toolkit = KoreanNLPToolkit()
            retriever = toolkit.build_retriever(
                documents,
                use_hybrid=method == "hybrid",
                ollama_adapter=ollama_adapter,
                embedding_profile=embedding_profile,
                verbose=False,
            )
        except Exception as exc:
            console.print(
                f"[yellow]Warning:[/yellow] {method} retriever 초기화 실패, "
                f"키워드 폴백 사용 ({exc})"
            )
        if retriever:
            return (
                lambda query, top_k: _search_with_retriever(retriever, doc_ids, query, top_k),
                method,
            )
        return (
            lambda query, top_k: _keyword_search(documents, doc_ids, query, top_k),
            "keyword",
        )

    if method == "dense":
        retriever = None
        try:
            from evalvault.adapters.outbound.nlp.korean.dense_retriever import (
                KoreanDenseRetriever,
            )

            retriever = KoreanDenseRetriever()
            if embedding_profile or embedding_model or ollama_adapter:
                retriever = KoreanDenseRetriever(
                    model_name=embedding_model,
                    profile=embedding_profile,
                    ollama_adapter=ollama_adapter,
                )
            retriever.index(list(documents))
        except Exception as exc:
            console.print(
                f"[yellow]Warning:[/yellow] dense retriever 초기화 실패, 키워드 폴백 사용 ({exc})"
            )
        if retriever:
            return (
                lambda query, top_k: _search_with_retriever(retriever, doc_ids, query, top_k),
                method,
            )
        return (
            lambda query, top_k: _keyword_search(documents, doc_ids, query, top_k),
            "keyword",
        )

    if method == "graphrag":
        retriever = None
        try:
            if kg_path is None:
                raise ValueError("KG path is required for GraphRAG.")
            from evalvault.adapters.outbound.kg.graph_rag_retriever import GraphRAGRetriever

            from .run_helpers import load_knowledge_graph

            kg_graph = load_knowledge_graph(kg_path)

            bm25_retriever = None
            try:
                from evalvault.adapters.outbound.nlp.korean import KoreanNLPToolkit

                toolkit = KoreanNLPToolkit()
                bm25_retriever = toolkit.build_retriever(
                    documents,
                    use_hybrid=False,
                    ollama_adapter=ollama_adapter,
                    embedding_profile=embedding_profile,
                    verbose=False,
                )
            except Exception:
                bm25_retriever = None

            dense_retriever = None
            try:
                from evalvault.adapters.outbound.nlp.korean.dense_retriever import (
                    KoreanDenseRetriever,
                )

                dense_retriever = KoreanDenseRetriever(
                    model_name=embedding_model,
                    profile=embedding_profile,
                    ollama_adapter=ollama_adapter,
                )
                dense_retriever.index(list(documents))
            except Exception:
                dense_retriever = None

            retriever = GraphRAGRetriever(
                kg_graph,
                bm25_retriever=bm25_retriever,
                dense_retriever=dense_retriever,
                documents=list(documents),
                document_ids=list(doc_ids),
            )
        except Exception as exc:
            console.print(
                "[yellow]Warning:[/yellow] graphrag retriever 초기화 실패, "
                f"키워드 폴백 사용 ({exc})"
            )
        if retriever:
            return (
                lambda query, top_k: _search_with_retriever(retriever, doc_ids, query, top_k),
                method,
            )
        return (
            lambda query, top_k: _keyword_search(documents, doc_ids, query, top_k),
            "keyword",
        )

    raise typer.BadParameter(f"Unsupported retrieval method: {method}")


def _search_with_retriever(
    retriever: Any,
    doc_ids: Sequence[str],
    query: str,
    top_k: int,
) -> list[str]:
    results = retriever.search(query, top_k=top_k)
    return [
        resolve_doc_id(getattr(result, "doc_id", None), doc_ids, idx)
        for idx, result in enumerate(results, start=1)
    ]


def _keyword_search(
    documents: Sequence[str],
    doc_ids: Sequence[str],
    query: str,
    top_k: int,
) -> list[str]:
    query_words = set(query.lower().split())
    scores: list[tuple[int, int, str]] = []
    for idx, doc in enumerate(documents):
        doc_words = set(doc.lower().split())
        overlap = len(query_words & doc_words)
        scores.append((overlap, idx, str(doc_ids[idx])))
    scores.sort(key=lambda item: (-item[0], item[1]))
    return [doc_id for _, _, doc_id in scores[:top_k]]


def _print_retrieval_table(
    console: Console,
    results: dict[str, dict[str, Any]],
    *,
    recall_key: str,
    precision_key: str,
    ndcg_key: str,
) -> None:
    table = Table(title="Retrieval Benchmark Results", show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    for method in results:
        table.add_column(method, justify="right")

    for metric_key in [recall_key, precision_key, "mrr", ndcg_key]:
        label = _format_metric_label(metric_key)
        row = [label]
        for method in results:
            value = results[method].get(metric_key)
            row.append(format_score(value, None, precision=3))
        table.add_row(*row)

    console.print(table)

    fallbacks = {m: r.get("backend") for m, r in results.items() if r.get("backend")}
    if fallbacks:
        details = ", ".join(f"{method}→{backend}" for method, backend in fallbacks.items())
        console.print(f"[dim]Fallbacks: {details}[/dim]")


def _format_metric_label(metric_key: str) -> str:
    if metric_key.startswith("precision_at_"):
        return f"Precision@{metric_key.split('_')[-1]}"
    if metric_key.startswith("recall_at_"):
        return f"Recall@{metric_key.split('_')[-1]}"
    if metric_key.startswith("ndcg_at_"):
        return f"nDCG@{metric_key.split('_')[-1]}"
    if metric_key == "mrr":
        return "MRR"
    return metric_key


def _build_overall_summary(
    results: dict[str, dict[str, Any]],
    recall_key: str,
    precision_key: str,
    ndcg_key: str,
) -> dict[str, Any]:
    best_by_metric: dict[str, dict[str, Any]] = {}
    for metric_key in [recall_key, precision_key, "mrr", ndcg_key]:
        best_method = max(
            results.keys(),
            key=lambda method: results[method].get(metric_key, float("-inf")),
        )
        best_by_metric[metric_key] = {
            "method": best_method,
            "score": results[best_method].get(metric_key, 0.0),
        }
    return {"best_by_metric": best_by_metric}


def _write_retrieval_output(
    path: Path,
    payload: dict[str, Any],
    results: dict[str, dict[str, Any]],
    recall_key: str,
    precision_key: str,
    ndcg_key: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".csv":
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["method", recall_key, precision_key, "mrr", ndcg_key, "test_cases", "backend"]
            )
            for method, metrics in results.items():
                writer.writerow(
                    [
                        method,
                        metrics.get(recall_key, 0.0),
                        metrics.get(precision_key, 0.0),
                        metrics.get("mrr", 0.0),
                        metrics.get(ndcg_key, 0.0),
                        metrics.get("test_cases", 0),
                        metrics.get("backend", ""),
                    ]
                )
        return

    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


__all__ = ["create_benchmark_app"]
