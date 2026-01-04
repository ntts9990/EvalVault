"""Debug report entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from evalvault.domain.entities.stage import StageMetric, StageSummary


@dataclass
class DebugReport:
    """Debug report combining run and stage diagnostics."""

    run_summary: dict[str, Any]
    stage_summary: StageSummary | None
    stage_metrics: list[StageMetric]
    bottlenecks: list[dict[str, Any]]
    recommendations: list[str]
    phoenix_trace_url: str | None = None
    langfuse_trace_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        summary_dict = None
        if self.stage_summary is not None:
            summary_dict = {
                "run_id": self.stage_summary.run_id,
                "total_events": self.stage_summary.total_events,
                "stage_type_counts": self.stage_summary.stage_type_counts,
                "stage_type_avg_durations": self.stage_summary.stage_type_avg_durations,
                "missing_required_stage_types": self.stage_summary.missing_required_stage_types,
            }
        return {
            "run_summary": self.run_summary,
            "stage_summary": summary_dict,
            "stage_metrics": [metric.to_dict() for metric in self.stage_metrics],
            "bottlenecks": self.bottlenecks,
            "recommendations": self.recommendations,
            "phoenix_trace_url": self.phoenix_trace_url,
            "langfuse_trace_url": self.langfuse_trace_url,
        }
