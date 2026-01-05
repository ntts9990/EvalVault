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

from ..utils.progress import multi_stage_progress
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
            help="Generation method: 'basic' (random chunks) or 'knowledge_graph' (KG-based).",
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
            help="Chunk size (in characters) for document splitting.",
        ),
        name: str = typer.Option(
            "generated-testset",
            "--name",
            "-N",
            help="Name for the generated dataset.",
        ),
    ) -> None:
        """Generate a synthetic test dataset from documents.

        Create test cases with questions, answers, and contexts from your
        document corpus for RAG evaluation.

        \b
        Methods:
          • basic          — Random chunk sampling with simple Q&A generation.
          • knowledge_graph — Extract entities/relations for structured Q&A.

        \b
        Examples:
          # Generate 10 questions from a single document
          evalvault generate doc.txt -n 10 -o testset.json

          # Generate from multiple documents
          evalvault generate doc1.txt doc2.txt doc3.txt -n 50

          # Use knowledge graph method for better quality
          evalvault generate docs/*.txt -m knowledge_graph -n 20

          # Custom chunk size for longer contexts
          evalvault generate doc.txt -c 1000 -n 10

          # Name your dataset
          evalvault generate doc.txt -N "insurance-qa-v1"

        \b
        Output Format (JSON):
          {
            "name": "...",
            "test_cases": [
              {"id": "tc-001", "question": "...", "answer": "...", "contexts": [...]}
            ]
          }

        \b
        See also:
          evalvault run       — Evaluate generated testsets
          evalvault kg build  — Build knowledge graphs from documents
        """

        allowed_methods = ("basic", "knowledge_graph")
        validate_choice(method, allowed_methods, console, value_label="method")

        console.print("\n[bold]EvalVault[/bold] - Testset Generation")
        console.print(f"Documents: [cyan]{len(documents)}[/cyan]")
        console.print(f"Target questions: [cyan]{num_questions}[/cyan]")
        console.print(f"Method: [cyan]{method}[/cyan]\n")

        stages = [
            ("Reading documents", len(documents)),
            ("Generating testset", num_questions),
            ("Saving results", 1),
        ]

        with multi_stage_progress(console, stages) as update_stage:
            doc_texts = []
            for idx, doc_path in enumerate(documents, start=1):
                with open(doc_path, encoding="utf-8") as file:
                    doc_texts.append(file.read())
                update_stage(0, idx)
            console.print(f"[green]Loaded {len(doc_texts)} documents[/green]")

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
            update_stage(1, len(dataset.test_cases))

            console.print(f"[green]Generated {len(dataset.test_cases)} test cases[/green]")
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
            update_stage(2, 1)

        console.print(f"[green]Testset saved to {output}[/green]\n")


__all__ = ["register_generate_commands"]
