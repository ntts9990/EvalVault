"""Debug report commands for the EvalVault CLI."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown

from evalvault.adapters.outbound.debug.report_renderer import render_json, render_markdown
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import Settings
from evalvault.domain.services.debug_report_service import DebugReportService

from ..utils.options import db_option
from ..utils.validators import validate_choice


def create_debug_app(console: Console) -> typer.Typer:
    """Create the Typer sub-application for debug report commands."""

    debug_app = typer.Typer(name="debug", help="Debug report utilities.")

    @debug_app.command("report")
    def report(
        run_id: str = typer.Argument(..., help="Run ID to report."),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file path for the debug report.",
        ),
        format: str = typer.Option(
            "markdown",
            "--format",
            "-f",
            help="Output format: markdown or json.",
        ),
        db_path: Path = db_option(help_text="Path to database file."),
    ) -> None:
        """Generate a debug report for a run."""

        validate_choice(format, ["markdown", "json"], console, value_label="format")

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        service = DebugReportService()

        try:
            report_data = service.build_report(
                run_id,
                storage=storage,
                stage_storage=storage,
            )
        except KeyError:
            console.print(f"[red]Error:[/red] Run not found: {run_id}")
            raise typer.Exit(1)

        payload = render_json(report_data) if format == "json" else render_markdown(report_data)

        if output:
            output.write_text(payload, encoding="utf-8")
            console.print(f"[green]Saved debug report to {output}[/green]")
            return

        if format == "markdown":
            console.print(Markdown(payload))
        else:
            console.print(payload)

    return debug_app
