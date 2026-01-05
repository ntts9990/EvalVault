"""Embedding distribution checker module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import build_check, get_upstream_output


class EmbeddingDistributionModule(BaseAnalysisModule):
    """Validate embedding distribution using summary statistics."""

    module_id = "embedding_distribution"
    name = "Embedding Distribution Checker"
    description = "Check embedding distribution heuristics for stability."
    input_types = ["embedding_summary"]
    output_types = ["quality_check"]
    requires = ["embedding_analyzer"]
    tags = ["verification", "embedding"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        embedding_output = (
            get_upstream_output(inputs, "embedding_analysis", "embedding_analyzer") or {}
        )
        summary = embedding_output.get("summary", {})

        if not summary:
            return {
                "passed": False,
                "checks": [build_check("data_presence", False, "No embedding stats")],
            }

        min_score = params.get("min_overall_score", 0.6)
        min_metrics = params.get("min_metric_count", 1)

        overall_score = summary.get("overall_score", 0)
        metric_count = summary.get("metric_count", 0)

        checks = [
            build_check(
                "overall_score",
                overall_score >= min_score,
                f"score={overall_score}, min={min_score}",
            ),
            build_check(
                "metric_count",
                metric_count >= min_metrics,
                f"count={metric_count}, min={min_metrics}",
            ),
        ]

        passed = all(check["status"] == "pass" for check in checks)
        return {
            "passed": passed,
            "checks": checks,
            "summary": summary,
        }
