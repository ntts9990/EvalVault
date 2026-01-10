"""Memory-aware evaluation helpers that leverage Domain Memory."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import nullcontext

from evalvault.domain.entities import Dataset, EvaluationRun
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.ports.outbound.domain_memory_port import MemoryInsightPort
from evalvault.ports.outbound.korean_nlp_port import RetrieverPort
from evalvault.ports.outbound.llm_port import LLMPort
from evalvault.ports.outbound.tracer_port import TracerPort


class MemoryAwareEvaluator:
    """Wraps :class:`RagasEvaluator` to apply Domain Memory signals."""

    def __init__(
        self,
        evaluator: RagasEvaluator,
        memory_port: MemoryInsightPort,
        tracer: TracerPort | None = None,
    ):
        self._evaluator = evaluator
        self._memory_port = memory_port
        self._tracer = tracer

    async def evaluate_with_memory(
        self,
        *,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,
        domain: str,
        language: str = "ko",
        thresholds: Mapping[str, float] | None = None,
        parallel: bool = False,
        batch_size: int = 5,
        retriever: RetrieverPort | None = None,
        retriever_top_k: int = 5,
        retriever_doc_ids: Sequence[str] | None = None,
        on_progress: Callable[[int, int, str], None] | None = None,
        prompt_overrides: dict[str, str] | None = None,
        claim_level: bool = False,
    ) -> EvaluationRun:
        """Run evaluation after adjusting thresholds with memory reliability."""

        reliability = self._memory_port.get_aggregated_reliability(domain=domain, language=language)
        base_thresholds = dict(dataset.thresholds)
        if thresholds:
            base_thresholds.update(thresholds)
        adjusted_thresholds = self._adjust_by_reliability(
            metrics=metrics,
            base_thresholds=base_thresholds,
            reliability=reliability,
        )

        return await self._evaluator.evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=llm,
            thresholds=adjusted_thresholds,
            parallel=parallel,
            batch_size=batch_size,
            retriever=retriever,
            retriever_top_k=retriever_top_k,
            retriever_doc_ids=retriever_doc_ids,
            on_progress=on_progress,
            prompt_overrides=prompt_overrides,
            claim_level=claim_level,
        )

    def augment_context_with_facts(
        self,
        *,
        question: str,
        original_context: str,
        domain: str,
        language: str = "ko",
        limit: int = 5,
    ) -> str:
        """Augment an existing context block with retrieved factual memories."""

        span_context = (
            self._tracer.span(
                "domain_memory.augment_context",
                {
                    "domain_memory.domain": domain,
                    "domain_memory.language": language,
                    "domain_memory.limit": limit,
                },
            )
            if self._tracer
            else nullcontext(None)
        )
        with span_context as span:
            facts = self._memory_port.search_facts(
                query=question,
                domain=domain,
                language=language,
                limit=limit,
            )
            if self._tracer and span:
                self._tracer.set_span_attributes(
                    span,
                    {
                        "question.length": len(question or ""),
                        "domain_memory.fact_count": len(facts),
                    },
                )
        if not facts:
            return original_context

        fact_rows = [f"- {fact.subject} {fact.predicate} {fact.object}" for fact in facts]
        header = "[관련 사실]\n" + "\n".join(fact_rows)
        return header if not original_context else f"{original_context}\n\n{header}"

    def _adjust_by_reliability(
        self,
        *,
        metrics: list[str],
        base_thresholds: dict[str, float],
        reliability: Mapping[str, float],
    ) -> dict[str, float]:
        """Lower or raise thresholds depending on reliability scores."""

        resolved = dict(base_thresholds)
        for metric in metrics:
            resolved.setdefault(metric, self._evaluator.default_threshold_for(metric))

        adjusted: dict[str, float] = {}
        for metric, base_value in resolved.items():
            score = reliability.get(metric)
            new_value = base_value
            if score is not None:
                if score < 0.6:
                    new_value = max(0.5, base_value - 0.1)
                elif score > 0.85:
                    new_value = min(0.95, base_value + 0.05)
            adjusted[metric] = new_value
        return adjusted

    @property
    def memory_port(self) -> MemoryInsightPort:
        """Expose the underlying MemoryInsightPort for advanced orchestration."""

        return self._memory_port

    @property
    def evaluator(self) -> RagasEvaluator:
        """Expose the wrapped evaluator."""

        return self._evaluator
