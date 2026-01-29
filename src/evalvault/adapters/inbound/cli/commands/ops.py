from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import typer
from rich.console import Console

from evalvault.adapters.outbound.filesystem.ops_snapshot_writer import OpsSnapshotWriter
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.services.ops_snapshot_service import (
    OpsSnapshotRequest,
    OpsSnapshotService,
)

from ..utils.console import print_cli_error, progress_spinner
from ..utils.options import db_option, profile_option


def _resolve_storage_path(db_path: Path | None) -> Path:
    if db_path is None:
        return Path(Settings().evalvault_db_path)
    return db_path


def create_ops_app(console: Console) -> typer.Typer:
    app = typer.Typer(name="ops", help="Ops utilities.")

    @app.command("snapshot")
    def snapshot(
        run_id: str = typer.Option(..., "--run-id", help="Run ID to snapshot."),
        profile: str | None = profile_option(help_text="Profile name to snapshot."),
        db_path: Path | None = db_option(help_text="Path to SQLite database file."),
        include_model_config: bool = typer.Option(
            False,
            "--include-model-config",
            help="Include model profile configuration.",
        ),
        include_env: bool = typer.Option(
            False,
            "--include-env",
            help="Include resolved settings snapshot.",
        ),
        redact: list[str] = typer.Option(
            [],
            "--redact",
            help="Environment keys to redact (repeatable).",
        ),
        output_path: Path = typer.Option(
            ..., "--output", "-o", help="Output JSON path for snapshot."
        ),
    ) -> None:
        settings = Settings()
        resolved_profile = profile or settings.evalvault_profile
        if resolved_profile:
            settings = apply_profile(settings, resolved_profile)

        resolved_db_path = _resolve_storage_path(db_path)
        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        writer = OpsSnapshotWriter()
        service = OpsSnapshotService(
            storage=storage,
            writer=writer,
            settings=settings,
            output_path=output_path,
        )
        request = OpsSnapshotRequest(
            run_id=run_id,
            profile=resolved_profile,
            db_path=resolved_db_path,
            include_model_config=include_model_config,
            include_env=include_env,
            redact_keys=tuple(redact),
        )

        with progress_spinner(console, "Ops snapshot 생성 중..."):
            started_at = datetime.now(UTC)
            try:
                envelope = service.collect(request)
            except KeyError as exc:
                print_cli_error(
                    console,
                    "Run을 찾지 못했습니다.",
                    details=str(exc),
                    fixes=["--run-id 값과 --db 경로를 확인하세요."],
                )
                raise typer.Exit(1) from exc
            except Exception as exc:
                print_cli_error(
                    console,
                    "Ops snapshot 생성 중 오류가 발생했습니다.",
                    details=str(exc),
                    fixes=["--output 경로와 파일 권한을 확인하세요."],
                )
                raise typer.Exit(1) from exc

            finished_at = datetime.now(UTC)
            duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        console.print("[green]Ops snapshot 완료[/green]")
        console.print(f"- output: {output_path}")
        console.print(f"- duration_ms: {duration_ms}")
        console.print(f"- status: {envelope.status}")
        if envelope.data.get("model_config") is None and include_model_config:
            console.print("[yellow]model_config을 찾지 못했습니다.[/yellow]")

    return app


__all__ = ["create_ops_app"]
