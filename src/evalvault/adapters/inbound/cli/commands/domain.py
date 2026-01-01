"""Domain memory management commands for EvalVault CLI."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from evalvault.config.domain_config import (
    generate_domain_template,
    list_domains,
    load_domain_config,
    save_domain_config,
)

from ..utils.validators import parse_csv_option, validate_choices


def create_domain_app(console: Console) -> typer.Typer:
    """Create the domain Typer sub-application."""

    domain_app = typer.Typer(name="domain", help="Domain memory management.")

    @domain_app.command("init")
    def domain_init(
        domain: str = typer.Argument(..., help="Domain name (e.g., 'insurance', 'medical')"),
        languages: str = typer.Option(
            "ko,en",
            "--languages",
            "-l",
            help="Supported languages (comma-separated)",
        ),
        description: str = typer.Option(
            "",
            "--description",
            "-d",
            help="Domain description",
        ),
        force: bool = typer.Option(
            False,
            "--force",
            "-f",
            help="Overwrite existing config",
        ),
    ) -> None:
        """Initialize domain memory configuration."""

        lang_list = parse_csv_option(languages)
        valid_languages = ("ko", "en")
        validate_choices(
            lang_list,
            valid_languages,
            console,
            value_label="language",
            available_label="language",
        )

        config_dir = Path("config/domains")
        domain_dir = config_dir / domain

        if domain_dir.exists() and not force:
            console.print(f"[yellow]Domain '{domain}' already exists.[/yellow]")
            console.print("Use --force to overwrite.")
            raise typer.Exit(1)

        console.print(f"\n[bold]Initializing domain:[/bold] {domain}")
        console.print(f"Languages: [cyan]{', '.join(lang_list)}[/cyan]")
        if description:
            console.print(f"Description: [dim]{description}[/dim]")
        console.print()

        with console.status("[bold green]Creating domain configuration..."):
            template = generate_domain_template(
                domain=domain,
                languages=lang_list,
                description=description,
            )
            config_path = save_domain_config(domain, template, config_dir)

            for lang in lang_list:
                terms_file = domain_dir / f"terms_dictionary_{lang}.json"
                if not terms_file.exists():
                    terms_template = {
                        "version": "1.0.0",
                        "language": lang,
                        "domain": domain,
                        "description": f"{domain.capitalize()} domain {lang} terminology",
                        "terms": {},
                        "categories": {},
                    }
                    with open(terms_file, "w", encoding="utf-8") as file:
                        json.dump(terms_template, file, indent=2, ensure_ascii=False)

        console.print(f"[green]Domain '{domain}' initialized successfully.[/green]")
        console.print("\n[bold]Created files:[/bold]")
        console.print(f"  Config: {config_path}")
        for lang in lang_list:
            console.print(f"  Terms ({lang}): {domain_dir / f'terms_dictionary_{lang}.json'}")

        console.print("\n[dim]Next steps:[/dim]")
        console.print(f"  1. Edit {config_path} to customize settings")
        console.print("  2. Add terms to terms_dictionary_*.json files")
        console.print(f"  3. Use 'evalvault domain show {domain}' to view config\n")

    @domain_app.command("list")
    def domain_list_cmd() -> None:
        """List all configured domains."""

        console.print("\n[bold]Configured Domains[/bold]\n")
        domains = list_domains()

        if not domains:
            console.print("[yellow]No domains configured.[/yellow]")
            console.print("[dim]Use 'evalvault domain init <name>' to create one.[/dim]\n")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Domain", style="bold")
        table.add_column("Languages")
        table.add_column("Learning")
        table.add_column("Description")

        for domain_name in domains:
            try:
                config = load_domain_config(domain_name)
                langs = ", ".join(config.metadata.supported_languages)
                learning = (
                    "[green]Enabled[/green]" if config.learning.enabled else "[dim]Disabled[/dim]"
                )
                desc = (
                    config.metadata.description[:40] + "..."
                    if len(config.metadata.description) > 40
                    else config.metadata.description
                )
                table.add_row(domain_name, langs, learning, desc)
            except Exception as exc:  # pragma: no cover - defensive logging
                table.add_row(domain_name, "[red]Error[/red]", "-", str(exc)[:30])

        console.print(table)
        console.print(f"\n[dim]Found {len(domains)} domain(s)[/dim]\n")

    @domain_app.command("show")
    def domain_show(domain: str = typer.Argument(..., help="Domain name to show")) -> None:
        """Show domain configuration details."""

        console.print(f"\n[bold]Domain Configuration: {domain}[/bold]\n")
        try:
            config = load_domain_config(domain)
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] Domain '{domain}' not found.")
            console.print(f"[dim]Use 'evalvault domain init {domain}' to create it.[/dim]\n")
            raise typer.Exit(1)

        console.print("[bold cyan]Metadata[/bold cyan]")
        table_meta = Table(show_header=False, box=None, padding=(0, 2))
        table_meta.add_column("Setting", style="bold")
        table_meta.add_column("Value")
        table_meta.add_row("Domain", config.metadata.domain)
        table_meta.add_row("Version", config.metadata.version)
        table_meta.add_row("Languages", ", ".join(config.metadata.supported_languages))
        table_meta.add_row("Default Language", config.metadata.default_language)
        table_meta.add_row("Description", config.metadata.description or "[dim]None[/dim]")
        console.print(table_meta)
        console.print()

        console.print("[bold cyan]Factual Layer[/bold cyan]")
        table_factual = Table(show_header=False, box=None, padding=(0, 2))
        table_factual.add_column("Setting", style="bold")
        table_factual.add_column("Value")
        for lang in config.metadata.supported_languages:
            glossary = config.factual.glossary.get(lang)
            if glossary:
                table_factual.add_row(f"Glossary ({lang})", glossary)
        if config.factual.shared:
            for name, path in config.factual.shared.items():
                table_factual.add_row(f"Shared ({name})", path)
        console.print(table_factual)
        console.print()

        console.print("[bold cyan]Experiential Layer[/bold cyan]")
        table_exp = Table(show_header=False, box=None, padding=(0, 2))
        table_exp.add_column("Setting", style="bold")
        table_exp.add_column("Value")
        table_exp.add_row("Failure Modes", config.experiential.failure_modes)
        table_exp.add_row("Behavior Handbook", config.experiential.behavior_handbook)
        for lang in config.metadata.supported_languages:
            rel_path = config.experiential.reliability_scores.get(lang)
            if rel_path:
                table_exp.add_row(f"Reliability ({lang})", rel_path)
        console.print(table_exp)
        console.print()

        console.print("[bold cyan]Working Layer[/bold cyan]")
        table_work = Table(show_header=False, box=None, padding=(0, 2))
        table_work.add_column("Setting", style="bold")
        table_work.add_column("Value")
        table_work.add_row("Run Cache", config.working.run_cache)
        table_work.add_row("KG Binding", config.working.kg_binding or "[dim]None[/dim]")
        table_work.add_row("Max Cache Size", f"{config.working.max_cache_size_mb} MB")
        console.print(table_work)
        console.print()

        console.print("[bold cyan]Learning Settings[/bold cyan]")
        table_learn = Table(show_header=False, box=None, padding=(0, 2))
        table_learn.add_column("Setting", style="bold")
        table_learn.add_column("Value")
        status = "[green]Enabled[/green]" if config.learning.enabled else "[red]Disabled[/red]"
        table_learn.add_row("Status", status)
        table_learn.add_row("Min Confidence", f"{config.learning.min_confidence_to_store:.2f}")
        table_learn.add_row(
            "Behavior Extraction", "Yes" if config.learning.behavior_extraction else "No"
        )
        table_learn.add_row("Auto Apply", "Yes" if config.learning.auto_apply else "No")
        table_learn.add_row("Decay Rate", f"{config.learning.decay_rate:.2f}")
        table_learn.add_row("Forget Threshold", f"{config.learning.forget_threshold_days} days")
        console.print(table_learn)
        console.print()

    @domain_app.command("terms")
    def domain_terms(
        domain: str = typer.Argument(..., help="Domain name"),
        language: str = typer.Option(
            None,
            "--language",
            "-l",
            help="Language code (ko, en). Uses default if not specified.",
        ),
        limit: int = typer.Option(
            10,
            "--limit",
            "-n",
            help="Number of terms to show",
        ),
    ) -> None:
        """Show domain terminology dictionary."""

        try:
            config = load_domain_config(domain)
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] Domain '{domain}' not found.")
            raise typer.Exit(1)

        lang = language or config.metadata.default_language

        if not config.supports_language(lang):
            console.print(
                f"[red]Error:[/red] Language '{lang}' not supported by domain '{domain}'."
            )
            console.print(f"Supported: {', '.join(config.metadata.supported_languages)}")
            raise typer.Exit(1)

        glossary_path = config.get_glossary_path(lang)
        if not glossary_path:
            console.print(f"[yellow]No glossary configured for language '{lang}'[/yellow]")
            raise typer.Exit(1)

        config_dir = Path("config/domains")
        terms_file = config_dir / domain / glossary_path

        if not terms_file.exists():
            console.print(f"[yellow]Glossary file not found:[/yellow] {terms_file}")
            raise typer.Exit(1)

        with open(terms_file, encoding="utf-8") as file:
            terms_data = json.load(file)

        console.print(f"\n[bold]Terminology Dictionary: {domain} ({lang})[/bold]\n")

        terms = terms_data.get("terms", {})
        if not terms:
            console.print("[yellow]No terms defined.[/yellow]\n")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Term", style="bold")
        table.add_column("Definition")
        table.add_column("Category")
        table.add_column("Aliases")

        for count, (term, info) in enumerate(terms.items()):
            if count >= limit:
                break
            definition = info.get("definition", "")
            if len(definition) > 50:
                definition = definition[:50] + "..."
            category = info.get("category", "-")
            aliases = ", ".join(info.get("aliases", [])[:2])
            if len(info.get("aliases", [])) > 2:
                aliases += "..."
            table.add_row(term, definition, category, aliases)

        console.print(table)

        total = len(terms)
        if total > limit:
            console.print(
                f"\n[dim]Showing {limit} of {total} terms. Use --limit to show more.[/dim]"
            )
        console.print()

    return domain_app


__all__ = ["create_domain_app"]
