"""Retrieval analyzer module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output, safe_mean
from evalvault.domain.entities import EvaluationRun


class RetrievalAnalyzerModule(BaseAnalysisModule):
    """Compute basic retrieval quality statistics from run data."""

    module_id = "retrieval_analyzer"
    name = "Retrieval Analyzer"
    description = "Summarize retrieval context coverage and sizes."
    input_types = ["run"]
    output_types = ["retrieval_summary", "statistics"]
    requires = ["data_loader"]
    tags = ["verification", "retrieval"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")
        if not isinstance(run, EvaluationRun):
            return {
                "summary": {},
                "statistics": {},
                "insights": ["No run data available for retrieval analysis."],
            }

        context_counts = [len(result.contexts or []) for result in run.results]
        total_cases = len(context_counts)
        empty_contexts = sum(1 for count in context_counts if count == 0)
        empty_rate = empty_contexts / total_cases if total_cases else 0.0

        context_token_counts = [
            len(context.split())
            for result in run.results
            for context in (result.contexts or [])
            if context
        ]

        summary = {
            "total_cases": total_cases,
            "avg_contexts": round(safe_mean(context_counts), 2),
            "empty_context_rate": round(empty_rate, 4),
            "avg_context_tokens": round(safe_mean(context_token_counts), 2),
        }

        insights = []
        if summary["avg_contexts"] < 1:
            insights.append("Average context count is below 1 per query.")
        if summary["empty_context_rate"] > 0.2:
            insights.append("Many queries are missing retrieval contexts.")

        return {
            "summary": summary,
            "statistics": {
                "context_counts": context_counts[:50],
                "context_token_counts": context_token_counts[:50],
            },
            "insights": insights,
        }
