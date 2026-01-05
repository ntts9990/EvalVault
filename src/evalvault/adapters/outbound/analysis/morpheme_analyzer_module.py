"""Morpheme analyzer module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output, safe_mean
from evalvault.domain.entities import EvaluationRun


class MorphemeAnalyzerModule(BaseAnalysisModule):
    """Lightweight token-level analysis for morpheme validation."""

    module_id = "morpheme_analyzer"
    name = "Morpheme Analyzer"
    description = "Compute basic token statistics for morpheme validation."
    input_types = ["run"]
    output_types = ["morpheme_stats", "summary"]
    requires = ["data_loader"]
    tags = ["verification", "morpheme"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")
        if not isinstance(run, EvaluationRun):
            return self._empty_output()

        questions = [result.question for result in run.results if result.question]
        contexts = [
            context for result in run.results for context in (result.contexts or []) if context
        ]

        question_token_counts = [len(text.split()) for text in questions]
        context_token_counts = [len(text.split()) for text in contexts]

        tokens = []
        for text in questions + contexts:
            tokens.extend(text.split())

        vocab_size = len({token.lower() for token in tokens})

        summary = {
            "total_questions": len(questions),
            "total_contexts": len(contexts),
            "avg_question_tokens": round(safe_mean(question_token_counts), 2),
            "avg_context_tokens": round(safe_mean(context_token_counts), 2),
            "vocab_size": vocab_size,
        }

        insights = []
        if summary["avg_question_tokens"] < 3:
            insights.append("Questions appear shorter than expected.")
        if summary["avg_context_tokens"] < 5 and contexts:
            insights.append("Context snippets are relatively short.")
        if vocab_size < 20:
            insights.append("Token diversity looks low for morpheme checks.")

        return {
            "summary": summary,
            "statistics": {
                "question_token_counts": question_token_counts[:50],
                "context_token_counts": context_token_counts[:50],
            },
            "insights": insights,
        }

    def _empty_output(self) -> dict[str, Any]:
        return {
            "summary": {},
            "statistics": {},
            "insights": ["No run data available for morpheme analysis."],
        }
