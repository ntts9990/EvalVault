from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from evalvault.domain.entities.stage import StageMetric, StageSummary


@dataclass
class OpsReport:
    run_summary: dict[str, Any]
    ops_kpis: dict[str, Any]
    stage_summary: StageSummary | None
    stage_metrics: list[StageMetric]
    bottlenecks: list[dict[str, Any]]
    recommendations: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_summary": self.run_summary,
            "ops_kpis": self.ops_kpis,
            "stage_summary": _stage_summary_to_dict(self.stage_summary),
            "stage_metrics": [metric.to_dict() for metric in self.stage_metrics],
            "bottlenecks": self.bottlenecks,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
        }


def _stage_summary_to_dict(summary: StageSummary | None) -> dict[str, Any] | None:
    if summary is None:
        return None
    return {
        "run_id": summary.run_id,
        "total_events": summary.total_events,
        "stage_type_counts": summary.stage_type_counts,
        "stage_type_avg_durations": summary.stage_type_avg_durations,
        "missing_required_stage_types": summary.missing_required_stage_types,
    }
