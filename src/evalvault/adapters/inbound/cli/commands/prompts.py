"""Prompt snapshot commands for the EvalVault CLI."""

from __future__ import annotations

import difflib
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.domain.entities import PromptSetBundle

from ..utils.options import db_option


def _bundle_to_role_map(bundle: PromptSetBundle) -> dict[str, dict[str, str]]:
    prompt_map = {prompt.prompt_id: prompt for prompt in bundle.prompts}
    roles: dict[str, dict[str, str]] = {}
    for item in bundle.items:
        prompt = prompt_map.get(item.prompt_id)
        if not prompt:
            continue
        roles[item.role] = {
            "checksum": prompt.checksum,
            "content": prompt.content,
            "name": prompt.name,
            "kind": prompt.kind,
        }
    return roles


def create_prompts_app(console: Console) -> typer.Typer:
    """Create the `prompts` sub-application."""

    app = typer.Typer(help="Prompt snapshots and diffs.")

    @app.command("show")
    def show_prompt_set(
        run_id: str = typer.Argument(..., help="Run ID to inspect."),
        db_path: Path = db_option(help_text="Path to database file."),
    ) -> None:
        """Show prompt snapshots attached to a run."""
        storage = SQLiteStorageAdapter(db_path=db_path)
        bundle = storage.get_prompt_set_for_run(run_id)
        if not bundle:
            console.print("[yellow]No prompt set found for this run.[/yellow]")
            raise typer.Exit(0)

        console.print(f"\n[bold]Prompt Set[/bold] {bundle.prompt_set.name}\n")
        prompt_map = {prompt.prompt_id: prompt for prompt in bundle.prompts}
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Role")
        table.add_column("Kind")
        table.add_column("Name")
        table.add_column("Checksum", style="dim")
        for item in bundle.items:
            prompt = prompt_map.get(item.prompt_id)
            if not prompt:
                continue
            table.add_row(
                item.role,
                prompt.kind,
                prompt.name,
                prompt.checksum[:12],
            )
        console.print(table)
        console.print()

    @app.command("diff")
    def diff_prompt_sets(
        run_id_a: str = typer.Argument(..., help="Base run ID."),
        run_id_b: str = typer.Argument(..., help="Target run ID."),
        db_path: Path = db_option(help_text="Path to database file."),
        max_lines: int = typer.Option(
            40,
            "--max-lines",
            help="Maximum diff lines per prompt.",
        ),
        show_diff: bool = typer.Option(
            True,
            "--show-diff/--no-show-diff",
            help="Print unified diffs for changed prompts.",
        ),
    ) -> None:
        """Compare prompt snapshots between two runs."""
        storage = SQLiteStorageAdapter(db_path=db_path)
        bundle_a = storage.get_prompt_set_for_run(run_id_a)
        bundle_b = storage.get_prompt_set_for_run(run_id_b)

        if not bundle_a or not bundle_b:
            console.print("[yellow]Prompt set not found for one or both runs.[/yellow]")
            raise typer.Exit(0)

        roles_a = _bundle_to_role_map(bundle_a)
        roles_b = _bundle_to_role_map(bundle_b)
        all_roles = sorted(set(roles_a) | set(roles_b))

        console.print("\n[bold]Prompt Diff Summary[/bold]\n")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Role")
        table.add_column("Run A", justify="left")
        table.add_column("Run B", justify="left")
        table.add_column("Status", justify="center")

        for role in all_roles:
            a = roles_a.get(role)
            b = roles_b.get(role)
            if not a:
                table.add_row(role, "-", b["checksum"][:12], "[yellow]missing[/yellow]")
                continue
            if not b:
                table.add_row(role, a["checksum"][:12], "-", "[yellow]missing[/yellow]")
                continue
            status = "same" if a["checksum"] == b["checksum"] else "diff"
            status_color = "green" if status == "same" else "red"
            table.add_row(
                role,
                a["checksum"][:12],
                b["checksum"][:12],
                f"[{status_color}]{status}[/{status_color}]",
            )

        console.print(table)

        if not show_diff:
            console.print()
            return

        for role in all_roles:
            a = roles_a.get(role)
            b = roles_b.get(role)
            if not a or not b or a["checksum"] == b["checksum"]:
                continue
            diff_lines = list(
                difflib.unified_diff(
                    a["content"].splitlines(),
                    b["content"].splitlines(),
                    fromfile=f"{run_id_a[:8]}:{role}",
                    tofile=f"{run_id_b[:8]}:{role}",
                    lineterm="",
                )
            )
            if not diff_lines:
                continue
            console.print(f"\n[bold]{role}[/bold]")
            for line in diff_lines[:max_lines]:
                console.print(line, markup=False)
            if len(diff_lines) > max_lines:
                console.print("[dim]... diff truncated ...[/dim]")
        console.print()

    return app


__all__ = ["create_prompts_app"]
