"""Init command for new user onboarding."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from evalvault.adapters.outbound.dataset.templates import (
    render_dataset_template_csv,
    render_dataset_template_json,
    render_dataset_template_xlsx,
    render_method_input_template_json,
)


def register_init_command(app: typer.Typer, console: Console) -> None:
    """Register the init command for onboarding.

    Args:
        app: Typer application instance
        console: Rich console instance
    """

    @app.command()
    def init(
        output_dir: Path = typer.Option(
            Path.cwd(),
            "--output-dir",
            "-d",
            help="Directory to initialize (default: current directory)",
        ),
        skip_env: bool = typer.Option(
            False,
            "--skip-env",
            help="Skip .env file creation",
        ),
        skip_sample: bool = typer.Option(
            False,
            "--skip-sample",
            help="Skip sample dataset creation",
        ),
        skip_templates: bool = typer.Option(
            False,
            "--skip-templates",
            help="Skip dataset template creation",
        ),
    ) -> None:
        """Initialize EvalVault in a new project.

        This command helps you get started by:
        1. Creating a .env file with required API keys
        2. Generating a sample dataset
        3. Creating empty dataset templates (JSON/CSV/XLSX)
        4. Providing quick start commands

        Examples:
          # Initialize in current directory
          uv run evalvault init

          # Initialize in a specific directory
          uv run evalvault init --output-dir ./my-project

          # Skip .env creation (if already exists)
          uv run evalvault init --skip-env
        """
        console.print("\n[bold cyan]EvalVault Initialization[/bold cyan]\n")

        # Ensure output directory exists
        output_dir = output_dir.expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Create .env file
        if not skip_env:
            _create_env_file(console, output_dir)

        # Step 2: Create sample dataset
        if not skip_sample:
            _create_sample_dataset(console, output_dir)

        # Step 3: Create dataset templates
        if not skip_templates:
            _create_dataset_templates(console, output_dir)

        # Step 4: Show quick start guide
        _show_quick_start(console, output_dir)

        console.print(
            "\n[bold green]Initialization complete![/bold green] You're ready to start evaluating.\n"
        )


def _create_env_file(console: Console, output_dir: Path) -> None:
    """Create .env file with API key placeholders."""
    env_path = output_dir / ".env"

    if env_path.exists():
        console.print(f"[yellow].env file already exists at {env_path}[/yellow]\n")
        return

    console.print("[bold]Step 1: Configure API Keys[/bold]")

    env_content = """# EvalVault Configuration

# OpenAI (recommended)
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-5-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Optional: Langfuse Tracking
# LANGFUSE_PUBLIC_KEY=pk-lf-...
# LANGFUSE_SECRET_KEY=sk-lf-...
# LANGFUSE_HOST=http://localhost:3000

# Optional: Phoenix Observability
# PHOENIX_ENABLED=true
# PHOENIX_ENDPOINT=http://localhost:6006
"""

    env_path.write_text(env_content, encoding="utf-8")
    console.print(f"[green]Created .env file at {env_path}[/green]")
    console.print("[dim]Remember to add your actual API key before running![/dim]\n")


def _create_sample_dataset(console: Console, output_dir: Path) -> None:
    """Create a sample dataset file."""
    console.print("[bold]Step 2: Create Sample Dataset[/bold]\n")

    dataset_path = output_dir / "sample_dataset.json"

    if dataset_path.exists():
        console.print(f"[yellow]Sample dataset already exists at {dataset_path}[/yellow]\n")
        return

    sample_dataset = {
        "name": "sample-qa-dataset",
        "version": "1.0.0",
        "metadata": {
            "description": "Sample dataset for getting started with EvalVault",
            "domain": "general",
        },
        "thresholds": {
            "faithfulness": 0.7,
            "answer_relevancy": 0.7,
        },
        "test_cases": [
            {
                "id": "tc-001",
                "question": "What is the capital of France?",
                "answer": "The capital of France is Paris.",
                "contexts": [
                    "Paris is the capital and largest city of France.",
                    "France is a country in Western Europe.",
                ],
                "ground_truth": "Paris",
            },
            {
                "id": "tc-002",
                "question": "What is machine learning?",
                "answer": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
                "contexts": [
                    "Machine learning is a method of data analysis that automates analytical model building.",
                    "It is a branch of artificial intelligence based on the idea that systems can learn from data.",
                ],
                "ground_truth": "Machine learning is a subset of AI that allows systems to learn from data.",
            },
        ],
    }

    dataset_path.write_text(
        json.dumps(sample_dataset, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    console.print(f"[green]Created sample dataset at {dataset_path}[/green]")
    console.print("[dim]This dataset contains 2 test cases for quick testing[/dim]\n")


def _create_dataset_templates(console: Console, output_dir: Path) -> None:
    """Create empty dataset templates (JSON/CSV/XLSX)."""
    console.print("[bold]Step 3: Create Dataset Templates[/bold]\n")

    templates_dir = output_dir / "dataset_templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    template_specs = [
        ("dataset_template.json", render_dataset_template_json()),
        ("dataset_template.csv", render_dataset_template_csv()),
        ("method_input_template.json", render_method_input_template_json()),
    ]

    created_any = False
    for filename, content in template_specs:
        template_path = templates_dir / filename
        if template_path.exists():
            console.print(f"[yellow]Template already exists at {template_path}[/yellow]")
            continue
        template_path.write_text(content, encoding="utf-8")
        created_any = True

    xlsx_path = templates_dir / "dataset_template.xlsx"
    if xlsx_path.exists():
        console.print(f"[yellow]Template already exists at {xlsx_path}[/yellow]")
    else:
        try:
            xlsx_path.write_bytes(render_dataset_template_xlsx())
            created_any = True
        except Exception as exc:
            console.print(f"[yellow]Skipping XLSX template: {exc}[/yellow]")

    if created_any:
        console.print(f"[green]Created dataset templates at {templates_dir}[/green]\n")
    else:
        console.print("[dim]Dataset templates already exist.[/dim]\n")


def _show_quick_start(console: Console, output_dir: Path) -> None:
    """Display quick start commands."""
    console.print("[bold]Step 4: Quick Start Commands[/bold]\n")

    commands = """# Run a quick evaluation with the quick preset
uv run evalvault run --preset quick sample_dataset.json

# Run production-grade evaluation
uv run evalvault run --preset production sample_dataset.json

# Run summarization evaluation (summary metrics)
uv run evalvault run --summary sample_dataset.json

# Run with output file
uv run evalvault run --preset production sample_dataset.json -o results.json

# Run comprehensive evaluation (all metrics)
uv run evalvault run --preset comprehensive sample_dataset.json

# View available metrics
uv run evalvault metrics

# Check configuration
uv run evalvault config
"""

    syntax = Syntax(
        commands,
        "bash",
        theme="monokai",
        line_numbers=False,
    )

    console.print(
        Panel(
            syntax,
            title="[bold]Quick Start Commands[/bold]",
            border_style="cyan",
        )
    )

    console.print(
        "\n[bold]Next Steps:[/bold]",
    )
    console.print("  1. Update .env with your API key")
    console.print(
        "  2. Try the quick preset: [cyan]uv run evalvault run --preset quick sample_dataset.json[/cyan]"
    )
    console.print("  3. View full documentation: [cyan]uv run evalvault run --help[/cyan]")


__all__ = ["register_init_command"]
