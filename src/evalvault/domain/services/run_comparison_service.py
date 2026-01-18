from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from evalvault.domain.entities.analysis import ComparisonResult
from evalvault.domain.entities.analysis_pipeline import AnalysisIntent, PipelineResult
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


__all__ = [
    "RunComparisonService",
    "RunComparisonRequest",
    "RunComparisonOutcome",
    "RunComparisonError",
]
