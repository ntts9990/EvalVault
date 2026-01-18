from __future__ import annotations

import json
import logging
from pathlib import Path

import typer
from rich.console import Console

from evalvault.adapters.inbound.cli.utils.console import print_cli_error
from evalvault.adapters.inbound.cli.utils.validators import validate_choice
from evalvault.adapters.outbound.artifact_fs import LocalArtifactFileSystemAdapter
from evalvault.domain.services.artifact_lint_service import ArtifactLintService

logger = logging.getLogger(__name__)


def create_artifacts_app(console: Console) -> typer.Typer:
    artifacts_app = typer.Typer(name="artifacts", help="Artifact utilities.")

    @artifacts_app.command("lint")
    def lint(
        artifacts_dir: Path = typer.Argument(..., help="Artifacts directory."),
        strict: bool = typer.Option(False, "--strict", help="Fail on missing files."),
        output_format: str = typer.Option(
            "json",
            "--format",
            "-f",
            help="Output format (json).",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file path for lint result.",
        ),
        parallel: bool = typer.Option(
            True,
            "--parallel/--no-parallel",
            help="Enable parallel validation (placeholder).",
        ),
        concurrency: int = typer.Option(
            8,
            "--concurrency",
            min=1,
            help="Parallel validation concurrency (placeholder).",
        ),
    ) -> None:
        validate_choice(output_format, ["json"], console, value_label="format")

        logger.info("Artifacts lint command started: %s", artifacts_dir)
        fs_adapter = LocalArtifactFileSystemAdapter()
        service = ArtifactLintService(fs_adapter)
        summary = service.lint(artifacts_dir, strict=strict)

        payload = _build_payload(summary, parallel=parallel, concurrency=concurrency)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            console.print(f"[green]Lint report saved:[/green] {output}")
        else:
            console.print(json.dumps(payload, ensure_ascii=False, indent=2))

        if summary.status == "error":
            logger.error("Artifacts lint command failed: %s", artifacts_dir)
            print_cli_error(console, "Artifact lint failed", details=str(artifacts_dir))
            raise typer.Exit(1)

        logger.info("Artifacts lint command finished: %s", artifacts_dir)

    return artifacts_app


def _build_payload(summary, *, parallel: bool, concurrency: int) -> dict[str, object]:
    issues = [
        {
            "level": issue.level,
            "code": issue.code,
            "message": issue.message,
            "path": issue.path,
        }
        for issue in summary.issues
    ]
    error_count = sum(1 for issue in summary.issues if issue.level == "error")
    warning_count = sum(1 for issue in summary.issues if issue.level == "warning")
    return {
        "command": "artifacts.lint",
        "version": 1,
        "status": summary.status,
        "started_at": summary.started_at.isoformat(),
        "finished_at": summary.finished_at.isoformat(),
        "duration_ms": summary.duration_ms,
        "artifacts": {
            "dir": str(summary.artifacts_dir),
            "index": str(summary.index_path),
        },
        "data": {
            "strict": summary.strict,
            "parallel": parallel,
            "concurrency": concurrency,
            "issue_counts": {
                "error": error_count,
                "warning": warning_count,
            },
            "issues": issues,
        },
    }
