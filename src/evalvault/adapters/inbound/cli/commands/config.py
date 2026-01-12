"""Configuration/diagnostics commands for EvalVault CLI."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.metrics.registry import list_metric_specs


def register_config_commands(app: typer.Typer, console: Console) -> None:
    """Attach config/metrics commands to the root Typer app."""

    @app.command()
    def metrics():
        """List available evaluation metrics."""

        console.print("\n[bold]Available Metrics[/bold]\n")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="bold")
        table.add_column("Description")
        table.add_column("Requires Ground Truth", justify="center")

        for spec in list_metric_specs():
            needs_gt = "[green]Yes[/green]" if spec.requires_ground_truth else "[red]No[/red]"
            table.add_row(spec.name, spec.description, needs_gt)

        console.print(table)
        console.print("\n[dim]Use --metrics flag with 'run' command to specify metrics.[/dim]")
        console.print(
            "[dim]Example: evalvault run data.csv --metrics faithfulness,answer_relevancy[/dim]\n"
        )

    @app.command()
    def config() -> None:
        """Show current configuration."""

        settings = Settings()
        profile_name = settings.evalvault_profile
        if profile_name:
            settings = apply_profile(settings, profile_name)

        console.print("\n[bold]Current Configuration[/bold]\n")
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
        elif settings.llm_provider == "vllm":
            api_key_status = (
                "[green]Set[/green]" if settings.vllm_api_key else "[yellow]Not set[/yellow]"
            )
            table_llm.add_row("vLLM API Key", api_key_status)
            table_llm.add_row("vLLM Model", settings.vllm_model)
            table_llm.add_row("vLLM Embedding", settings.vllm_embedding_model)
            table_llm.add_row("vLLM Base URL", settings.vllm_base_url)
            table_llm.add_row(
                "vLLM Embedding Base URL",
                settings.vllm_embedding_base_url or "[dim]Same as vLLM Base URL[/dim]",
            )
            table_llm.add_row("vLLM Timeout", f"{settings.vllm_timeout}s")
        else:
            api_key_status = (
                "[green]Set[/green]" if settings.openai_api_key else "[red]Not set[/red]"
            )
            table_llm.add_row("OpenAI API Key", api_key_status)
            table_llm.add_row("OpenAI Model", settings.openai_model)
            table_llm.add_row("OpenAI Embedding", settings.openai_embedding_model)
            table_llm.add_row(
                "OpenAI Base URL",
                settings.openai_base_url or "[dim]Default[/dim]",
            )
        console.print(table_llm)
        console.print()

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
        console.print(
            "[dim]  evalvault run data.json --profile prod --metrics faithfulness[/dim]\n"
        )


__all__ = ["register_config_commands"]
