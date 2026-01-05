"""Hybrid RRF search module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output


class HybridRRFModule(BaseAnalysisModule):
    """Combine BM25 and embedding scores with a simple RRF-style blend."""

    module_id = "hybrid_rrf"
    name = "Hybrid RRF"
    description = "Blend sparse and dense retrieval scores using a simple average."
    input_types = ["search_score"]
    output_types = ["search_score"]
    requires = ["bm25_searcher", "embedding_searcher"]
    tags = ["search", "hybrid"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        bm25_output = get_upstream_output(inputs, "bm25_search") or {}
        embedding_output = get_upstream_output(inputs, "embedding_search") or {}

        bm25_score = bm25_output.get("score", 0.0)
        embedding_score = embedding_output.get("score", 0.0)

        score = (bm25_score + embedding_score) / 2.0
        score = min(1.0, score + 0.02)

        return {
            "method": "hybrid_rrf",
            "score": round(score, 4),
            "details": {
                "bm25_score": bm25_score,
                "embedding_score": embedding_score,
            },
        }
