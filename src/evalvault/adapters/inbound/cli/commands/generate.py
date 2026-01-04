"""`evalvault generate` 명령을 등록하는 모듈."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from evalvault.domain.services.kg_generator import KnowledgeGraphGenerator
from evalvault.domain.services.testset_generator import (
    BasicTestsetGenerator,
    GenerationConfig,
)

from ..utils.validators import validate_choice


def register_generate_commands(app: typer.Typer, console: Console) -> None:
    """Attach the `generate` command to the given Typer app."""

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
            "-c",
            help="Chunk size for document splitting.",
        ),
        name: str = typer.Option(
            "generated-testset",
            "--name",
            "-N",
            help="Dataset name.",
        ),
    ) -> None:
        """Generate a synthetic test dataset from documents."""

        allowed_methods = ("basic", "knowledge_graph")
        validate_choice(method, allowed_methods, console, value_label="method")

        console.print("\n[bold]EvalVault[/bold] - Testset Generation")
        console.print(f"Documents: [cyan]{len(documents)}[/cyan]")
        console.print(f"Target questions: [cyan]{num_questions}[/cyan]")
        console.print(f"Method: [cyan]{method}[/cyan]\n")

        with console.status("[bold green]Reading documents..."):
            doc_texts = []
            for doc_path in documents:
                with open(doc_path, encoding="utf-8") as file:
                    doc_texts.append(file.read())
            console.print(f"[green]Loaded {len(doc_texts)} documents[/green]")

        with console.status("[bold green]Generating testset..."):
            if method == "knowledge_graph":
                generator = KnowledgeGraphGenerator()
                generator.build_graph(doc_texts)
                stats = generator.get_statistics()
                console.print(
                    "[dim]Knowledge Graph: "
                    f"{stats['num_entities']} entities, {stats['num_relations']} relations[/dim]"
                )
                dataset = generator.generate_dataset(
                    num_questions=num_questions,
                    name=name,
                    version="1.0.0",
                )
            else:
                generator = BasicTestsetGenerator()
                config = GenerationConfig(
                    num_questions=num_questions,
                    chunk_size=chunk_size,
                    dataset_name=name,
                )
                dataset = generator.generate(doc_texts, config)

            console.print(f"[green]Generated {len(dataset.test_cases)} test cases[/green]")

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

            with open(output, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)

            console.print(f"[green]Testset saved to {output}[/green]\n")


__all__ = ["register_generate_commands"]
