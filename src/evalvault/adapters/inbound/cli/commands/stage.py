"""Stage event commands for the EvalVault CLI."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.improvement.stage_metric_playbook_loader import (
    StageMetricPlaybookLoader,
)
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import Settings
from evalvault.domain.entities.stage import REQUIRED_STAGE_TYPES, StageEvent, StageMetric
from evalvault.domain.services.stage_metric_guide_service import StageMetricGuideService
from evalvault.domain.services.stage_metric_service import StageMetricService
from evalvault.domain.services.stage_summary_service import StageSummaryService

from ..utils.options import db_option

logger = logging.getLogger(__name__)


@dataclass
class ValidationStats:
    """Tracks StageEvent validation failures by error type."""

    total_processed: int = 0
    valid_count: int = 0
    error_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record_success(self) -> None:
        self.total_processed += 1
        self.valid_count += 1

    def record_failure(self, error_message: str) -> None:
        self.total_processed += 1
        error_type = self._classify_error(error_message)
        self.error_counts[error_type] += 1

    def _classify_error(self, message: str) -> str:
        """Classify error messages into aggregate types."""
        lower_msg = message.lower()
        if "run_id" in lower_msg:
            return "missing_run_id"
        if "stage_type" in lower_msg:
            return "invalid_stage_type"
        if "attributes" in lower_msg:
            return "invalid_attributes"
        if "metadata" in lower_msg:
            return "invalid_metadata"
        if "attempt" in lower_msg:
            return "invalid_attempt"
        if "duration" in lower_msg:
            return "invalid_duration"
        if "datetime" in lower_msg or "started_at" in lower_msg or "finished_at" in lower_msg:
            return "invalid_datetime"
        if "payload" in lower_msg or "ref" in lower_msg:
            return "invalid_payload_ref"
        return "other"

    @property
    def failed_count(self) -> int:
        return self.total_processed - self.valid_count

    @property
    def has_failures(self) -> bool:
        return self.failed_count > 0


def create_stage_app(console: Console) -> typer.Typer:
    """Create the stage Typer sub-application."""

    stage_app = typer.Typer(name="stage", help="Stage-level pipeline observability.")

    @stage_app.command("ingest")
    def ingest(
        file: Path = typer.Argument(..., help="Stage events JSON/JSONL file."),
        db_path: Path | None = db_option(help_text="Path to database file."),
        failed_output: Path | None = typer.Option(
            None,
            "--failed-output",
            help="Write invalid samples to JSONL for inspection.",
        ),
        skip_invalid: bool = typer.Option(
            False,
            "--skip-invalid",
            help="Continue processing after validation failures, logging aggregate counts.",
        ),
    ) -> None:
        """Ingest stage events from JSON or JSONL."""
        events, stats = _load_stage_events_with_stats(
            file,
            skip_invalid=skip_invalid,
            failed_output=failed_output,
        )

        if stats.has_failures:
            _print_validation_stats(console, stats)
            logger.warning(
                "StageEvent validation failures: %d/%d (types: %s)",
                stats.failed_count,
                stats.total_processed,
                dict(stats.error_counts),
            )

        if not events:
            console.print("[yellow]No valid stage events found in the input file.[/yellow]")
            raise typer.Exit(1)

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        stored = storage.save_stage_events(events)

        console.print(f"[green]Stored {stored} stage event(s).[/green]")
        _print_ingest_summary(console, events)

    @stage_app.command("list")
    def list_events(
        run_id: str = typer.Argument(..., help="Run ID to list."),
        stage_type: str | None = typer.Option(
            None,
            "--stage-type",
            "-t",
            help="Filter by stage type.",
        ),
        limit: int = typer.Option(
            200,
            "--limit",
            "-n",
            help="Maximum number of rows to display.",
        ),
        db_path: Path | None = db_option(help_text="Path to database file."),
    ) -> None:
        """List stage events for a run."""
        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        events = storage.list_stage_events(run_id, stage_type=stage_type)

        if not events:
            console.print("[yellow]No stage events found.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Stage ID", style="dim")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("Duration(ms)", justify="right")
        table.add_column("Started At")
        table.add_column("Name")

        for event in events[:limit]:
            started_at = event.started_at.isoformat() if event.started_at else "-"
            duration = f"{event.duration_ms:.1f}" if event.duration_ms is not None else "-"
            table.add_row(
                event.stage_id[:12] + "...",
                event.stage_type,
                event.status,
                duration,
                started_at,
                event.stage_name or "-",
            )

        console.print(table)
        console.print(f"\n[dim]Showing {min(len(events), limit)} of {len(events)}[/dim]\n")

    @stage_app.command("summary")
    def summary(
        run_id: str = typer.Argument(..., help="Run ID to summarize."),
        db_path: Path | None = db_option(help_text="Path to database file."),
    ) -> None:
        """Show summary stats for stage events."""
        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        events = storage.list_stage_events(run_id)
        if not events:
            console.print("[yellow]No stage events found.[/yellow]")
            return

        summary_service = StageSummaryService()
        summary_data = summary_service.summarize(events)
        _print_stage_summary(console, summary_data)

        _print_metric_summary(console, storage.list_stage_metrics(run_id))

    @stage_app.command("compute-metrics")
    def compute_metrics(
        run_id: str = typer.Argument(..., help="Run ID to compute metrics for."),
        relevance_json: Path | None = typer.Option(
            None,
            "--relevance-json",
            help="Optional JSON mapping test_case_id to relevant doc ids.",
        ),
        thresholds_json: Path | None = typer.Option(
            None,
            "--thresholds-json",
            help="Optional JSON mapping metric_name to threshold.",
        ),
        thresholds_profile: str | None = typer.Option(
            None,
            "--thresholds-profile",
            help="Profile key for thresholds JSON (defaults to Settings profile).",
        ),
        db_path: Path | None = db_option(help_text="Path to database file."),
    ) -> None:
        """Compute stage metrics from stored events."""
        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        events = storage.list_stage_events(run_id)
        if not events:
            console.print("[yellow]No stage events found.[/yellow]")
            return

        relevance_map = _load_relevance_map(relevance_json) if relevance_json else None
        thresholds_path = thresholds_json or _default_thresholds_path()
        profile_name = thresholds_profile or _load_default_profile()
        thresholds = (
            _load_thresholds_map(thresholds_path, profile=profile_name) if thresholds_path else None
        )
        metrics = StageMetricService().build_metrics(
            events,
            relevance_map=relevance_map,
            thresholds=thresholds,
        )

        if not metrics:
            console.print("[yellow]No metrics computed from stage events.[/yellow]")
            return

        stored = storage.save_stage_metrics(metrics)
        console.print(f"[green]Stored {stored} stage metric(s).[/green]")
        _print_metric_summary(console, metrics)

    @stage_app.command("report")
    def report(
        run_id: str = typer.Argument(..., help="Run ID to report."),
        relevance_json: Path | None = typer.Option(
            None,
            "--relevance-json",
            help="Optional JSON mapping test_case_id to relevant doc ids.",
        ),
        thresholds_json: Path | None = typer.Option(
            None,
            "--thresholds-json",
            help="Optional JSON mapping metric_name to threshold.",
        ),
        thresholds_profile: str | None = typer.Option(
            None,
            "--thresholds-profile",
            help="Profile key for thresholds JSON (defaults to Settings profile).",
        ),
        playbook: Path | None = typer.Option(
            None,
            "--playbook",
            help="Optional YAML stage metric playbook for actions.",
        ),
        save_metrics: bool = typer.Option(
            True,
            "--save-metrics/--no-save-metrics",
            help="Store computed stage metrics in the database.",
        ),
        db_path: Path | None = db_option(help_text="Path to database file."),
    ) -> None:
        """Report stage summary, metrics, and improvement guides."""
        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        events = storage.list_stage_events(run_id)
        if not events:
            console.print("[yellow]No stage events found.[/yellow]")
            return

        summary_service = StageSummaryService()
        summary_data = summary_service.summarize(events)
        _print_stage_summary(console, summary_data)

        relevance_map = _load_relevance_map(relevance_json) if relevance_json else None
        thresholds_path = thresholds_json or _default_thresholds_path()
        profile_name = thresholds_profile or _load_default_profile()
        thresholds = (
            _load_thresholds_map(thresholds_path, profile=profile_name) if thresholds_path else None
        )
        metrics = StageMetricService().build_metrics(
            events,
            relevance_map=relevance_map,
            thresholds=thresholds,
        )

        if metrics:
            if save_metrics:
                storage.save_stage_metrics(metrics)
            _print_metric_summary(console, metrics)
            action_overrides = StageMetricPlaybookLoader(playbook).load()
            guides = StageMetricGuideService(action_overrides=action_overrides).build_guides(
                metrics
            )
            _print_guide_summary(console, guides)
        else:
            console.print("[yellow]No metrics computed from stage events.[/yellow]")

    return stage_app


def _load_stage_events_with_stats(
    file_path: Path,
    *,
    skip_invalid: bool = False,
    failed_output: Path | None = None,
) -> tuple[list[StageEvent], ValidationStats]:
    suffix = file_path.suffix.lower()
    if suffix == ".jsonl":
        return _load_jsonl_with_stats(
            file_path,
            skip_invalid=skip_invalid,
            failed_output=failed_output,
        )
    if suffix == ".json":
        return _load_json_with_stats(
            file_path,
            skip_invalid=skip_invalid,
            failed_output=failed_output,
        )
    raise typer.BadParameter("Unsupported file format. Use .json or .jsonl")


def _load_jsonl_with_stats(
    file_path: Path,
    *,
    skip_invalid: bool = False,
    failed_output: Path | None = None,
) -> tuple[list[StageEvent], ValidationStats]:
    events: list[StageEvent] = []
    stats = ValidationStats()
    with file_path.open(encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                if failed_output:
                    _record_failed_sample(
                        failed_output,
                        {"raw": raw},
                        error=f"JSON parse error at line {idx}: {exc}",
                        line=idx,
                    )
                if skip_invalid:
                    stats.record_failure(f"JSON parse error at line {idx}")
                    logger.debug("Skipped invalid JSON at line %d: %s", idx, exc)
                    continue
                raise typer.BadParameter(f"Invalid JSON at line {idx}") from exc
            try:
                events.append(StageEvent.from_dict(payload))
                stats.record_success()
            except ValueError as exc:
                if failed_output:
                    _record_failed_sample(
                        failed_output,
                        payload,
                        error=f"Invalid stage event at line {idx}: {exc}",
                        line=idx,
                    )
                if skip_invalid:
                    stats.record_failure(str(exc))
                    logger.debug("Skipped invalid stage event at line %d: %s", idx, exc)
                    continue
                raise typer.BadParameter(f"Invalid stage event at line {idx}: {exc}") from exc
    return events, stats


def _load_json_with_stats(
    file_path: Path,
    *,
    skip_invalid: bool = False,
    failed_output: Path | None = None,
) -> tuple[list[StageEvent], ValidationStats]:
    with file_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict) and "stage_events" in payload:
        raw_events = payload["stage_events"]
    elif isinstance(payload, list):
        raw_events = payload
    elif isinstance(payload, dict):
        raw_events = [payload]
    else:
        raise typer.BadParameter("Unsupported JSON structure for stage events")

    events: list[StageEvent] = []
    stats = ValidationStats()
    for idx, item in enumerate(raw_events, start=1):
        try:
            events.append(StageEvent.from_dict(item))
            stats.record_success()
        except ValueError as exc:
            if failed_output:
                _record_failed_sample(
                    failed_output,
                    item,
                    error=f"Invalid stage event at index {idx}: {exc}",
                    index=idx,
                )
            if skip_invalid:
                stats.record_failure(str(exc))
                logger.debug("Skipped invalid stage event at index %d: %s", idx, exc)
                continue
            raise typer.BadParameter(f"Invalid stage event at index {idx}: {exc}") from exc
    return events, stats


def _record_failed_sample(
    output_path: Path | None,
    payload: object,
    *,
    error: str,
    index: int | None = None,
    line: int | None = None,
) -> None:
    if output_path is None:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "error": error,
        "index": index,
        "line": line,
        "payload": payload,
    }
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _print_validation_stats(console: Console, stats: ValidationStats) -> None:
    console.print(
        f"[yellow]Validation: {stats.valid_count}/{stats.total_processed} valid, "
        f"{stats.failed_count} failed[/yellow]"
    )
    if stats.error_counts:
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Error Type")
        table.add_column("Count", justify="right")
        for error_type, count in sorted(stats.error_counts.items(), key=lambda x: -x[1]):
            table.add_row(error_type, str(count))
        console.print(table)


def _print_ingest_summary(console: Console, events: Iterable[StageEvent]) -> None:
    grouped: dict[str, list[StageEvent]] = defaultdict(list)
    for event in events:
        grouped[event.run_id].append(event)

    summary_service = StageSummaryService()
    for run_id, run_events in grouped.items():
        summary = summary_service.summarize(run_events)
        console.print(f"[bold]Run[/bold] {run_id} | Events: {summary.total_events}")
        if summary.missing_required_stage_types:
            required = ", ".join(REQUIRED_STAGE_TYPES)
            console.print(f"[dim]  Required stages:[/dim] {required}")
            missing = ", ".join(summary.missing_required_stage_types)
            console.print(f"[yellow]  Missing required stages:[/yellow] {missing}")


def _load_relevance_map(file_path: Path) -> dict[str, list[str]]:
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise typer.BadParameter("Invalid relevance JSON file.") from exc

    if not isinstance(payload, dict):
        raise typer.BadParameter("Relevance JSON must be an object mapping test_case_id to list.")

    relevance_map: dict[str, list[str]] = {}
    for key, value in payload.items():
        if isinstance(value, list):
            relevance_map[str(key)] = [str(item) for item in value]
        else:
            relevance_map[str(key)] = [str(value)]

    return relevance_map


def _load_thresholds_map(file_path: Path, *, profile: str | None = None) -> dict[str, float]:
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise typer.BadParameter("Invalid thresholds JSON file.") from exc

    if not isinstance(payload, dict):
        raise typer.BadParameter("Thresholds JSON must be an object mapping metric_name to value.")

    thresholds_payload = _select_threshold_block(payload, profile=profile)

    thresholds: dict[str, float] = {}
    for key, value in thresholds_payload.items():
        if isinstance(value, (int, float, str)):
            thresholds[str(key)] = float(value)
            continue
        raise typer.BadParameter(f"Invalid threshold value for '{key}': {value}")

    return thresholds


def _default_thresholds_path() -> Path | None:
    candidate = Path("config/stage_metric_thresholds.json")
    return candidate if candidate.exists() else None


def _select_threshold_block(
    payload: dict[str, object],
    *,
    profile: str | None,
) -> dict[str, object]:
    default_block = payload.get("default")
    profiles_block = payload.get("profiles")

    if isinstance(default_block, dict) or isinstance(profiles_block, dict):
        merged: dict[str, object] = {}
        if isinstance(default_block, dict):
            merged.update(default_block)
        if profile and isinstance(profiles_block, dict):
            profile_block = profiles_block.get(profile)
            if isinstance(profile_block, dict):
                merged.update(profile_block)
        return merged

    return payload


def _load_default_profile() -> str | None:
    try:
        return Settings().evalvault_profile
    except Exception:
        return None


def _print_stage_summary(console: Console, summary_data) -> None:
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Stage Type")
    table.add_column("Count", justify="right")
    table.add_column("Avg Duration(ms)", justify="right")

    for stage_type, count in sorted(summary_data.stage_type_counts.items()):
        avg_duration = summary_data.stage_type_avg_durations.get(stage_type)
        avg_display = f"{avg_duration:.1f}" if avg_duration is not None else "-"
        table.add_row(stage_type, str(count), avg_display)

    console.print(table)

    if summary_data.missing_required_stage_types:
        required = ", ".join(REQUIRED_STAGE_TYPES)
        console.print(f"[dim]Required stages:[/dim] {required}")
        missing = ", ".join(summary_data.missing_required_stage_types)
        console.print(f"[yellow]Missing required stages:[/yellow] {missing}")


def _print_metric_summary(console: Console, metrics: list[StageMetric]) -> None:
    if not metrics:
        console.print("[dim]No stage metrics stored for this run.[/dim]")
        return

    aggregates = _aggregate_metrics(metrics)
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Count", justify="right")
    table.add_column("Avg", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Pass Rate", justify="right")

    for metric_name, stats in sorted(aggregates.items()):
        pass_rate = str(stats.get("pass_rate", "-"))
        table.add_row(
            metric_name,
            str(stats["count"]),
            f"{stats['avg']:.4f}",
            f"{stats['min']:.4f}",
            f"{stats['max']:.4f}",
            pass_rate,
        )

    console.print(table)


def _aggregate_metrics(metrics: list[StageMetric]) -> dict[str, dict[str, float | str]]:
    grouped: dict[str, list[StageMetric]] = defaultdict(list)
    for metric in metrics:
        grouped[metric.metric_name].append(metric)

    aggregates: dict[str, dict[str, float | str]] = {}
    for name, items in grouped.items():
        scores = [item.score for item in items]
        pass_values = [item.passed for item in items if item.passed is not None]
        pass_rate = (
            f"{(sum(1 for value in pass_values if value) / len(pass_values)):.2%}"
            if pass_values
            else "-"
        )
        aggregates[name] = {
            "count": len(scores),
            "avg": sum(scores) / len(scores),
            "min": min(scores),
            "max": max(scores),
            "pass_rate": pass_rate,
        }
    return aggregates


def _print_guide_summary(console: Console, guides: list) -> None:
    if not guides:
        console.print("[green]No stage metric issues detected.[/green]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Component")
    table.add_column("Priority")
    table.add_column("Top Action")
    table.add_column("Effort")
    table.add_column("Expected Improvement", justify="right")

    for guide in guides:
        top_action = guide.top_action
        action_title = top_action.title if top_action else "-"
        effort = top_action.effort.value if top_action else "-"
        improvement = (
            f"{guide.total_expected_improvement:.2%}" if guide.total_expected_improvement else "-"
        )
        table.add_row(
            guide.component.value, guide.priority.value, action_title, effort, improvement
        )

    console.print(table)
