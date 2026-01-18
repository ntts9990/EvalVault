from __future__ import annotations

from typing import Protocol

from evalvault.domain.entities.analysis_pipeline import PipelineResult


class ComparisonPipelinePort(Protocol):
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
    ) -> PipelineResult: ...


__all__ = ["ComparisonPipelinePort"]
