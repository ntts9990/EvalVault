"""Statistical comparator module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output


class StatisticalComparatorModule(BaseAnalysisModule):
    """Compare models or runs using aggregated scores."""

    module_id = "statistical_comparator"
    name = "Statistical Comparator"
    description = "Compare aggregated run/model scores and choose a winner."
    input_types = ["model_summary", "run_summary"]
    output_types = ["comparison"]
    requires = ["model_analyzer", "run_analyzer"]
    tags = ["comparison", "statistics"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        model_output = get_upstream_output(inputs, "model_analysis", "model_analyzer") or {}
        run_output = get_upstream_output(inputs, "run_analysis", "run_analyzer") or {}

        candidates: dict[str, Any] = {}
        scope = "model"
        if model_output.get("models"):
            candidates = model_output.get("models", {})
        elif run_output.get("runs"):
            candidates = run_output.get("runs", {})
            scope = "run"

        if not candidates:
            return {"winner": "N/A"}

        scores = {
            name: details.get("overall_score")
            or details.get("avg_pass_rate")
            or details.get("pass_rate")
            or 0.0
            for name, details in candidates.items()
        }

        winner = max(scores, key=scores.get)

        comparison: dict[str, Any] = {"winner": winner, "scope": scope}
        for name, score in scores.items():
            comparison[name] = {"score": round(score, 4)}

        return comparison
