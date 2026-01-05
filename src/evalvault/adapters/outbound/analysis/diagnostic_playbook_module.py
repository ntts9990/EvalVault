"""Diagnostic playbook module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output


class DiagnosticPlaybookModule(BaseAnalysisModule):
    """Generate diagnostics and recommendations from RAGAS summaries."""

    module_id = "diagnostic_playbook"
    name = "Diagnostic Playbook"
    description = "Generate issue hypotheses and remediation hints."
    input_types = ["ragas_summary"]
    output_types = ["diagnostics"]
    requires = ["ragas_evaluator"]
    tags = ["analysis", "diagnostic"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        threshold = float(params.get("metric_threshold", 0.6))

        ragas_output = get_upstream_output(inputs, "ragas_eval", "ragas_evaluator") or {}
        metrics = ragas_output.get("metrics", {}) or {}

        diagnostics = []
        recommendations = []
        for metric, score in metrics.items():
            if score >= threshold:
                continue
            issue = f"{metric} is below threshold ({score:.2f} < {threshold:.2f})."
            recommendation = f"Review data and prompts related to {metric}."
            diagnostics.append({"metric": metric, "issue": issue, "score": score})
            recommendations.append(recommendation)

        return {
            "threshold": threshold,
            "diagnostics": diagnostics,
            "recommendations": recommendations,
        }
