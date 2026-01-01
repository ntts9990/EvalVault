"""Streamlit web command for EvalVault CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console

from ..utils.options import db_option


def register_web_command(app: typer.Typer, console: Console) -> None:
    """Attach the `web` command to the root Typer app."""

    @app.command()
    def web(
        port: int = typer.Option(
            8501,
            "--port",
            "-p",
            help="Port to run the web server on.",
        ),
        host: str = typer.Option(
            "localhost",
            "--host",
            "-H",
            help="Host to bind the web server to.",
        ),
        db_path: Path = db_option(
            help_text="Path to SQLite database file.", default=Path("evalvault.db")
        ),
    ) -> None:
        """Launch the EvalVault Web UI (Streamlit dashboard)."""

        console.print("\n[bold]EvalVault Web UI[/bold]\n")
        console.print(f"Starting server at [cyan]http://{host}:{port}[/cyan]")
        console.print(f"Database: [dim]{db_path}[/dim]")
        console.print("\n[dim]Press Ctrl+C to stop the server.[/dim]\n")

        try:
            from evalvault.adapters.inbound.web import app as web_app_module

            app_path = Path(web_app_module.__file__).parent / "app.py"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    str(app_path),
                    "--server.port",
                    str(port),
                    "--server.address",
                    host,
                    "--",
                    "--db",
                    str(db_path),
                ],
                check=True,
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped.[/yellow]")
        except ImportError:
            console.print("[red]Error:[/red] Streamlit not installed.")
            console.print("Install with: [cyan]uv add streamlit[/cyan]")
            raise typer.Exit(1)
        except subprocess.CalledProcessError as exc:
            console.print(f"[red]Error starting web server:[/red] {exc}")
            raise typer.Exit(1) from exc


__all__ = ["register_web_command"]
