"""Embedding searcher module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import (
    average_scores,
    get_upstream_output,
    safe_mean,
)


class EmbeddingSearcherModule(BaseAnalysisModule):
    """Heuristic embedding retrieval scorer."""

    module_id = "embedding_searcher"
    name = "Embedding Searcher"
    description = "Estimate dense retrieval quality using metric averages."
    input_types = ["metrics"]
    output_types = ["search_score"]
    requires = ["data_loader"]
    tags = ["search", "embedding"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        metrics = loader_output.get("metrics", {}) or {}

        if metrics:
            avg_scores = average_scores(metrics)
            score = safe_mean(avg_scores.values())
        else:
            avg_scores = {}
            score = 0.5

        return {
            "method": "embedding",
            "score": round(score, 4),
            "details": {
                "metric_averages": avg_scores,
            },
        }
