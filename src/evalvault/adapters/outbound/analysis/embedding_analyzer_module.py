"""Embedding analyzer module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import (
    average_scores,
    get_upstream_output,
    safe_mean,
)


class EmbeddingAnalyzerModule(BaseAnalysisModule):
    """Compute lightweight embedding quality summaries."""

    module_id = "embedding_analyzer"
    name = "Embedding Analyzer"
    description = "Summarize embedding-related quality signals from metrics."
    input_types = ["metrics"]
    output_types = ["embedding_summary", "statistics"]
    requires = ["data_loader"]
    tags = ["verification", "embedding"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        metrics = loader_output.get("metrics", {}) or {}

        if not metrics:
            return {
                "summary": {},
                "statistics": {},
                "insights": ["No metrics available for embedding analysis."],
            }

        avg_scores = average_scores(metrics)
        overall = safe_mean(avg_scores.values())
        sample_count = max((len(values) for values in metrics.values()), default=0)

        summary = {
            "metric_count": len(avg_scores),
            "sample_count": sample_count,
            "overall_score": round(overall, 4),
        }

        insights = []
        if overall < 0.6:
            insights.append("Embedding quality appears low based on metric averages.")
        elif overall > 0.8:
            insights.append("Embedding metrics look strong overall.")

        return {
            "summary": summary,
            "statistics": {
                "metric_averages": avg_scores,
            },
            "insights": insights,
        }
