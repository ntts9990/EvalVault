"""Root cause analyzer module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output


class RootCauseAnalyzerModule(BaseAnalysisModule):
    """Combine diagnostics into root-cause hypotheses."""

    module_id = "root_cause_analyzer"
    name = "Root Cause Analyzer"
    description = "Aggregate diagnostics and causal hints into root causes."
    input_types = ["diagnostics", "low_performers", "causal_analysis"]
    output_types = ["root_cause"]
    requires = ["diagnostic_playbook", "low_performer_extractor"]
    tags = ["analysis", "root_cause"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        low_samples = get_upstream_output(inputs, "low_samples", "low_performers") or {}
        diagnostic = get_upstream_output(inputs, "diagnostic", "diagnostic_playbook") or {}
        causal = get_upstream_output(inputs, "causal", "causal_analyzer") or {}

        low_performers = low_samples.get("low_performers", [])
        diagnostics = diagnostic.get("diagnostics", [])
        recommendations = list(diagnostic.get("recommendations", []))

        causes = []
        for item in diagnostics:
            causes.append(
                {
                    "metric": item.get("metric", "unknown"),
                    "reason": item.get("issue", "Low metric score"),
                }
            )

        if low_performers and not causes:
            causes.append(
                {
                    "metric": "overall",
                    "reason": "Multiple test cases fall below the performance threshold.",
                }
            )

        interventions = causal.get("interventions", [])
        for intervention in interventions:
            if isinstance(intervention, dict):
                text = intervention.get("intervention") or intervention.get("detail")
                if text:
                    recommendations.append(text)
            elif isinstance(intervention, str):
                recommendations.append(intervention)

        root_causes = causal.get("root_causes", [])
        for root_cause in root_causes:
            if isinstance(root_cause, dict):
                reason = root_cause.get("description") or root_cause.get("factor")
                if reason:
                    causes.append({"metric": root_cause.get("metric", "unknown"), "reason": reason})

        recommendations = list(dict.fromkeys(recommendations))

        return {
            "causes": causes,
            "recommendations": recommendations,
            "low_performer_count": len(low_performers),
        }
