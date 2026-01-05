"""Morpheme quality checker module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import build_check, get_upstream_output


class MorphemeQualityCheckerModule(BaseAnalysisModule):
    """Quality checks for morpheme analysis output."""

    module_id = "morpheme_quality_checker"
    name = "Morpheme Quality Checker"
    description = "Validate morpheme statistics against heuristic thresholds."
    input_types = ["morpheme_stats"]
    output_types = ["quality_check"]
    requires = ["morpheme_analyzer"]
    tags = ["verification", "morpheme"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        morpheme_output = (
            get_upstream_output(inputs, "morpheme_analysis", "morpheme_analyzer") or {}
        )
        summary = morpheme_output.get("summary", {})

        if not summary:
            return {
                "passed": False,
                "checks": [build_check("data_presence", False, "No morpheme stats")],
            }

        min_avg_tokens = params.get("min_avg_tokens", 4)
        min_vocab_size = params.get("min_vocab_size", 30)

        avg_tokens = summary.get("avg_tokens", 0)
        vocab_size = summary.get("vocab_size", 0)
        backend = summary.get("backend", "unknown")

        checks = [
            build_check(
                "avg_tokens",
                avg_tokens >= min_avg_tokens,
                f"avg={avg_tokens}, min={min_avg_tokens}",
            ),
            build_check(
                "vocab_size",
                vocab_size >= min_vocab_size,
                f"vocab={vocab_size}, min={min_vocab_size}",
            ),
            build_check(
                "tokenizer_backend",
                backend == "kiwi",
                f"backend={backend}",
            ),
        ]

        passed = all(check["status"] == "pass" for check in checks)
        return {
            "passed": passed,
            "checks": checks,
            "summary": summary,
        }
