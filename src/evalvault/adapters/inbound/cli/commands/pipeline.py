"""Pipeline command group for EvalVault CLI."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.config.phoenix_support import ensure_phoenix_instrumentation
from evalvault.config.settings import Settings

from ..utils.analysis_io import serialize_pipeline_result
from ..utils.options import db_option


def register_pipeline_commands(app: typer.Typer, console) -> None:
    """Attach pipeline-related commands to the root Typer app."""

    pipeline_app = typer.Typer(name="pipeline", help="Query-based analysis pipeline.")

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
        db_path: Path | None = db_option(help_text="Path to database file."),
    ) -> None:
        """Analyze evaluation results using natural language query."""
        from evalvault.adapters.outbound.analysis.pipeline_factory import (
            build_analysis_pipeline_service,
        )
        from evalvault.adapters.outbound.llm import get_llm_adapter
        from evalvault.domain.entities.analysis import StatisticalAnalysis

        console.print("\n[bold]Pipeline Analysis[/bold]\n")
        console.print(f"Query: [cyan]{query}[/cyan]")

        settings = Settings()
        if settings.phoenix_enabled:
            ensure_phoenix_instrumentation(settings, console=console)

        if db_path is None:
            console.print("[red]Error: Database path is not configured.[/red]")
            raise typer.Exit(1)

        storage = SQLiteStorageAdapter(db_path=db_path)
        llm_adapter = None
        try:
            llm_adapter = get_llm_adapter(settings)
        except Exception as exc:
            console.print(f"[yellow]Warning: LLM adapter initialization failed ({exc})[/yellow]")

        service = build_analysis_pipeline_service(storage=storage, llm_adapter=llm_adapter)

        intent = service.get_intent(query)
        console.print(f"Detected Intent: [green]{intent.value}[/green]\n")

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
                    console.print(
                        f"[yellow]Warning: Failed to store analysis result ({exc})[/yellow]"
                    )

        if result.is_complete:
            console.print("[green]Pipeline completed successfully![/green]")
            console.print(f"Duration: {result.total_duration_ms}ms")
            console.print(f"Nodes executed: {len(result.node_results)}")
            if saved_analysis_id:
                console.print(f"Analysis saved as [blue]{saved_analysis_id}[/blue]")

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

        if output:
            payload = serialize_pipeline_result(result)
            payload["query"] = query
            with open(output, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            console.print(f"\n[green]Results saved to {output}[/green]")

        console.print()

    @pipeline_app.command("intents")
    def pipeline_intents() -> None:
        """List available analysis intents."""
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
            AnalysisIntent.COMPARE_SEARCH_METHODS: (
                "Comparison",
                "검색 방식 비교 (BM25/Dense/Hybrid)",
            ),
            AnalysisIntent.COMPARE_MODELS: ("Comparison", "LLM 모델 비교"),
            AnalysisIntent.COMPARE_RUNS: ("Comparison", "평가 결과 비교"),
            AnalysisIntent.ANALYZE_LOW_METRICS: ("Analysis", "낮은 메트릭 원인 분석"),
            AnalysisIntent.ANALYZE_PATTERNS: ("Analysis", "패턴 분석"),
            AnalysisIntent.ANALYZE_TRENDS: ("Analysis", "추세 분석"),
            AnalysisIntent.BENCHMARK_RETRIEVAL: ("Benchmark", "검색 벤치마크"),
            AnalysisIntent.GENERATE_SUMMARY: ("Report", "요약 보고서 생성"),
            AnalysisIntent.GENERATE_DETAILED: ("Report", "상세 보고서 생성"),
            AnalysisIntent.GENERATE_COMPARISON: ("Report", "비교 보고서 생성"),
        }

        for intent in AnalysisIntent:
            category, desc = intent_descriptions.get(intent, ("Other", intent.value))
            table.add_row(intent.value, category, desc)

        console.print(table)
        console.print(
            "\n[dim]Use 'evalvault pipeline analyze \"<query>\"' to run analysis.[/dim]\n"
        )

    @pipeline_app.command("templates")
    def pipeline_templates() -> None:
        """List available pipeline templates for each intent."""
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

    app.add_typer(pipeline_app, name="pipeline")


__all__ = ["register_pipeline_commands"]
