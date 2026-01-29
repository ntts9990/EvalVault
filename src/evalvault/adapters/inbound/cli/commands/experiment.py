"""Experiment management commands for the EvalVault CLI."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import Settings
from evalvault.domain.services.experiment_manager import ExperimentManager

from ..utils.options import db_option
from ..utils.validators import parse_csv_option, validate_choice


def register_experiment_commands(app: typer.Typer, console: Console) -> None:
    """Attach experiment-related commands to the root Typer app."""

    @app.command()
    def experiment_create(
        name: str = typer.Option(..., "--name", "-n", help="Experiment name."),
        description: str = typer.Option("", "--description", "-d", help="Experiment description."),
        hypothesis: str = typer.Option("", "--hypothesis", "-h", help="Experiment hypothesis."),
        metrics: str | None = typer.Option(
            None,
            "--metrics",
            "-m",
            help="Comma-separated list of metrics to compare.",
        ),
        control_retriever: str | None = typer.Option(
            None,
            "--control-retriever",
            help="Control retriever (bm25, dense, hybrid, graphrag).",
        ),
        variant_retriever: str | None = typer.Option(
            None,
            "--variant-retriever",
            help="Variant retriever (bm25, dense, hybrid, graphrag).",
        ),
        db_path: Path = db_option(help_text="Path to database file."),
    ) -> None:
        """Create a new experiment for A/B testing."""

        for retriever_name in (control_retriever, variant_retriever):
            if retriever_name:
                validate_choice(retriever_name, ["bm25", "dense", "hybrid", "graphrag"], console)

        console.print("\n[bold]Creating Experiment[/bold]\n")
        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        manager = ExperimentManager(storage)
        metric_list = parse_csv_option(metrics)
        metric_list = metric_list or None
        experiment = manager.create_experiment(
            name=name,
            description=description,
            hypothesis=hypothesis,
            metrics=metric_list,
        )
        if control_retriever:
            manager.add_group_to_experiment(
                experiment.experiment_id,
                "control",
                f"retriever={control_retriever}",
            )
        if variant_retriever:
            manager.add_group_to_experiment(
                experiment.experiment_id,
                "variant",
                f"retriever={variant_retriever}",
            )
        console.print(f"[green]Created experiment:[/green] {experiment.experiment_id}")
        console.print(f"  Name: {experiment.name}")
        console.print(f"  Status: {experiment.status}")
        if experiment.hypothesis:
            console.print(f"  Hypothesis: {experiment.hypothesis}")
        if experiment.metrics_to_compare:
            console.print(f"  Metrics: {', '.join(experiment.metrics_to_compare)}")
        console.print()

    @app.command()
    def experiment_add_group(
        experiment_id: str = typer.Option(..., "--id", help="Experiment ID."),
        group_name: str = typer.Option(..., "--group", "-g", help="Group name (control, variant)."),
        description: str = typer.Option("", "--description", "-d", help="Group description."),
        db_path: Path = db_option(help_text="Path to database file."),
    ) -> None:
        """Add a group to an experiment."""

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        manager = ExperimentManager(storage)
        try:
            manager.add_group_to_experiment(experiment_id, group_name, description)
            console.print(
                f"[green]Added group '{group_name}' to experiment {experiment_id}[/green]\n"
            )
        except KeyError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1) from exc

    @app.command()
    def experiment_add_run(
        experiment_id: str = typer.Option(..., "--id", help="Experiment ID."),
        group_name: str = typer.Option(..., "--group", "-g", help="Group name."),
        run_id: str = typer.Option(..., "--run", "-r", help="Run ID to add to the group."),
        db_path: Path = db_option(help_text="Path to database file."),
    ) -> None:
        """Add an evaluation run to an experiment group."""

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        manager = ExperimentManager(storage)
        try:
            manager.add_run_to_experiment_group(experiment_id, group_name, run_id)
            console.print(
                f"[green]Added run {run_id} to group '{group_name}' in experiment {experiment_id}[/green]\n"
            )
        except (KeyError, ValueError) as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1) from exc

    @app.command()
    def experiment_list(
        status: str | None = typer.Option(
            None,
            "--status",
            "-s",
            help="Filter by status (draft, running, completed, archived).",
        ),
        db_path: Path = db_option(help_text="Path to database file."),
    ) -> None:
        """List experiments."""

        console.print("\n[bold]Experiments[/bold]\n")
        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        manager = ExperimentManager(storage)
        experiments = manager.list_experiments(status=status)
        if not experiments:
            console.print("[yellow]No experiments found.[/yellow]\n")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Experiment ID", style="dim")
        table.add_column("Name")
        table.add_column("Status")
        table.add_column("Groups", justify="right")
        table.add_column("Created At")

        for exp in experiments:
            status_color = {
                "draft": "yellow",
                "running": "blue",
                "completed": "green",
                "archived": "dim",
            }.get(exp.status, "white")
            table.add_row(
                exp.experiment_id[:12] + "...",
                exp.name,
                f"[{status_color}]{exp.status}[/{status_color}]",
                str(len(exp.groups)),
                exp.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)
        console.print(f"\n[dim]Showing {len(experiments)} experiments[/dim]\n")

    @app.command()
    def experiment_compare(
        experiment_id: str = typer.Option(..., "--id", help="Experiment ID."),
        db_path: Path = db_option(help_text="Path to database file."),
    ) -> None:
        """Compare groups inside an experiment."""

        console.print("\n[bold]Experiment Comparison[/bold]\n")
        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        manager = ExperimentManager(storage)
        try:
            experiment = manager.get_experiment(experiment_id)
            comparisons = manager.compare_groups(experiment_id)
        except KeyError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1) from exc

        if not comparisons:
            console.print("[yellow]No comparison data available.[/yellow]")
            console.print("Make sure groups have evaluation runs added.\n")
            return

        console.print(f"[bold]{experiment.name}[/bold]")
        if experiment.hypothesis:
            console.print(f"Hypothesis: [dim]{experiment.hypothesis}[/dim]")
        console.print()

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="bold")
        for group in experiment.groups:
            table.add_column(group.name, justify="right")
        table.add_column("Best Group", justify="center")
        table.add_column("Improvement", justify="right")

        for comp in comparisons:
            row = [comp.metric_name]
            for group in experiment.groups:
                score = comp.group_scores.get(group.name)
                if score is not None:
                    color = "green" if group.name == comp.best_group else "white"
                    row.append(f"[{color}]{score:.3f}[/{color}]")
                else:
                    row.append("-")
            row.append(f"[green]{comp.best_group}[/green]")
            row.append(f"[cyan]{comp.improvement:+.1f}%[/cyan]")
            table.add_row(*row)

        console.print(table)
        console.print()

    @app.command()
    def experiment_conclude(
        experiment_id: str = typer.Option(..., "--id", help="Experiment ID."),
        conclusion: str = typer.Option(..., "--conclusion", "-c", help="Experiment conclusion."),
        db_path: Path = db_option(help_text="Path to database file."),
    ) -> None:
        """Conclude an experiment and record findings."""

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        manager = ExperimentManager(storage)
        try:
            manager.conclude_experiment(experiment_id, conclusion)
            console.print(f"[green]Experiment {experiment_id} concluded.[/green]")
            console.print(f"Conclusion: {conclusion}\n")
        except KeyError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1) from exc

    @app.command()
    def experiment_summary(
        experiment_id: str = typer.Option(..., "--id", help="Experiment ID."),
        db_path: Path = db_option(help_text="Path to database file."),
    ) -> None:
        """Show experiment summary."""

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        manager = ExperimentManager(storage)
        try:
            summary = manager.get_summary(experiment_id)
        except KeyError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1) from exc

        console.print(f"\n[bold]{summary['name']}[/bold]")
        console.print(f"ID: [dim]{summary['experiment_id']}[/dim]")
        console.print(f"Status: [{summary['status']}]{summary['status']}[/{summary['status']}]")
        console.print(f"Created: {summary['created_at']}")

        if summary["description"]:
            console.print(f"\n[bold]Description:[/bold]\n{summary['description']}")

        if summary["hypothesis"]:
            console.print(f"\n[bold]Hypothesis:[/bold]\n{summary['hypothesis']}")

        if summary["metrics_to_compare"]:
            console.print("\n[bold]Metrics to Compare:[/bold]")
            console.print(f"  {', '.join(summary['metrics_to_compare'])}")

        console.print("\n[bold]Groups:[/bold]")
        for group_name, group_data in summary["groups"].items():
            console.print(f"\n  [cyan]{group_name}[/cyan]")
            if group_data["description"]:
                console.print(f"    Description: {group_data['description']}")
            console.print(f"    Runs: {group_data['num_runs']}")
            if group_data["run_ids"]:
                for run_id in group_data["run_ids"]:
                    console.print(f"      - {run_id}")

        if summary["conclusion"]:
            console.print(f"\n[bold]Conclusion:[/bold]\n{summary['conclusion']}")
        console.print()


__all__ = ["register_experiment_commands"]
