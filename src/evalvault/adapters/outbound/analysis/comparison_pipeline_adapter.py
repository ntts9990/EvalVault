from __future__ import annotations

import asyncio

from evalvault.domain.entities.analysis_pipeline import AnalysisIntent, PipelineResult
from evalvault.domain.services.pipeline_orchestrator import AnalysisPipelineService
from evalvault.ports.outbound.comparison_pipeline_port import ComparisonPipelinePort


class ComparisonPipelineAdapter(ComparisonPipelinePort):
    def __init__(self, service: AnalysisPipelineService) -> None:
        self._service = service

    def run_comparison(
        self,
        *,
        run_ids: list[str],
        compare_metrics: list[str] | None,
        test_type: str,
        parallel: bool,
        concurrency: int | None,
        report_type: str,
        use_llm_report: bool,
    ) -> PipelineResult:
        params = {
            "run_ids": run_ids,
            "compare_metrics": compare_metrics,
            "test_type": test_type,
            "report_type": report_type,
            "use_llm_report": use_llm_report,
        }
        if parallel:
            if concurrency is not None:
                params["max_concurrency"] = concurrency
            return asyncio.run(
                self._service.analyze_intent_async(
                    AnalysisIntent.GENERATE_COMPARISON,
                    run_id=run_ids[0] if run_ids else None,
                    **params,
                )
            )
        return self._service.analyze_intent(
            AnalysisIntent.GENERATE_COMPARISON,
            run_id=run_ids[0] if run_ids else None,
            **params,
        )


__all__ = ["ComparisonPipelineAdapter"]
