"""`evalvault generate` 명령을 등록하는 모듈."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from evalvault.domain.services.kg_generator import KnowledgeGraphGenerator
from evalvault.domain.services.synthetic_qa_generator import (
    SyntheticQAConfig,
    SyntheticQAGenerator,
)
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
            help="Generation method: 'basic', 'knowledge_graph', or 'synthetic'.",
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
        profile: str = typer.Option(
            None,
            "--profile",
            "-p",
            help="Model profile for LLM-based generation (required for 'synthetic' method).",
        ),
        language: str = typer.Option(
            "ko",
            "--language",
            "-l",
            help="Language for Q&A generation: 'ko' or 'en'.",
        ),
        include_no_answer: bool = typer.Option(
            True,
            "--include-no-answer/--no-include-no-answer",
            help="Include no-answer test cases for hallucination detection.",
        ),
    ) -> None:
        """Generate a synthetic test dataset from documents.

        Create test cases with questions, answers, and contexts from your
        document corpus for RAG evaluation.

        \b
        Methods:
          • basic          — Random chunk sampling with template-based Q&A.
          • knowledge_graph — Extract entities/relations for structured Q&A.
          • synthetic      — LLM-based Q&A with ground truth (requires --profile).

        \b
        Examples:
          # Generate 10 questions from a single document
          evalvault generate doc.txt -n 10 -o testset.json

          # Generate from multiple documents
          evalvault generate doc1.txt doc2.txt doc3.txt -n 50

          # Use knowledge graph method for better quality
          evalvault generate docs/*.txt -m knowledge_graph -n 20

          # Use LLM-based synthetic generation with ground truth
          evalvault generate doc.txt -m synthetic -p local -n 20

          # Synthetic with English language
          evalvault generate doc.txt -m synthetic -p openai -l en -n 10

          # Custom chunk size for longer contexts
          evalvault generate doc.txt -c 1000 -n 10

          # Name your dataset
          evalvault generate doc.txt -N "insurance-qa-v1"

        \b
        Output Format (JSON):
          {
            "name": "...",
            "test_cases": [
              {"id": "tc-001", "question": "...", "answer": "...", "contexts": [...],
               "ground_truth": "..."}
            ]
          }

        \b
        See also:
          evalvault run       — Evaluate generated testsets
          evalvault kg build  — Build knowledge graphs from documents
        """

        allowed_methods = ("basic", "knowledge_graph", "synthetic")
        validate_choice(method, allowed_methods, console, value_label="method")

        # Synthetic method requires profile
        if method == "synthetic" and not profile:
            console.print("[red]Error:[/red] --profile is required for 'synthetic' method.")
            console.print("Example: evalvault generate doc.txt -m synthetic -p local")
            raise typer.Exit(1)

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
            elif method == "synthetic":
                # Load LLM adapter based on profile
                from evalvault.config import load_model_config

                model_config = load_model_config(profile)
                llm = model_config.create_llm_adapter()

                console.print(f"[dim]LLM: {llm.get_model_name()}[/dim]")

                syn_generator = SyntheticQAGenerator(llm)
                syn_config = SyntheticQAConfig(
                    num_questions=num_questions,
                    chunk_size=chunk_size,
                    dataset_name=name,
                    language=language,
                    include_no_answer=include_no_answer,
                )

                def progress_cb(current: int, total: int) -> None:
                    update_stage(1, current)

                dataset = syn_generator.generate(doc_texts, syn_config, progress_cb)

                # Show generation stats
                meta = dataset.metadata
                console.print(
                    f"[dim]Generated: {meta.get('questions_generated', 0)} → "
                    f"Filtered: {meta.get('questions_final', 0)}[/dim]"
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
