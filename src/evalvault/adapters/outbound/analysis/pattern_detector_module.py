"""Pattern detector module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output


class PatternDetectorModule(BaseAnalysisModule):
    """Detect simple patterns from NLP analysis output."""

    module_id = "pattern_detector"
    name = "Pattern Detector"
    description = "Summarize notable keyword and question-type patterns."
    input_types = ["nlp_analysis"]
    output_types = ["pattern_detection"]
    requires = ["nlp_analyzer"]
    tags = ["analysis", "pattern"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        nlp_output = get_upstream_output(inputs, "nlp_analysis", "nlp_analyzer") or {}
        keywords = nlp_output.get("top_keywords", [])
        question_types = nlp_output.get("question_types", [])

        patterns = []
        for item in keywords[:5]:
            keyword = item.get("keyword")
            if keyword:
                patterns.append(
                    {
                        "label": "Top keyword",
                        "detail": f"{keyword} (freq {item.get('frequency', 0)})",
                    }
                )

        for item in question_types[:3]:
            qtype = item.get("question_type")
            if qtype:
                patterns.append(
                    {
                        "label": "Question type",
                        "detail": f"{qtype} ({item.get('percentage', 0):.1f}%)",
                    }
                )

        return {
            "patterns": patterns,
            "summary": {
                "keyword_count": len(keywords),
                "question_type_count": len(question_types),
            },
        }
