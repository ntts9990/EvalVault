"""Langfuse dashboard command for EvalVault CLI."""

from __future__ import annotations

import base64
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import typer
from rich.console import Console
from rich.table import Table

from evalvault.config.settings import Settings


def register_langfuse_commands(app: typer.Typer, console: Console) -> None:
    """Attach langfuse-dashboard command to the root Typer app."""

    @app.command("langfuse-dashboard")
    def langfuse_dashboard(
        limit: int = typer.Option(5, help="표시할 Langfuse trace 개수"),
        event_type: str = typer.Option("ragas_evaluation", help="필터링할 event_type"),
    ) -> None:
        """Langfuse에서 평가/그래프 trace를 조회해 요약."""

        settings = Settings()
        if not settings.langfuse_public_key or not settings.langfuse_secret_key:
            console.print("[red]Langfuse credentials not configured.[/red]")
            raise typer.Exit(1)

        try:
            traces = _fetch_langfuse_traces(
                host=settings.langfuse_host,
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                event_type=event_type,
                limit=limit,
            )
        except HTTPError as exc:
            console.print(
                f"[yellow]Langfuse public API not available (HTTP {exc.code}). "
                "Skipping dashboard output.[/yellow]"
            )
            return
        except Exception as exc:  # pragma: no cover - network handling
            console.print(f"[red]Failed to fetch Langfuse traces:[/red] {exc}")
            raise typer.Exit(1) from exc

        if not traces:
            console.print("[yellow]No traces found for the given event_type.[/yellow]")
            return

        table = Table(
            title=f"Langfuse Traces ({event_type})", show_header=True, header_style="bold cyan"
        )
        table.add_column("Trace ID")
        table.add_column("Dataset")
        table.add_column("Model")
        table.add_column("Pass Rate", justify="right")
        table.add_column("Total Cases", justify="right")
        table.add_column("Created At")

        for trace in traces:
            metadata = trace.get("metadata", {})
            dataset_name = metadata.get("dataset_name") or metadata.get("source", "N/A")
            model_name = metadata.get("model_name", "N/A")
            pass_rate = metadata.get("pass_rate")
            total_cases = metadata.get("total_test_cases") or metadata.get("documents_processed")
            created_at = trace.get("createdAt") or trace.get("created_at", "")
            table.add_row(
                trace.get("id", "unknown"),
                str(dataset_name),
                str(model_name),
                f"{pass_rate:.2f}" if isinstance(pass_rate, int | float) else "N/A",
                str(total_cases) if total_cases is not None else "N/A",
                created_at,
            )

        console.print(table)


def _fetch_langfuse_traces(
    host: str,
    public_key: str,
    secret_key: str,
    event_type: str,
    limit: int,
) -> list[dict]:
    """Langfuse Public API를 호출해 trace 리스트를 가져온다."""

    base = host.rstrip("/")
    url = f"{base}/api/public/traces/search"
    payload = {
        "query": {"metadata.event_type": {"equals": event_type}},
        "limit": limit,
        "orderBy": {"createdAt": "desc"},
    }
    auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode("utf-8")
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth}",
        },
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("data", data if isinstance(data, list) else [])


__all__ = ["register_langfuse_commands", "_fetch_langfuse_traces"]
