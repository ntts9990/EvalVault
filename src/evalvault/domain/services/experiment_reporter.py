"""Generate experiment reports that combine statistics and comparisons.

D-S3b rewiring
--------------
The legacy :class:`ExperimentReportGenerator` returning a ``dict`` remains
the canonical path used by CLI/Web adapters. This module additionally
exposes :class:`ExperimentReportBuilder` and :class:`ExperimentRenderer`
conforming to the ``ReportBuilder`` / ``Renderer`` Protocols.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from evalvault.domain.entities.experiment import Experiment
from evalvault.domain.services.experiment_comparator import ExperimentComparator
from evalvault.domain.services.experiment_statistics import ExperimentStatisticsCalculator
from evalvault.domain.services.reporting import (
    MetricTable,
    ReportData,
    ReportSection,
)


class ExperimentReportGenerator:
    """Produces structured experiment reports for CLI/Web adapters."""

    def __init__(
        self,
        comparator: ExperimentComparator,
        statistics_calculator: ExperimentStatisticsCalculator,
    ):
        self._comparator = comparator
        self._statistics = statistics_calculator

    def generate(self, experiment: Experiment) -> dict:
        """Build a report that joins summary stats with metric comparisons."""
        summary = self._statistics.build_summary(experiment)
        comparisons = self._comparator.compare(experiment)

        return {
            "generated_at": datetime.now().isoformat(),
            "experiment": summary,
            "comparisons": [
                {
                    "metric_name": comp.metric_name,
                    "best_group": comp.best_group,
                    "improvement": comp.improvement,
                    "group_scores": comp.group_scores,
                }
                for comp in comparisons
            ],
        }


# ---------------------------------------------------------------------------
# D-S3b: Builder / Renderer adapters
# ---------------------------------------------------------------------------


def _experiment_payload_to_report_data(
    experiment: Experiment, payload: dict[str, Any]
) -> ReportData:
    """Project an ExperimentReportGenerator payload onto :class:`ReportData`."""

    summary = dict(payload.get("experiment") or {})
    comparisons = list(payload.get("comparisons") or [])

    comparison_table = MetricTable(
        name="comparisons",
        columns=("metric_name", "best_group", "improvement"),
        rows=tuple(
            (
                str(comp.get("metric_name", "")),
                str(comp.get("best_group", "")),
                comp.get("improvement"),
            )
            for comp in comparisons
        ),
    )

    sections: list[ReportSection] = [
        ReportSection(
            title="Experiment Summary",
            body=", ".join(f"{k}={v}" for k, v in summary.items()),
            section_type="summary",
            metadata=summary,
        )
    ]

    metadata = {
        "experiment_id": getattr(experiment, "id", None),
        "experiment_name": getattr(experiment, "name", None),
        "raw_summary": summary,
    }

    generated_at = payload.get("generated_at")
    generated_dt: datetime | None = None
    if isinstance(generated_at, str):
        try:
            generated_dt = datetime.fromisoformat(generated_at)
        except ValueError:
            generated_dt = None

    if generated_dt is None:
        return ReportData(
            report_id=str(getattr(experiment, "id", "")) or "",
            title=f"Experiment Report: {getattr(experiment, 'name', '')}",
            sections=tuple(sections),
            tables=(comparison_table,),
            metadata=metadata,
        )
    return ReportData(
        report_id=str(getattr(experiment, "id", "")) or "",
        title=f"Experiment Report: {getattr(experiment, 'name', '')}",
        sections=tuple(sections),
        tables=(comparison_table,),
        metadata=metadata,
        generated_at=generated_dt,
    )


class ExperimentReportBuilder:
    """:class:`ReportBuilder` adapter over :class:`ExperimentReportGenerator`."""

    def __init__(self, generator: ExperimentReportGenerator) -> None:
        self._generator = generator

    def build(self, *args: Any, **kwargs: Any) -> ReportData:
        experiment = kwargs.pop("experiment", None)
        if experiment is None:
            if not args:
                raise ValueError("ExperimentReportBuilder.build requires experiment")
            experiment = args[0]
        payload = self._generator.generate(experiment)
        return _experiment_payload_to_report_data(experiment, payload)


class ExperimentRenderer:
    """:class:`Renderer` Protocol adapter for experiment reports."""

    def render(self, data: ReportData) -> str:
        lines: list[str] = [f"# {data.title}", ""]
        for section in data.sections:
            lines.extend([f"## {section.title}", section.body, ""])
        comparison_table = next((t for t in data.tables if t.name == "comparisons"), None)
        if comparison_table and comparison_table.rows:
            lines.append("## Comparisons")
            for metric_name, best_group, improvement in comparison_table.rows:
                lines.append(f"- {metric_name}: best={best_group} improvement={improvement}")
        return "\n".join(lines).strip()


__all__ = [
    "ExperimentRenderer",
    "ExperimentReportBuilder",
    "ExperimentReportGenerator",
]
