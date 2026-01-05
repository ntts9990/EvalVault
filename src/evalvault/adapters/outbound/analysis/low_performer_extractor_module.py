"""Low performer extractor module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output


class LowPerformerExtractorModule(BaseAnalysisModule):
    """Extract low-performing test cases from RAGAS output."""

    module_id = "low_performer_extractor"
    name = "Low Performer Extractor"
    description = "Extract cases with low aggregate RAGAS scores."
    input_types = ["ragas_summary"]
    output_types = ["low_performers"]
    requires = ["ragas_evaluator"]
    tags = ["analysis", "diagnostic"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        threshold = float(params.get("threshold", 0.5))

        ragas_output = get_upstream_output(inputs, "ragas_eval", "ragas_evaluator") or {}
        per_case = ragas_output.get("per_case", [])

        low_performers = [case for case in per_case if case.get("avg_score", 1.0) < threshold]

        return {
            "threshold": threshold,
            "low_performers": low_performers,
            "count": len(low_performers),
        }
