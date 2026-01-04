"""Debug report service."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from evalvault.config.langfuse_support import get_langfuse_trace_url
from evalvault.config.phoenix_support import get_phoenix_trace_url
from evalvault.domain.entities.debug import DebugReport
from evalvault.domain.entities.stage import StageEvent, StageMetric, StageSummary
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
