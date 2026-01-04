"""API server command for EvalVault CLI."""

from __future__ import annotations

import typer
import uvicorn
from rich.console import Console

from evalvault.adapters.inbound.api.main import create_app


def register_api_command(app: typer.Typer, console: Console) -> None:
    """Attach the `serve-api` command to the root Typer app."""

    @app.command("serve-api")
    def serve_api(
        host: str = typer.Option(
            "127.0.0.1",
            "--host",
            "-h",
            help="Host to bind the server to.",
        ),
        port: int = typer.Option(
            8000,
            "--port",
            "-p",
            help="Port to run the server on.",
        ),
        reload: bool = typer.Option(
            False,
            "--reload",
            help="Enable auto-reload for development.",
        ),
    ) -> None:
        """Start the EvalVault FastAPI Backend Server."""
        console.print(f"[bold green]Starting EvalVault API[/bold green] at http://{host}:{port}")
        console.print("[dim]Press Ctrl+C to stop.[/dim]")

        # We can either run the app object directly or pass the import string.
        # Passing the import string is better for reload=True.
        # However, since create_app is a factory, we might need to handle it.
        # Uvicorn supports factory with "module:factory" syntax + --factory flag if running from CLI,
        # but via python code with `uvicorn.run`, we can pass the app instance directly if reload is False.
        # If reload is True, we must pass the import string.

        if reload:
            uvicorn.run(
                "evalvault.adapters.inbound.api.main:create_app",
                host=host,
                port=port,
                reload=True,
                factory=True,
            )
        else:
            api_app = create_app()
            uvicorn.run(api_app, host=host, port=port)


__all__ = ["register_api_command"]
