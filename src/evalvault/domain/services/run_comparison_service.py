"""Run-comparison service.

D-S3b rewiring
--------------
The legacy :class:`RunComparisonService` returning :class:`RunComparisonOutcome`
remains the canonical CLI/Web path. This module additionally exposes
:class:`RunComparisonBuilder` and :class:`RunComparisonRenderer` conforming
to the ``ReportBuilder`` / ``Renderer`` Protocols. The Renderer returns the
report text already produced by the analysis pipeline, so CLI output is
byte-identical.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from evalvault.domain.entities.analysis import ComparisonResult
from evalvault.domain.entities.analysis_pipeline import AnalysisIntent, PipelineResult
from evalvault.domain.services.reporting import (
    MetricTable,
    ReportData,
    ReportSection,
)
from evalvault.ports.outbound.analysis_port import AnalysisPort
from evalvault.ports.outbound.comparison_pipeline_port import ComparisonPipelinePort
from evalvault.ports.outbound.storage_port import StoragePort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunComparisonRequest:
    run_id_a: str
    run_id_b: str
    metrics: list[str] | None = None
    test_type: str = "t-test"
    parallel: bool = False
    concurrency: int | None = None
    report_type: str = "comparison"
    use_llm_report: bool = True


@dataclass
class RunComparisonOutcome:
    run_ids: tuple[str, str]
    comparisons: list[ComparisonResult]
    pipeline_result: PipelineResult
    report_text: str
    status: str
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    degraded_reasons: list[str] = field(default_factory=list)

    @property
    def is_degraded(self) -> bool:
        return self.status != "ok"


class RunComparisonError(Exception):
    def __init__(self, message: str, *, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class RunComparisonService:
    def __init__(
        self,
        *,
        storage: StoragePort,
        analysis_port: AnalysisPort,
        pipeline_port: ComparisonPipelinePort,
    ) -> None:
        self._storage = storage
        self._analysis = analysis_port
        self._pipeline = pipeline_port

    def compare_runs(self, request: RunComparisonRequest) -> RunComparisonOutcome:
        started_at = datetime.now(UTC)
        logger.info("Starting run comparison: %s vs %s", request.run_id_a, request.run_id_b)

        try:
            run_a = self._storage.get_run(request.run_id_a)
            run_b = self._storage.get_run(request.run_id_b)
        except KeyError as exc:
            logger.error("Run not found during comparison: %s", exc)
            raise RunComparisonError("Run을 찾을 수 없습니다.", exit_code=1) from exc

        comparisons = self._analysis.compare_runs(
            run_a,
            run_b,
            metrics=request.metrics,
            test_type=request.test_type,
        )
        if not comparisons:
            logger.warning("No common metrics to compare for %s vs %s", run_a.run_id, run_b.run_id)
            raise RunComparisonError("공통 메트릭이 없습니다.", exit_code=1)

        pipeline_error: Exception | None = None
        try:
            pipeline_result = self._pipeline.run_comparison(
                run_ids=[run_a.run_id, run_b.run_id],
                compare_metrics=request.metrics,
                test_type=request.test_type,
                parallel=request.parallel,
                concurrency=request.concurrency,
                report_type=request.report_type,
                use_llm_report=request.use_llm_report,
            )
        except Exception as exc:
            pipeline_error = exc
            logger.exception("Comparison pipeline failed: %s", exc)
            pipeline_result = PipelineResult(
                pipeline_id=f"compare-{run_a.run_id[:8]}-{run_b.run_id[:8]}",
                intent=AnalysisIntent.GENERATE_COMPARISON,
            )
            pipeline_result.mark_complete()

        report_text, report_found = self._extract_markdown_report(pipeline_result)
        degraded_reasons: list[str] = []
        if pipeline_error is not None:
            degraded_reasons.append("pipeline_error")
        if not report_found:
            degraded_reasons.append("report_missing")
        if not pipeline_result.all_succeeded:
            degraded_reasons.append("pipeline_failed")

        status = "degraded" if degraded_reasons else "ok"
        if status == "degraded":
            logger.warning("Comparison report degraded: %s", degraded_reasons)
        finished_at = datetime.now(UTC)
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)

        logger.info("Completed run comparison: status=%s duration_ms=%s", status, duration_ms)

        return RunComparisonOutcome(
            run_ids=(run_a.run_id, run_b.run_id),
            comparisons=comparisons,
            pipeline_result=pipeline_result,
            report_text=report_text,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            degraded_reasons=degraded_reasons,
        )

    @staticmethod
    def _extract_markdown_report(pipeline_result: PipelineResult) -> tuple[str, bool]:
        final_output = pipeline_result.final_output
        if isinstance(final_output, dict):
            report = RunComparisonService._find_report(final_output)
            if report:
                return report, True
        return "# 비교 분석 보고서\n\n보고서 본문을 찾지 못했습니다.\n", False

    @staticmethod
    def _find_report(output: dict) -> str | None:
        if "report" in output and isinstance(output["report"], str):
            return output["report"]
        for value in output.values():
            if isinstance(value, dict):
                nested = RunComparisonService._find_report(value)
                if nested:
                    return nested
        return None


# ---------------------------------------------------------------------------
# D-S3b: Builder / Renderer adapters
# ---------------------------------------------------------------------------


def _run_comparison_outcome_to_report_data(
    outcome: RunComparisonOutcome,
) -> ReportData:
    """Project :class:`RunComparisonOutcome` onto :class:`ReportData`."""

    run_a, run_b = outcome.run_ids

    comparison_rows: list[tuple[Any, ...]] = []
    for comp in outcome.comparisons:
        comparison_rows.append(
            (
                getattr(comp, "metric_name", ""),
                getattr(comp, "mean_a", None),
                getattr(comp, "mean_b", None),
                getattr(comp, "p_value", None),
                getattr(comp, "is_significant", None),
            )
        )
    comparison_table = MetricTable(
        name="metric_comparisons",
        columns=("metric_name", "mean_a", "mean_b", "p_value", "is_significant"),
        rows=tuple(comparison_rows),
    )

    sections: list[ReportSection] = []
    if outcome.degraded_reasons:
        sections.append(
            ReportSection(
                title="Degraded Reasons",
                body=", ".join(outcome.degraded_reasons),
                section_type="warning",
                metadata={"reasons": list(outcome.degraded_reasons)},
            )
        )

    # T2 authority discipline: only "ok"/"degraded" (no T3 promote/rollback).
    status = outcome.status if outcome.status in {"ok", "degraded"} else None

    metadata: dict[str, Any] = {
        "run_id_a": run_a,
        "run_id_b": run_b,
        "duration_ms": outcome.duration_ms,
        "started_at": outcome.started_at.isoformat(),
        "finished_at": outcome.finished_at.isoformat(),
        "pipeline_id": outcome.pipeline_result.pipeline_id,
    }

    return ReportData(
        report_id=f"compare-{run_a}-{run_b}",
        title="비교 분석 보고서",
        sections=tuple(sections),
        tables=(comparison_table,),
        narratives={"report": outcome.report_text},
        status=status,
        metadata=metadata,
        generated_at=outcome.finished_at,
    )


class RunComparisonBuilder:
    """:class:`ReportBuilder` adapter over :class:`RunComparisonService`."""

    def __init__(self, service: RunComparisonService) -> None:
        self._service = service

    def build(self, *args: Any, **kwargs: Any) -> ReportData:
        request = kwargs.pop("request", None)
        if request is None:
            if not args:
                raise ValueError("RunComparisonBuilder.build requires a RunComparisonRequest")
            request = args[0]
        outcome = self._service.compare_runs(request)
        return _run_comparison_outcome_to_report_data(outcome)


class RunComparisonRenderer:
    """:class:`Renderer` Protocol adapter for run comparison reports.

    The pipeline already produced the canonical markdown body; the renderer
    simply returns it verbatim via ``data.narratives['report']`` to preserve
    byte equality with the legacy ``RunComparisonOutcome.report_text``.
    """

    def render(self, data: ReportData) -> str:
        report = data.narratives.get("report")
        if isinstance(report, str):
            return report
        return ""


__all__ = [
    "RunComparisonBuilder",
    "RunComparisonError",
    "RunComparisonOutcome",
    "RunComparisonRenderer",
    "RunComparisonRequest",
    "RunComparisonService",
]
