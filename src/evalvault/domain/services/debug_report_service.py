"""Debug report service.

D-S3b rewiring
--------------
The legacy :class:`DebugReportService` and its :class:`DebugReport` domain
entity stay as the canonical persistence path. This module also exposes a
:class:`DebugReportBuilder` / :class:`DebugRenderer` pair that conform to
the ``ReportBuilder`` / ``Renderer`` Protocols from
:mod:`evalvault.domain.services.reporting`. Markdown rendering for CLI
consumers continues to live in
``evalvault.adapters.outbound.debug.report_renderer`` and remains
byte-identical.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from evalvault.config.langfuse_support import get_langfuse_trace_url
from evalvault.config.phoenix_support import get_phoenix_trace_url
from evalvault.domain.entities.debug import DebugReport
from evalvault.domain.entities.stage import StageEvent, StageMetric, StageSummary
from evalvault.domain.services.reporting import (
    MetricTable,
    ReportData,
    ReportSection,
)
from evalvault.domain.services.stage_metric_guide_service import StageMetricGuideService
from evalvault.domain.services.stage_metric_service import StageMetricService
from evalvault.domain.services.stage_summary_service import StageSummaryService
from evalvault.ports.outbound.stage_storage_port import StageStoragePort
from evalvault.ports.outbound.storage_port import StoragePort


class DebugReportService:
    """Build a debug report for an evaluation run."""

    def __init__(
        self,
        *,
        metric_service: StageMetricService | None = None,
        summary_service: StageSummaryService | None = None,
        guide_service: StageMetricGuideService | None = None,
    ) -> None:
        self._metric_service = metric_service or StageMetricService()
        self._summary_service = summary_service or StageSummaryService()
        self._guide_service = guide_service or StageMetricGuideService()

    def build_report(
        self,
        run_id: str,
        storage: StoragePort,
        stage_storage: StageStoragePort,
    ) -> DebugReport:
        run = storage.get_run(run_id)
        run_summary = run.to_summary_dict()
        phoenix_trace_url = get_phoenix_trace_url(run.tracker_metadata)
        langfuse_trace_url = get_langfuse_trace_url(run.tracker_metadata)

        events = stage_storage.list_stage_events(run_id)
        stage_summary = self._summarize_events(events)

        stage_metrics = stage_storage.list_stage_metrics(run_id)
        if not stage_metrics and events:
            stage_metrics = self._metric_service.build_metrics(events)

        bottlenecks = self._build_bottlenecks(stage_summary)
        recommendations = self._build_recommendations(stage_metrics)

        return DebugReport(
            run_summary=run_summary,
            stage_summary=stage_summary,
            stage_metrics=stage_metrics,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            phoenix_trace_url=phoenix_trace_url,
            langfuse_trace_url=langfuse_trace_url,
        )

    def _summarize_events(self, events: Iterable[StageEvent]) -> StageSummary | None:
        event_list = list(events)
        if not event_list:
            return None
        return self._summary_service.summarize(event_list)

    def _build_bottlenecks(self, summary: StageSummary | None) -> list[dict[str, Any]]:
        if summary is None:
            return []
        bottlenecks: list[dict[str, Any]] = []

        for stage_type in summary.missing_required_stage_types:
            bottlenecks.append(
                {
                    "type": "missing_stage",
                    "stage_type": stage_type,
                    "detail": "required stage missing",
                }
            )

        durations = summary.stage_type_avg_durations
        if durations:
            top = sorted(durations.items(), key=lambda item: item[1], reverse=True)[:3]
            for stage_type, duration in top:
                bottlenecks.append(
                    {
                        "type": "latency",
                        "stage_type": stage_type,
                        "avg_duration_ms": round(duration, 3),
                    }
                )
        return bottlenecks

    def _build_recommendations(self, metrics: list[StageMetric]) -> list[str]:
        if not metrics:
            return []
        guides = self._guide_service.build_guides(metrics)
        recommendations: list[str] = []
        for guide in guides:
            top_action = guide.top_action
            if top_action is None:
                continue
            hint = top_action.implementation_hint or top_action.description
            label = f"[{guide.priority.value}] {guide.component.value}"
            if hint:
                recommendations.append(f"{label}: {top_action.title} - {hint}")
            else:
                recommendations.append(f"{label}: {top_action.title}")
        return recommendations


# ---------------------------------------------------------------------------
# D-S3b: Builder / Renderer adapters
# ---------------------------------------------------------------------------


def _debug_report_to_report_data(report: DebugReport) -> ReportData:
    """Project :class:`DebugReport` onto :class:`ReportData`."""

    run_summary = dict(report.run_summary)
    sections: list[ReportSection] = []

    stage_summary = report.stage_summary
    if stage_summary is not None:
        sections.append(
            ReportSection(
                title="Stage Summary",
                body=(
                    f"total_events={stage_summary.total_events}; "
                    f"missing={list(stage_summary.missing_required_stage_types)}"
                ),
                section_type="summary",
                metadata={
                    "stage_type_counts": dict(stage_summary.stage_type_counts),
                    "stage_type_avg_durations": dict(
                        stage_summary.stage_type_avg_durations
                    ),
                    "missing_required_stage_types": list(
                        stage_summary.missing_required_stage_types
                    ),
                },
            )
        )

    if report.bottlenecks:
        sections.append(
            ReportSection(
                title="Bottlenecks",
                body="; ".join(
                    str(item.get("type", "unknown")) for item in report.bottlenecks
                ),
                section_type="analysis",
                metadata={"items": list(report.bottlenecks)},
            )
        )

    if report.recommendations:
        sections.append(
            ReportSection(
                title="Recommendations",
                body="\n".join(report.recommendations),
                section_type="recommendation",
            )
        )

    failing_metrics = [m for m in report.stage_metrics if m.passed is False]
    metric_table = MetricTable(
        name="failing_stage_metrics",
        columns=("metric_name", "score", "threshold", "stage_id"),
        rows=tuple(
            (m.metric_name, m.score, m.threshold, m.stage_id) for m in failing_metrics
        ),
    )

    metadata: dict[str, Any] = {
        "phoenix_trace_url": report.phoenix_trace_url,
        "langfuse_trace_url": report.langfuse_trace_url,
        "run_summary": run_summary,
    }

    return ReportData(
        report_id=str(run_summary.get("run_id", "")),
        title="Debug Report",
        sections=tuple(sections),
        tables=(metric_table,),
        metadata=metadata,
    )


class DebugReportBuilder:
    """:class:`ReportBuilder` adapter over :class:`DebugReportService`."""

    def __init__(self, service: DebugReportService | None = None) -> None:
        self._service = service or DebugReportService()

    def build(self, *args: Any, **kwargs: Any) -> ReportData:
        run_id = kwargs.pop("run_id", None)
        storage = kwargs.pop("storage", None)
        stage_storage = kwargs.pop("stage_storage", None)
        if run_id is None or storage is None or stage_storage is None:
            if len(args) != 3:
                raise ValueError(
                    "DebugReportBuilder.build requires run_id, storage, stage_storage"
                )
            run_id, storage, stage_storage = args
        report = self._service.build_report(run_id, storage, stage_storage)
        return _debug_report_to_report_data(report)


class DebugRenderer:
    """:class:`Renderer` Protocol adapter for debug reports.

    Produces a domain-level markdown summary from the projected
    :class:`ReportData`. Legacy CLI markdown bytes still flow through
    ``evalvault.adapters.outbound.debug.report_renderer.render_markdown``
    so existing CLI consumers stay byte-identical.
    """

    def render(self, data: ReportData) -> str:
        lines: list[str] = [f"# {data.title}", ""]
        run_summary = dict(data.metadata.get("run_summary") or {})
        if run_summary:
            lines.append("## Run Summary")
            for key in (
                "run_id",
                "dataset_name",
                "model_name",
                "started_at",
                "finished_at",
                "duration_seconds",
                "total_test_cases",
                "pass_rate",
            ):
                lines.append(f"- {key}: {run_summary.get(key, '-')}")
            lines.append("")
        for section in data.sections:
            lines.extend([f"## {section.title}", section.body, ""])
        failing = next(
            (t for t in data.tables if t.name == "failing_stage_metrics"), None
        )
        if failing and failing.rows:
            lines.append("## Failing Stage Metrics")
            for name, score, threshold, stage_id in failing.rows:
                lines.append(
                    f"- {name}: score={score} threshold={threshold} stage_id={stage_id}"
                )
        return "\n".join(lines).strip()


__all__ = [
    "DebugRenderer",
    "DebugReportBuilder",
    "DebugReportService",
]
