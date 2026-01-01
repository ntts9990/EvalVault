"""`evalvault agent` command module.

Operation mode agents for automating evaluation workflows.
Development mode agents are available separately in the `agent/` folder.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from evalvault.config.agent_types import (
    OPERATION_AGENT_CONFIGS,
    AgentType,
    get_agent_config,
)


def register_agent_commands(app: typer.Typer, console: Console) -> None:
    """Register agent commands to the CLI app."""

    agent_app = typer.Typer(
        name="agent",
        help="Operation agents for automating evaluation workflows.",
        no_args_is_help=True,
    )

    @agent_app.command("list")
    def agent_list(
        all_agents: bool = typer.Option(
            False,
            "--all",
            "-a",
            help="Show all agents including development mode agents.",
        ),
    ) -> None:
        """List available operation agents."""
        table = Table(title="Available Agents")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description")
        table.add_column("Mode", style="yellow")
        table.add_column("Services")

        if all_agents:
            from evalvault.config.agent_types import ALL_AGENT_CONFIGS

            configs = ALL_AGENT_CONFIGS
        else:
            configs = OPERATION_AGENT_CONFIGS

        for agent_type, config in configs.items():
            services = (
                ", ".join(config.evalvault_services[:2]) if config.evalvault_services else "-"
            )
            if len(config.evalvault_services) > 2:
                services += "..."

            table.add_row(
                agent_type.value,
                config.name,
                config.description,
                config.mode.value,
                services,
            )

        console.print(table)

        if not all_agents:
            console.print("\n[dim]Tip: Use --all to see development mode agents as well.[/dim]")

    @agent_app.command("info")
    def agent_info(
        agent_type: str = typer.Argument(..., help="Agent type to get info for."),
    ) -> None:
        """Show detailed information about an agent."""
        try:
            atype = AgentType(agent_type)
        except ValueError:
            console.print(f"[red]Unknown agent type: {agent_type}[/red]")
            console.print(f"Available: {', '.join(t.value for t in AgentType.operation_agents())}")
            raise typer.Exit(1)

        config = get_agent_config(atype)

        console.print(f"\n[bold cyan]{config.name}[/bold cyan]")
        console.print(f"Type: {atype.value}")
        console.print(f"Mode: {config.mode.value}")
        console.print(f"Description: {config.description}")
        console.print(f"Independence: {config.independence}")

        if config.evalvault_services:
            console.print("\nEvalVault Services:")
            for svc in config.evalvault_services:
                console.print(f"  - {svc}")

        if config.dependencies:
            console.print("\nDependencies:")
            for dep in config.dependencies:
                console.print(f"  - {dep.value}")

    @agent_app.command("status")
    def agent_status() -> None:
        """Show status of operation agents (placeholder)."""
        console.print("[yellow]Agent status tracking not yet implemented.[/yellow]")
        console.print("\nTo run operation agents, use:")
        console.print("  evalvault agent run <agent-type> [OPTIONS]")
        console.print("\nFor development mode agents, see:")
        console.print("  agent/README.md")

    @agent_app.command("run")
    def agent_run(
        agent_type: str = typer.Argument(..., help="Agent type to run."),
        domain: str | None = typer.Option(
            None,
            "--domain",
            "-d",
            help="Domain for domain-specific agents (e.g., 'insurance').",
        ),
        language: str = typer.Option(
            "ko",
            "--language",
            "-l",
            help="Language for analysis (ko, en).",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Show what would be done without executing.",
        ),
    ) -> None:
        """Run an operation agent.

        NOTE: Full agent execution requires additional setup.
        This command shows what the agent would do.
        """
        try:
            atype = AgentType(agent_type)
        except ValueError:
            console.print(f"[red]Unknown agent type: {agent_type}[/red]")
            available = ", ".join(t.value for t in AgentType.operation_agents())
            console.print(f"Available operation agents: {available}")
            raise typer.Exit(1)

        if atype not in AgentType.operation_agents():
            console.print(f"[red]{agent_type} is a development agent.[/red]")
            console.print("Development agents should be run from the agent/ folder:")
            console.print(f"  cd agent && uv run python main.py --agent-type {agent_type}")
            raise typer.Exit(1)

        config = get_agent_config(atype)
        console.print(f"\n[bold]Running: {config.name}[/bold]")
        console.print(f"Description: {config.description}")

        if domain:
            console.print(f"Domain: {domain}")
        console.print(f"Language: {language}")

        if dry_run:
            console.print("\n[yellow]Dry run mode - showing what would be done:[/yellow]")

        # Show what services would be used
        if config.evalvault_services:
            console.print("\nServices to use:")
            for svc in config.evalvault_services:
                console.print(f"  - {svc}")

        # Agent-specific actions
        if atype == AgentType.QUALITY_MONITOR:
            console.print("\nActions:")
            console.print("  1. Run scheduled evaluation")
            console.print("  2. Compare with baseline")
            console.print("  3. Detect regressions")
            console.print("  4. Generate alerts if needed")
            if not dry_run:
                console.print("\n[yellow]Full implementation pending.[/yellow]")
                console.print("See docs/AGENT_STRATEGY.md for implementation plan.")

        elif atype == AgentType.DOMAIN_EXPERT:
            if not domain:
                console.print("\n[red]--domain is required for domain-expert agent[/red]")
                raise typer.Exit(1)
            console.print("\nActions:")
            console.print(f"  1. Analyze evaluation results for {domain}")
            console.print("  2. Update terms dictionary")
            console.print("  3. Adjust reliability scores")
            console.print("  4. Run domain evolution")
            if not dry_run:
                console.print("\n[yellow]Full implementation pending.[/yellow]")

        elif atype == AgentType.TESTSET_CURATOR:
            console.print("\nActions:")
            console.print("  1. Analyze coverage gaps")
            console.print("  2. Generate targeted test cases")
            console.print("  3. Check distribution balance")
            if not dry_run:
                console.print("\n[yellow]Full implementation pending.[/yellow]")

        else:
            if not dry_run:
                console.print(f"\n[yellow]{config.name} implementation pending.[/yellow]")
                console.print("See docs/AGENT_STRATEGY.md for details.")

    app.add_typer(agent_app)
