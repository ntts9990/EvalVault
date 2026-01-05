"""Retrieval quality checker module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import build_check, get_upstream_output


class RetrievalQualityCheckerModule(BaseAnalysisModule):
    """Validate retrieval summary heuristics."""

    module_id = "retrieval_quality_checker"
    name = "Retrieval Quality Checker"
    description = "Check retrieval context coverage thresholds."
    input_types = ["retrieval_summary"]
    output_types = ["quality_check"]
    requires = ["retrieval_analyzer"]
    tags = ["verification", "retrieval"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        retrieval_output = (
            get_upstream_output(inputs, "retrieval_analysis", "retrieval_analyzer") or {}
        )
        summary = retrieval_output.get("summary", {})

        if not summary:
            return {
                "passed": False,
                "checks": [build_check("data_presence", False, "No retrieval stats")],
            }

        min_avg_contexts = float(params.get("min_avg_contexts", 1.0))
        max_empty_rate = float(params.get("max_empty_context_rate", 0.2))
        min_context_tokens = float(params.get("min_avg_context_tokens", 4.0))
        min_keyword_overlap = float(params.get("min_keyword_overlap", 0.3))
        min_ground_truth_hit = float(params.get("min_ground_truth_hit_rate", 0.2))

        avg_contexts = summary.get("avg_contexts", 0)
        empty_rate = summary.get("empty_context_rate", 0)
        avg_context_tokens = summary.get("avg_context_tokens", 0)
        keyword_overlap = summary.get("avg_keyword_overlap", 0)
        ground_truth_hit = summary.get("ground_truth_hit_rate", 0)

        checks = [
            build_check(
                "avg_contexts",
                avg_contexts >= min_avg_contexts,
                f"avg={avg_contexts}, min={min_avg_contexts}",
            ),
            build_check(
                "empty_context_rate",
                empty_rate <= max_empty_rate,
                f"rate={empty_rate}, max={max_empty_rate}",
            ),
            build_check(
                "avg_context_tokens",
                avg_context_tokens >= min_context_tokens,
                f"avg={avg_context_tokens}, min={min_context_tokens}",
            ),
            build_check(
                "keyword_overlap",
                keyword_overlap >= min_keyword_overlap,
                f"overlap={keyword_overlap}, min={min_keyword_overlap}",
            ),
            build_check(
                "ground_truth_hit_rate",
                ground_truth_hit >= min_ground_truth_hit,
                f"hit={ground_truth_hit}, min={min_ground_truth_hit}",
            ),
        ]

        passed = all(check["status"] == "pass" for check in checks)
        return {
            "passed": passed,
            "checks": checks,
            "summary": summary,
        }
