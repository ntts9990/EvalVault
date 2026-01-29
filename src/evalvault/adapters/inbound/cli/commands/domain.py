"""Domain memory management commands for EvalVault CLI."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.domain_memory import build_domain_memory_adapter
from evalvault.config.domain_config import (
    generate_domain_template,
    list_domains,
    load_domain_config,
    save_domain_config,
)
from evalvault.domain.entities.memory import FactType
from evalvault.domain.services.domain_learning_hook import DomainLearningHook
from evalvault.domain.services.embedding_overlay import build_cluster_facts
from evalvault.ports.outbound.domain_memory_port import DomainMemoryPort

from ..utils.options import memory_db_option
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

    memory_app = typer.Typer(name="memory", help="Domain memory utilities.")
    domain_app.add_typer(memory_app, name="memory")

    def _load_memory_adapter(db_path: Path | None) -> DomainMemoryPort:
        return build_domain_memory_adapter(db_path=db_path)

    def _truncate(text: str, max_length: int = 40) -> str:
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def _format_list(values: list[str], max_items: int = 3) -> str:
        if not values:
            return "-"
        display = ", ".join(values[:max_items])
        if len(values) > max_items:
            display += "..."
        return display

    def _load_embedding_rows(file_path: Path) -> list[dict[str, Any]]:
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            with file_path.open(encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader]
        if suffix in {".parquet", ".pq"}:
            try:
                import pandas as pd  # type: ignore
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise typer.BadParameter(
                    "Reading Parquet exports requires pandas. Install via `uv pip install pandas pyarrow`."
                ) from exc
            df = pd.read_parquet(file_path)
            return df.to_dict(orient="records")
        raise typer.BadParameter(
            "Unsupported embedding file format. Use CSV or Parquet exported by `evalvault phoenix export-embeddings`."
        )

    @memory_app.command("stats")
    def memory_stats(
        domain: str | None = typer.Option(
            None,
            "--domain",
            "-d",
            help="Filter by domain (leave empty for global stats).",
        ),
        memory_db: Path | None = memory_db_option(),
    ) -> None:
        """Show aggregated domain memory statistics."""

        adapter = _load_memory_adapter(memory_db)
        stats = adapter.get_statistics(domain=domain)
        title = f"Domain Memory Stats ({domain})" if domain else "Domain Memory Stats"
        table = Table(title=title, show_header=False, box=None, padding=(0, 1))
        table.add_column("Category", style="bold")
        table.add_column("Count", justify="right")
        table.add_row("Facts", str(stats.get("facts", 0)))
        table.add_row("Learnings", str(stats.get("learnings", 0)))
        table.add_row("Behaviors", str(stats.get("behaviors", 0)))
        table.add_row("Contexts", str(stats.get("contexts", 0)))
        console.print(table)
        database_label = "postgres (default)" if memory_db is None else str(memory_db)
        console.print(
            f"[dim]Database:[/dim] {database_label}  |  [dim]Domain:[/dim] {domain or 'all'}\n"
        )

    @memory_app.command("ingest-embeddings")
    def memory_ingest_embeddings(  # noqa: PLR0913
        file: Path = typer.Argument(
            ..., help="CSV/Parquet exported via `evalvault phoenix export-embeddings`."
        ),
        domain: str = typer.Option(
            "insurance", "--domain", "-d", help="Domain to store the facts."
        ),
        language: str = typer.Option(
            "ko", "--language", "-l", help="Language tag for stored facts."
        ),
        min_cluster_size: int = typer.Option(
            5, "--min-cluster-size", help="Skip clusters smaller than this size."
        ),
        sample_size: int = typer.Option(
            3, "--sample-size", help="Number of representative questions per cluster."
        ),
        cluster_key: str = typer.Option(
            "cluster_id", "--cluster-key", help="Column containing the Phoenix cluster identifier."
        ),
        verification_score: float = typer.Option(
            0.4,
            "--verification-score",
            help="Verification score assigned to imported facts (0.0~1.0).",
        ),
        fact_type: str = typer.Option(
            "inferred",
            "--fact-type",
            help="Fact type to use when storing clusters (verified, inferred, contradictory).",
        ),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Print summary without writing to the database."
        ),
        memory_db: Path | None = memory_db_option(),
    ) -> None:
        """Convert Phoenix embedding exports into Domain Memory facts."""

        if min_cluster_size < 1:
            raise typer.BadParameter("--min-cluster-size must be >= 1")
        if sample_size < 1:
            raise typer.BadParameter("--sample-size must be >= 1")
        if not 0.0 < verification_score <= 1.0:
            raise typer.BadParameter("--verification-score must be between 0 and 1")
        if not file.exists():
            console.print(f"[red]Error:[/red] File not found: {file}")
            raise typer.Exit(1)

        fact_type_value = fact_type.lower().strip()
        valid_fact_types = {"verified", "inferred", "contradictory"}
        if fact_type_value not in valid_fact_types:
            raise typer.BadParameter(
                f"--fact-type must be one of {', '.join(sorted(valid_fact_types))}"
            )

        rows = _load_embedding_rows(file)
        if not rows:
            console.print(f"[yellow]No rows found in {file}. Nothing to ingest.[/yellow]\n")
            return

        console.print(f"[dim]Loaded {len(rows)} embedding rows from[/dim] [cyan]{file}[/cyan]")

        fact_type_enum: FactType = fact_type_value  # type: ignore[assignment]

        facts = build_cluster_facts(
            rows,
            domain=domain,
            language=language,
            cluster_key=cluster_key,
            min_cluster_size=min_cluster_size,
            sample_size=sample_size,
            fact_type=fact_type_enum,
            verification_score=verification_score,
        )

        if not facts:
            console.print(
                "[yellow]No clusters met the ingestion thresholds. "
                "Check --cluster-key and --min-cluster-size settings.[/yellow]\n"
            )
            return

        if dry_run:
            console.print(
                f"[cyan]Dry run:[/cyan] {len(facts)} cluster facts would be saved to domain "
                f"[bold]{domain}[/bold] ({language})."
            )
            preview = facts[: min(3, len(facts))]
            for fact in preview:
                console.print(f"  • {fact.subject} → {fact.object[:80]}...")
            console.print()
            return

        adapter = _load_memory_adapter(memory_db)
        for fact in facts:
            adapter.save_fact(fact)

        console.print(
            f"[green]Stored {len(facts)} embedding clusters into domain memory[/green] "
            f"(domain={domain}, language={language})."
        )
        console.print(f"[dim]Database:[/dim] {memory_db}\n")

    @memory_app.command("search")
    def memory_search(
        query: str = typer.Argument(..., help="키워드 또는 문장 형태의 검색 쿼리."),
        domain: str = typer.Option("insurance", "--domain", "-d", help="도메인 이름."),
        language: str = typer.Option("ko", "--language", "-l", help="언어 코드."),
        limit: int = typer.Option(10, "--limit", "-n", help="최대 결과 수."),
        min_score: float = typer.Option(
            0.0,
            "--min-score",
            help="최소 검증 점수 필터 (0.0~1.0).",
        ),
        memory_db: Path | None = memory_db_option(),
    ) -> None:
        """Search factual facts stored in domain memory."""

        if not 0.0 <= min_score <= 1.0:
            console.print("[red]Error:[/red] --min-score must be between 0.0 and 1.0.")
            raise typer.Exit(1)

        adapter = _load_memory_adapter(memory_db)
        facts = adapter.search_facts(
            query=query,
            domain=domain,
            language=language,
            limit=limit * 2,
        )
        results = [fact for fact in facts if fact.verification_score >= min_score][:limit]

        if not results:
            console.print("[yellow]No matching facts found.[/yellow]\n")
            return

        table = Table(title="Factual Facts", header_style="bold cyan")
        table.add_column("Fact ID", style="dim", overflow="fold")
        table.add_column("Subject")
        table.add_column("Predicate")
        table.add_column("Object")
        table.add_column("Score", justify="right")
        table.add_column("Verified", justify="right")

        for fact in results:
            table.add_row(
                fact.fact_id,
                _truncate(fact.subject),
                _truncate(fact.predicate),
                _truncate(fact.object),
                f"{fact.verification_score:.2f}",
                str(fact.verification_count),
            )

        console.print(table)
        console.print(f"[dim]Query:[/dim] {query}  |  [dim]Domain:[/dim] {domain}\n")

    @memory_app.command("behaviors")
    def memory_behaviors(
        context: str = typer.Option(
            "",
            "--context",
            "-c",
            help="행동 검색에 사용할 컨텍스트 (옵션).",
        ),
        domain: str = typer.Option("insurance", "--domain", "-d", help="도메인 이름."),
        language: str = typer.Option("ko", "--language", "-l", help="언어 코드."),
        limit: int = typer.Option(5, "--limit", "-n", help="최대 결과 수."),
        min_success: float = typer.Option(
            0.0,
            "--min-success",
            help="최소 성공률 필터 (0.0~1.0).",
        ),
        memory_db: Path | None = memory_db_option(),
    ) -> None:
        """List reusable behaviors from domain memory."""

        if not 0.0 <= min_success <= 1.0:
            console.print("[red]Error:[/red] --min-success must be between 0.0 and 1.0.")
            raise typer.Exit(1)

        adapter = _load_memory_adapter(memory_db)
        behaviors = adapter.search_behaviors(
            context=context or "",
            domain=domain,
            language=language,
            limit=limit * 3,
        )
        results = [b for b in behaviors if b.success_rate >= min_success][:limit]

        if not results:
            console.print("[yellow]No behaviors matched the filters.[/yellow]\n")
            return

        table = Table(title="Behavior Patterns", header_style="bold cyan")
        table.add_column("Behavior ID", style="dim", overflow="fold")
        table.add_column("Description")
        table.add_column("Success", justify="right")
        table.add_column("Token Δ", justify="right")
        table.add_column("Actions")

        for behavior in results:
            action_preview = ", ".join(behavior.action_sequence[:3])
            if len(behavior.action_sequence) > 3:
                action_preview += "..."
            table.add_row(
                behavior.behavior_id,
                _truncate(behavior.description, max_length=50),
                f"{behavior.success_rate:.2f}",
                str(behavior.token_savings),
                action_preview or "-",
            )

        console.print(table)
        console.print(
            f"[dim]Context provided:[/dim] {'yes' if context else 'no'}"
            f"  |  [dim]Domain:[/dim] {domain}\n"
        )

    @memory_app.command("learnings")
    def memory_learnings(
        domain: str = typer.Option("insurance", "--domain", "-d", help="도메인 이름."),
        language: str = typer.Option("ko", "--language", "-l", help="언어 코드."),
        limit: int = typer.Option(5, "--limit", "-n", help="최대 결과 수."),
        memory_db: Path | None = memory_db_option(),
    ) -> None:
        """Display experiential learning entries stored in memory."""

        adapter = _load_memory_adapter(memory_db)
        learnings = adapter.list_learnings(domain=domain, language=language, limit=limit)

        if not learnings:
            console.print("[yellow]No learning memories found for this domain.[/yellow]\n")
            return

        table = Table(title="Learning Memories", header_style="bold cyan")
        table.add_column("Learning ID", style="dim", overflow="fold")
        table.add_column("Run ID", overflow="fold")
        table.add_column("Success Patterns")
        table.add_column("Failed Patterns")

        for learning in learnings:
            table.add_row(
                learning.learning_id,
                learning.run_id or "-",
                _format_list(learning.successful_patterns),
                _format_list(learning.failed_patterns),
            )

        console.print(table)
        console.print(f"[dim]Domain:[/dim] {domain}  |  [dim]Language:[/dim] {language}\n")

    @memory_app.command("evolve")
    def memory_evolve(
        domain: str = typer.Option(..., "--domain", "-d", help="도메인 이름."),
        language: str = typer.Option("ko", "--language", "-l", help="언어 코드."),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="데이터 변경 없이 예상 작업만 출력합니다.",
        ),
        yes: bool = typer.Option(
            False,
            "--yes",
            "-y",
            help="확인 프롬프트를 건너뜁니다.",
        ),
        memory_db: Path | None = memory_db_option(),
    ) -> None:
        """Run consolidation/cleanup on stored memories."""

        adapter = _load_memory_adapter(memory_db)

        if dry_run:
            stats = adapter.get_statistics(domain=domain)
            console.print(
                "[cyan]Dry run:[/cyan] consolidation, forgetting, and decay would run with "
                f"{stats.get('facts', 0)} facts and {stats.get('behaviors', 0)} behaviors."
            )
            console.print("[dim]Use --yes to skip confirmation when executing for real.[/dim]\n")
            return

        if not yes:
            confirmed = typer.confirm(
                f"Run memory evolution for domain '{domain}'? This operation modifies stored data."
            )
            if not confirmed:
                console.print("[yellow]Cancelled memory evolution.[/yellow]\n")
                return

        hook = DomainLearningHook(adapter)
        result = hook.run_evolution(domain=domain, language=language)

        table = Table(title="Evolution Result", header_style="bold cyan")
        table.add_column("Operation")
        table.add_column("Count", justify="right")
        table.add_row("Consolidated", str(result.get("consolidated", 0)))
        table.add_row("Forgotten", str(result.get("forgotten", 0)))
        table.add_row("Decayed", str(result.get("decayed", 0)))
        console.print(table)
        console.print(f"[green]Domain memory evolution completed for '{domain}'.[/green]\n")

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
