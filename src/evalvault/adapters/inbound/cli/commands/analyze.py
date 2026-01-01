"""Analyze-related commands for the EvalVault CLI."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from evalvault.adapters.outbound.analysis import (
    CausalAnalysisAdapter,
    NLPAnalysisAdapter,
    StatisticalAnalysisAdapter,
)
from evalvault.adapters.outbound.cache import MemoryCacheAdapter
from evalvault.adapters.outbound.llm import get_llm_adapter
from evalvault.adapters.outbound.report import MarkdownReportAdapter
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.services.analysis_service import AnalysisService

_console = Console()


def register_analyze_commands(app: typer.Typer, console: Console) -> None:
    """Attach analyze/analyze-compare commands to the root Typer app."""

    global _console
    _console = console

    @app.command()
    def analyze(  # noqa: PLR0913 - CLI 옵션 다양성을 위한 길이 허용
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
    ) -> None:
        """Analyze an evaluation run and show statistical insights."""

        storage = SQLiteStorageAdapter(db_path=db_path)

        try:
            run = storage.get_run(run_id)
        except KeyError:
            _console.print(f"[red]Error: Run not found: {run_id}[/red]")
            raise typer.Exit(1)

        if not run.results:
            _console.print("[yellow]Warning: No test case results to analyze.[/yellow]")
            raise typer.Exit(0)

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

        _console.print(f"\n[bold]Analyzing run: {run_id}[/bold]\n")
        bundle = service.analyze_run(run, include_nlp=nlp, include_causal=causal)

        if not bundle.statistical:
            _console.print("[yellow]No statistical analysis available.[/yellow]")
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
            improvement_report = _perform_playbook_analysis(run, enable_llm, profile)

        if save:
            storage.save_analysis(analysis)
            _console.print(f"\n[green]Analysis saved to database: {db_path}[/green]")

        if output:
            _export_analysis_json(analysis, output, bundle.nlp if nlp else None, improvement_report)
            _console.print(f"\n[green]Analysis exported to: {output}[/green]")

        if report:
            _generate_report(bundle, report, include_nlp=nlp, improvement_report=improvement_report)
            _console.print(f"\n[green]Report generated: {report}[/green]")

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
    ) -> None:
        """Compare two evaluation runs statistically."""

        storage = SQLiteStorageAdapter(db_path=db_path)

        try:
            run_a = storage.get_run(run_id1)
            run_b = storage.get_run(run_id2)
        except KeyError as exc:
            _console.print(f"[red]Error: {exc}[/red]")
            raise typer.Exit(1) from exc

        metric_list = None
        if metrics:
            metric_list = [m.strip() for m in metrics.split(",")]

        analysis_adapter = StatisticalAnalysisAdapter()
        service = AnalysisService(analysis_adapter)

        _console.print("\n[bold]Comparing runs:[/bold]")
        _console.print(f"  Run A: {run_id1}")
        _console.print(f"  Run B: {run_id2}")
        _console.print(f"  Test: {test}\n")

        comparisons = service.compare_runs(run_a, run_b, metrics=metric_list, test_type=test)

        if not comparisons:
            _console.print("[yellow]No common metrics to compare.[/yellow]")
            raise typer.Exit(0)

        table = Table(title="Statistical Comparison", show_header=True, header_style="bold cyan")
        table.add_column("Metric")
        table.add_column("Run A (Mean)", justify="right")
        table.add_column("Run B (Mean)", justify="right")
        table.add_column("Diff (%)", justify="right")
        table.add_column("p-value", justify="right")
        table.add_column("Effect Size", justify="right")
        table.add_column("Significant")
        table.add_column("Winner")

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
                f"[{sig_style}]{'Yes' if comparison.is_significant else 'No'}[/{sig_style}]",
                winner,
            )

        _console.print(table)
        _console.print()


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
    _console.print(panel)


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

    _console.print(table)
    _console.print()


def _display_correlations(analysis) -> None:
    """Display significant correlations."""

    if not analysis.significant_correlations:
        return

    _console.print("[bold]Significant Correlations:[/bold]")
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

    _console.print(f"[bold]Low Performing Test Cases ({len(analysis.low_performers)}):[/bold]")

    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("Test Case")
    table.add_column("Metric")
    table.add_column("Score", justify="right")
    table.add_column("Threshold", justify="right")
    table.add_column("Potential Causes")

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

    _console.print("[bold]Insights:[/bold]")
    for insight in analysis.insights:
        _console.print(f"  • {insight}")
    _console.print()


def _display_nlp_analysis(nlp_analysis) -> None:
    """Display NLP analysis results."""

    _console.print("\n[bold cyan]NLP Analysis[/bold cyan]\n")

    if nlp_analysis.question_stats:
        _console.print("[bold]Text Statistics (Questions):[/bold]")
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

        _console.print(table)
        _console.print()

    if nlp_analysis.question_types:
        _console.print("[bold]Question Type Distribution:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Type")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")
        table.add_column("Avg Scores")

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
        _console.print("[bold]Top Keywords:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Keyword")
        table.add_column("Frequency", justify="right")
        table.add_column("TF-IDF Score", justify="right")

        for keyword in nlp_analysis.top_keywords[:10]:
            table.add_row(keyword.keyword, str(keyword.frequency), f"{keyword.tfidf_score:.3f}")

        _console.print(table)
        _console.print()

    if nlp_analysis.insights:
        _console.print("[bold]NLP Insights:[/bold]")
        for insight in nlp_analysis.insights:
            _console.print(f"  • {insight}")
        _console.print()


def _display_causal_analysis(causal_analysis) -> None:
    """Display causal analysis results."""

    _console.print("\n[bold magenta]Causal Analysis[/bold magenta]\n")

    significant_impacts = causal_analysis.significant_impacts
    if significant_impacts:
        _console.print("[bold]Significant Factor-Metric Relationships:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Factor")
        table.add_column("Metric")
        table.add_column("Direction")
        table.add_column("Strength")
        table.add_column("Correlation", justify="right")
        table.add_column("p-value", justify="right")

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
        _console.print("[bold]Strong Causal Relationships (confidence > 0.7):[/bold]")
        for rel in strong_relationships[:5]:
            direction_arrow = "↑" if rel.direction.value == "positive" else "↓"
            _console.print(
                f"  • {rel.cause.value} → {rel.effect_metric} {direction_arrow} "
                f"(confidence: {rel.confidence:.2f})"
            )
        _console.print()

    if causal_analysis.root_causes:
        _console.print("[bold]Root Cause Analysis:[/bold]")
        for rc in causal_analysis.root_causes:
            primary_str = ", ".join(f.value for f in rc.primary_causes)
            _console.print(f"  [bold]{rc.metric_name}:[/bold]")
            _console.print(f"    Primary causes: {primary_str}")
            if rc.contributing_factors:
                contributing_str = ", ".join(f.value for f in rc.contributing_factors)
                _console.print(f"    Contributing factors: {contributing_str}")
            if rc.explanation:
                _console.print(f"    Explanation: {rc.explanation}")
        _console.print()

    if causal_analysis.interventions:
        _console.print("[bold]Recommended Interventions:[/bold]")
        for intervention in causal_analysis.interventions[:5]:
            priority_str = {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}.get(
                intervention.priority, f"Priority {intervention.priority}"
            )
            _console.print(f"  [{priority_str}] {intervention.intervention}")
            _console.print(f"      Target: {intervention.target_metric}")
            _console.print(f"      Expected: {intervention.expected_impact}")
        _console.print()

    if causal_analysis.insights:
        _console.print("[bold]Causal Insights:[/bold]")
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


def _perform_playbook_analysis(run, enable_llm: bool, profile: str | None):
    """Perform playbook-based improvement analysis."""

    from evalvault.adapters.outbound.improvement.insight_generator import InsightGenerator
    from evalvault.adapters.outbound.improvement.pattern_detector import PatternDetector
    from evalvault.adapters.outbound.improvement.playbook_loader import get_default_playbook
    from evalvault.domain.services.improvement_guide_service import ImprovementGuideService

    _console.print("\n[bold cyan]Playbook-based Improvement Analysis[/bold cyan]\n")

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
        _console.print("[dim]LLM-based insight generation enabled[/dim]")

    service = ImprovementGuideService(
        pattern_detector=detector,
        insight_generator=insight_generator,
        playbook=playbook,
        enable_llm_enrichment=enable_llm,
    )

    with _console.status("[bold green]Analyzing patterns and generating recommendations..."):
        report = service.generate_report(run, include_llm_analysis=enable_llm)

    _display_improvement_report(report)
    return report


def _display_improvement_report(report) -> None:
    """Display improvement report in console."""

    from evalvault.domain.entities.improvement import ImprovementPriority

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

    _console.print(
        Panel(summary, title="[bold cyan]Improvement Analysis[/bold cyan]", border_style="cyan")
    )

    if not report.guides:
        _console.print("[yellow]No improvement guides generated.[/yellow]")
        return

    critical_guides = report.get_critical_guides()
    if critical_guides:
        _console.print("\n[bold red]Critical Issues (P0)[/bold red]")
        for guide in critical_guides:
            _display_guide(guide)

    high_priority = [g for g in report.guides if g.priority == ImprovementPriority.P1_HIGH]
    if high_priority:
        _console.print("\n[bold yellow]High Priority (P1)[/bold yellow]")
        for guide in high_priority[:3]:
            _display_guide(guide)

    medium_priority = [g for g in report.guides if g.priority == ImprovementPriority.P2_MEDIUM]
    if medium_priority:
        _console.print("\n[bold blue]Medium Priority (P2)[/bold blue]")
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
            _console.print(f"     Pattern: {primary.pattern_type.value}")
            _console.print(
                f"     Affected: {primary.affected_count}/{primary.total_count} test cases "
                f"({primary.affected_ratio:.1%})"
            )
        elif guide.evidence.total_failures > 0:
            _console.print(f"     Failures: {guide.evidence.total_failures} test cases")
            _console.print(f"     Avg Score (failures): {guide.evidence.avg_score_failures:.3f}")

    if guide.actions:
        _console.print("     [bold]Recommended Actions:[/bold]")
        for action in guide.actions[:3]:
            effort_color = {"low": "green", "medium": "yellow", "high": "red"}.get(
                action.effort, "white"
            )
            _console.print(f"       • {action.title}")
            if action.description:
                if len(action.description) > 60:
                    _console.print(f"         [dim]{action.description[:60]}...[/dim]")
                else:
                    _console.print(f"         [dim]{action.description}[/dim]")
            _console.print(
                f"         Expected: +{action.expected_improvement:.1%} | Effort: "
                f"[{effort_color}]{action.effort}[/{effort_color}]"
            )

    if guide.verification_command:
        _console.print(f"     [dim]Verify: {guide.verification_command}[/dim]")


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
        content += "\n\n" + improvement_report.to_markdown()

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(content)


__all__ = [
    "register_analyze_commands",
    "_perform_playbook_analysis",
    "_display_improvement_report",
]
