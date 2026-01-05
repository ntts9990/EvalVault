"""Weighted hybrid search module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output


class HybridWeightedModule(BaseAnalysisModule):
    """Combine BM25 and embedding scores with weighted averaging."""

    module_id = "hybrid_weighted"
    name = "Hybrid Weighted"
    description = "Blend sparse and dense retrieval scores using weighted average."
    input_types = ["search_score"]
    output_types = ["search_score"]
    requires = ["bm25_searcher", "embedding_searcher"]
    tags = ["search", "hybrid"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        bm25_weight = params.get("bm25_weight", 0.4)
        embedding_weight = params.get("embedding_weight", 0.6)

        bm25_output = get_upstream_output(inputs, "bm25_search") or {}
        embedding_output = get_upstream_output(inputs, "embedding_search") or {}

        bm25_score = bm25_output.get("score", 0.0)
        embedding_score = embedding_output.get("score", 0.0)

        total_weight = bm25_weight + embedding_weight
        if total_weight == 0:
            score = 0.0
        else:
            score = (bm25_score * bm25_weight + embedding_score * embedding_weight) / total_weight

        return {
            "method": "hybrid_weighted",
            "score": round(min(1.0, score), 4),
            "details": {
                "bm25_score": bm25_score,
                "embedding_score": embedding_score,
                "weights": {
                    "bm25": bm25_weight,
                    "embedding": embedding_weight,
                },
            },
        }
