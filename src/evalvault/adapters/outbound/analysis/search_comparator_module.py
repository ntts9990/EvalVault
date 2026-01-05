"""Search comparator module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output


class SearchComparatorModule(BaseAnalysisModule):
    """Compare search strategies and select a winner."""

    module_id = "search_comparator"
    name = "Search Comparator"
    description = "Compare hybrid search variants and pick the best score."
    input_types = ["search_score"]
    output_types = ["comparison"]
    requires = ["hybrid_rrf", "hybrid_weighted"]
    tags = ["comparison", "search"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        rrf_output = get_upstream_output(inputs, "rrf_hybrid", "hybrid_rrf") or {}
        weighted_output = get_upstream_output(inputs, "weighted_hybrid", "hybrid_weighted") or {}

        rrf_available = rrf_output.get("available", True)
        weighted_available = weighted_output.get("available", True)
        rrf_score = rrf_output.get("score", 0.0)
        weighted_score = weighted_output.get("score", 0.0)

        if rrf_available and not weighted_available:
            winner = "rrf_hybrid"
        elif weighted_available and not rrf_available:
            winner = "weighted_hybrid"
        else:
            winner = "rrf_hybrid" if rrf_score >= weighted_score else "weighted_hybrid"

        return {
            "winner": winner,
            "rrf_hybrid": {"score": rrf_score, "available": rrf_available},
            "weighted_hybrid": {"score": weighted_score, "available": weighted_available},
        }
