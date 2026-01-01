"""Benchmark subcommands for EvalVault CLI."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table


def create_benchmark_app(console: Console) -> typer.Typer:
    """Create the Typer sub-application for benchmark commands."""

    benchmark_app = typer.Typer(name="benchmark", help="Korean RAG benchmark utilities.")

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
    ) -> None:
        """Run a benchmark suite."""

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
                status = "[green]PASS[/green]" if result.passed else "[red]FAIL[/red]"
                if result.passed:
                    passed += 1
                score = f"{result.score:.2f}" if result.score is not None else "-"
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

    @benchmark_app.command("list")
    def benchmark_list() -> None:
        """List available benchmarks."""

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
        console.print(
            "\n[dim]Use 'evalvault benchmark run --name <name>' to run a benchmark.[/dim]\n"
        )

    return benchmark_app


__all__ = ["create_benchmark_app"]
