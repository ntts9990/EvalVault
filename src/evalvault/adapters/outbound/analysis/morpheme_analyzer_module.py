"""Morpheme analyzer module."""

from __future__ import annotations

from collections import Counter
from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import (
    get_upstream_output,
    safe_mean,
)
from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer
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

        params = params or {}
        max_questions = int(params.get("max_questions", 200))
        max_contexts = int(params.get("max_contexts", 300))

        questions = [result.question for result in run.results if result.question][:max_questions]
        contexts: list[str] = []
        for result in run.results:
            for context in result.contexts or []:
                if context:
                    contexts.append(context)
                if len(contexts) >= max_contexts:
                    break
            if len(contexts) >= max_contexts:
                break

        backend = "kiwi"
        errors: list[str] = []
        try:
            tokenizer = KiwiTokenizer()
        except Exception as exc:  # pragma: no cover - optional dependency
            tokenizer = None
            backend = "fallback"
            errors.append(str(exc))

        token_counts: list[int] = []
        pos_counts: Counter[str] = Counter()
        lemma_counts: Counter[str] = Counter()

        def _tokenize(text: str) -> None:
            if tokenizer is None:
                tokens = [part for part in text.split() if part]
                token_counts.append(len(tokens))
                lemma_counts.update(tokens)
                return
            tokens = tokenizer.analyze(text)
            token_counts.append(len(tokens))
            for token in tokens:
                lemma = token.lemma or token.form
                lemma_counts[lemma] += 1
                pos_counts[token.tag] += 1

        for text in questions:
            _tokenize(text)
        for text in contexts:
            _tokenize(text)

        top_keywords = [word for word, _ in lemma_counts.most_common(20)]
        vocab_size = len(lemma_counts)

        summary = {
            "backend": backend,
            "total_questions": len(questions),
            "total_contexts": len(contexts),
            "analyzed_texts": len(token_counts),
            "avg_tokens": round(safe_mean(token_counts), 2),
            "vocab_size": vocab_size,
            "top_keywords": top_keywords,
        }
        if errors:
            summary["errors"] = errors

        insights = []
        if summary["avg_tokens"] < 4:
            insights.append("Average token count is low for morpheme coverage.")
        if vocab_size < 30:
            insights.append("Token diversity looks low.")
        if backend != "kiwi":
            insights.append("Fallback tokenizer used; install kiwipiepy for morpheme detail.")

        return {
            "summary": summary,
            "statistics": {
                "token_counts": token_counts[:100],
                "pos_distribution": dict(pos_counts.most_common(15)),
            },
            "insights": insights,
        }

    def _empty_output(self) -> dict[str, Any]:
        return {
            "summary": {},
            "statistics": {},
            "insights": ["No run data available for morpheme analysis."],
        }
