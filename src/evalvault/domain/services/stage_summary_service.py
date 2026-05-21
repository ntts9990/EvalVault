"""Stage summary service for pipeline observability.

D-S3b rewiring
--------------
The legacy :class:`StageSummaryService` returning :class:`StageSummary`
remains the canonical persistence path. This module additionally exposes
:class:`StageSummaryBuilder` and :class:`StageSummaryRenderer` conforming
to the ``ReportBuilder`` / ``Renderer`` Protocols.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from evalvault.domain.entities.stage import (
    REQUIRED_STAGE_TYPES,
    StageEvent,
    StageSummary,
)
from evalvault.domain.services.reporting import (
    MetricTable,
    ReportData,
    ReportSection,
)


class StageSummaryService:
    """Compute summary statistics for stage events."""

    def summarize(self, events: Iterable[StageEvent]) -> StageSummary:
        event_list = list(events)
        run_id = event_list[0].run_id if event_list else ""
        stage_counts: dict[str, int] = defaultdict(int)
        duration_totals: dict[str, float] = defaultdict(float)
        duration_counts: dict[str, int] = defaultdict(int)

        for event in event_list:
            stage_counts[event.stage_type] += 1
            if event.duration_ms is not None:
                duration_totals[event.stage_type] += event.duration_ms
                duration_counts[event.stage_type] += 1

        avg_durations = {
            stage_type: duration_totals[stage_type] / duration_counts[stage_type]
            for stage_type in duration_totals
            if duration_counts[stage_type] > 0
        }

        observed_types = set(stage_counts.keys())
        missing_required = [stage for stage in REQUIRED_STAGE_TYPES if stage not in observed_types]

        return StageSummary(
            run_id=run_id,
            total_events=len(event_list),
            stage_type_counts=dict(stage_counts),
            stage_type_avg_durations=avg_durations,
            missing_required_stage_types=missing_required,
        )


# ---------------------------------------------------------------------------
# D-S3b: Builder / Renderer adapters
# ---------------------------------------------------------------------------


def _stage_summary_to_report_data(summary: StageSummary) -> ReportData:
    """Project :class:`StageSummary` onto :class:`ReportData`."""

    counts_table = MetricTable(
        name="stage_type_counts",
        columns=("stage_type", "count"),
        rows=tuple(
            (stage_type, count)
            for stage_type, count in summary.stage_type_counts.items()
        ),
    )
    durations_table = MetricTable(
        name="stage_type_avg_durations_ms",
        columns=("stage_type", "avg_duration_ms"),
        rows=tuple(
            (stage_type, duration)
            for stage_type, duration in summary.stage_type_avg_durations.items()
        ),
    )

    sections: list[ReportSection] = []
    if summary.missing_required_stage_types:
        sections.append(
            ReportSection(
                title="Missing Required Stages",
                body=", ".join(summary.missing_required_stage_types),
                section_type="warning",
                metadata={
                    "missing": list(summary.missing_required_stage_types),
                },
            )
        )

    # T2 authority discipline: only T1/T2 verdicts (ok / degraded).
    status = "ok" if not summary.missing_required_stage_types else "degraded"

    return ReportData(
        report_id=summary.run_id,
        title="Stage Summary",
        sections=tuple(sections),
        tables=(counts_table, durations_table),
        status=status,
        metadata={"total_events": summary.total_events},
    )


class StageSummaryBuilder:
    """:class:`ReportBuilder` adapter over :class:`StageSummaryService`."""

    def __init__(self, service: StageSummaryService | None = None) -> None:
        self._service = service or StageSummaryService()

    def build(self, *args: Any, **kwargs: Any) -> ReportData:
        events = kwargs.pop("events", None)
        if events is None:
            if not args:
                raise ValueError("StageSummaryBuilder.build requires events")
            events = args[0]
        summary = self._service.summarize(events)
        return _stage_summary_to_report_data(summary)


class StageSummaryRenderer:
    """:class:`Renderer` Protocol adapter for stage summaries."""

    def render(self, data: ReportData) -> str:
        lines: list[str] = [f"# {data.title}", ""]
        lines.append(f"- total_events: {data.metadata.get('total_events', '-')}")
        lines.append(f"- status: {data.status or 'unknown'}")
        counts = next((t for t in data.tables if t.name == "stage_type_counts"), None)
        if counts and counts.rows:
            lines.append("## Stage Type Counts")
            for stage_type, count in counts.rows:
                lines.append(f"- {stage_type}: {count}")
        durations = next(
            (t for t in data.tables if t.name == "stage_type_avg_durations_ms"), None
        )
        if durations and durations.rows:
            lines.append("## Stage Type Avg Durations (ms)")
            for stage_type, duration in durations.rows:
                lines.append(f"- {stage_type}: {duration:.3f}")
        for section in data.sections:
            lines.extend([f"## {section.title}", section.body])
        return "\n".join(lines).strip()


__all__ = [
    "StageSummaryBuilder",
    "StageSummaryRenderer",
    "StageSummaryService",
]
