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

        min_dimension = int(params.get("min_dimension", 128))
        min_norm_std = float(params.get("min_norm_std", 0.01))
        max_cosine_mean = float(params.get("max_cosine_mean", 0.98))

        dimension = summary.get("dimension", 0) or 0
        norm_std = summary.get("norm_std", 0) or 0
        cosine_mean = summary.get("mean_cosine_to_centroid", 0) or 0
        backend = summary.get("backend", "unknown")

        checks = [
            build_check(
                "dimension",
                dimension >= min_dimension,
                f"dim={dimension}, min={min_dimension}",
            ),
            build_check(
                "norm_std",
                norm_std >= min_norm_std,
                f"std={norm_std}, min={min_norm_std}",
            ),
            build_check(
                "cosine_collapse",
                cosine_mean <= max_cosine_mean,
                f"mean={cosine_mean}, max={max_cosine_mean}",
            ),
            build_check(
                "embedding_backend",
                backend not in {"unavailable", ""},
                f"backend={backend}",
            ),
        ]

        passed = all(check["status"] == "pass" for check in checks)
        return {
            "passed": passed,
            "checks": checks,
            "summary": summary,
        }
