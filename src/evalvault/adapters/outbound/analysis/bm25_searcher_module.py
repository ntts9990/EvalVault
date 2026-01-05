"""BM25 searcher module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output


class BM25SearcherModule(BaseAnalysisModule):
    """Heuristic BM25 scoring based on token statistics."""

    module_id = "bm25_searcher"
    name = "BM25 Searcher"
    description = "Estimate BM25-style retrieval quality from token stats."
    input_types = ["morpheme_stats"]
    output_types = ["search_score"]
    requires = ["morpheme_analyzer"]
    tags = ["search", "bm25"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        morpheme_output = (
            get_upstream_output(inputs, "morpheme_analysis", "morpheme_analyzer") or {}
        )
        summary = morpheme_output.get("summary", {})

        avg_tokens = summary.get("avg_question_tokens", 0)
        vocab_size = summary.get("vocab_size", 0)

        score = min(1.0, (avg_tokens / 10.0) + (min(vocab_size, 100) / 200.0))

        return {
            "method": "bm25",
            "score": round(score, 4),
            "details": {
                "avg_question_tokens": avg_tokens,
                "vocab_size": vocab_size,
            },
        }
