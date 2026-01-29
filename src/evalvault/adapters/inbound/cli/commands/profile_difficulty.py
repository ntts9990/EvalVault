from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import typer
from rich.console import Console

from evalvault.adapters.outbound.filesystem.difficulty_profile_writer import DifficultyProfileWriter
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import Settings
from evalvault.domain.services.difficulty_profile_reporter import DifficultyProfileReporter
from evalvault.domain.services.difficulty_profiling_service import (
    DifficultyProfileRequest,
    DifficultyProfilingService,
)

from ..utils.console import print_cli_error, progress_spinner
from ..utils.options import db_option
from ..utils.validators import parse_csv_option, validate_choices

logger = logging.getLogger(__name__)


def register_profile_difficulty_commands(
    app: typer.Typer,
    console: Console,
    available_metrics: Sequence[str],
) -> None:
    @app.command("profile-difficulty")
    def profile_difficulty(
        dataset_name: str | None = typer.Option(
            None, "--dataset-name", help="Dataset name to profile."
        ),
        run_id: str | None = typer.Option(None, "--run-id", help="Run ID to profile."),
        limit_runs: int | None = typer.Option(
            None, "--limit-runs", help="Limit number of runs to analyze."
        ),
        metrics: str | None = typer.Option(
            None, "--metrics", "-m", help="Comma-separated metric allowlist."
        ),
        bucket_count: int = typer.Option(
            3, "--bucket-count", help="Number of difficulty buckets.", min=2
        ),
        min_samples: int = typer.Option(
            10, "--min-samples", help="Minimum samples required for profiling.", min=1
        ),
        output_path: Path | None = typer.Option(None, "--output", "-o", help="Output JSON path."),
        artifacts_dir: Path | None = typer.Option(
            None, "--artifacts-dir", help="Artifacts directory path."
        ),
        parallel: bool = typer.Option(
            False, "--parallel/--no-parallel", help="Enable parallel execution."
        ),
        concurrency: int | None = typer.Option(
            None, "--concurrency", help="Max concurrency when parallel is enabled.", min=1
        ),
        db_path: Path | None = db_option(help_text="DB path."),
    ) -> None:
        if not dataset_name and not run_id:
            print_cli_error(
                console,
                "--dataset-name 또는 --run-id 중 하나는 필수입니다.",
                fixes=["예: --dataset-name insurance-qa", "또는 --run-id run_123"],
            )
            raise typer.Exit(1)
        if dataset_name and run_id:
            print_cli_error(
                console,
                "--dataset-name과 --run-id는 동시에 사용할 수 없습니다.",
                fixes=["둘 중 하나만 지정하세요."],
            )
            raise typer.Exit(1)

        metric_list = parse_csv_option(metrics)
        if metric_list:
            validate_choices(metric_list, available_metrics, console, value_label="metric")
        resolved_metrics = tuple(metric_list) if metric_list else None

        identifier = _safe_identifier(run_id or dataset_name or "difficulty")
        prefix = f"difficulty_{identifier}"
        resolved_output = output_path or Path("reports") / "difficulty" / f"{prefix}.json"
        resolved_artifacts_dir = artifacts_dir or resolved_output.parent / "artifacts" / prefix

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        writer = DifficultyProfileWriter()
        reporter = DifficultyProfileReporter(writer)
        service = DifficultyProfilingService(storage=storage, reporter=reporter)
        request = DifficultyProfileRequest(
            dataset_name=dataset_name,
            run_id=run_id,
            limit_runs=limit_runs,
            metrics=resolved_metrics,
            bucket_count=bucket_count,
            min_samples=min_samples,
            output_path=resolved_output,
            artifacts_dir=resolved_artifacts_dir,
            parallel=parallel,
            concurrency=concurrency,
        )

        with progress_spinner(console, "난이도 프로파일링 실행 중..."):
            started_at = datetime.now(UTC)
            logger.info("profile-difficulty started", extra={"dataset_name": dataset_name})
            try:
                envelope = service.profile(request)
            except KeyError as exc:
                logger.exception("profile-difficulty run missing")
                print_cli_error(
                    console,
                    "Run을 찾지 못했습니다.",
                    details=str(exc),
                    fixes=["--run-id 값과 --db 경로를 확인하세요."],
                )
                raise typer.Exit(1) from exc
            except ValueError as exc:
                logger.exception("profile-difficulty validation failed")
                print_cli_error(
                    console,
                    "난이도 프로파일링 조건을 만족하지 못했습니다.",
                    details=str(exc),
                    fixes=["--min-samples 값을 낮추거나 충분한 실행 이력을 준비하세요."],
                )
                raise typer.Exit(1) from exc
            except Exception as exc:
                logger.exception("profile-difficulty failed")
                print_cli_error(
                    console,
                    "난이도 프로파일링 중 오류가 발생했습니다.",
                    details=str(exc),
                )
                raise typer.Exit(1) from exc

            finished_at = datetime.now(UTC)
            duration_ms = int((finished_at - started_at).total_seconds() * 1000)

        console.print("[green]난이도 프로파일링 완료[/green]")
        console.print(f"- output: {resolved_output}")
        console.print(f"- artifacts: {envelope.get('artifacts', {}).get('dir')}")
        console.print(f"- duration_ms: {duration_ms}")


def _safe_identifier(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")
    return sanitized or "difficulty"


__all__ = ["register_profile_difficulty_commands"]
