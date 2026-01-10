"""Tests for memory-aware evaluation and analysis helpers."""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from evalvault.domain.entities import (
    Dataset,
    EvaluationRun,
    MetricScore,
    TestCase,
    TestCaseResult,
)
from evalvault.domain.entities.memory import BehaviorEntry, FactualFact, LearningMemory
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.domain.services.memory_aware_evaluator import MemoryAwareEvaluator
from evalvault.domain.services.memory_based_analysis import MemoryBasedAnalysis
from evalvault.ports.outbound.korean_nlp_port import RetrieverPort
from evalvault.ports.outbound.llm_port import LLMPort


class DummyLLM(LLMPort):
    def get_model_name(self) -> str:  # pragma: no cover - simple stub
        return "dummy-llm"

    def as_ragas_llm(self):
        return object()


class DummyEvaluator(RagasEvaluator):
    """Override evaluate() to avoid running the full pipeline."""

    def __init__(self):
        self.captured_thresholds: dict[str, float] = {}

    async def evaluate(  # type: ignore[override]
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,
        thresholds: dict[str, float] | None = None,
        parallel: bool = False,
        batch_size: int = 5,
        retriever: RetrieverPort | None = None,
        retriever_top_k: int = 5,
        retriever_doc_ids: Sequence[str] | None = None,
        on_progress: object = None,
        prompt_overrides: dict[str, str] | None = None,
        claim_level: bool = False,
    ) -> EvaluationRun:
        self.captured_thresholds = dict(thresholds or {})
        run = EvaluationRun(dataset_name=dataset.name, dataset_version=dataset.version)
        run.metrics_evaluated = metrics
        run.thresholds = self.captured_thresholds
        return run


class FakeMemoryPort:
    """Minimal MemoryInsightPort stub."""

    def __init__(self):
        self.reliability = {"faithfulness": 0.55, "answer_relevancy": 0.9}
        self.facts = [
            FactualFact(
                subject="청약",
                predicate="가능 기간",
                object="15일",
                domain="insurance",
                language="ko",
            )
        ]
        self.behaviors = [
            BehaviorEntry(
                description="약관 검토",
                trigger_pattern="보험",
                action_sequence=["약관 확인", "중요 조항 요약"],
                success_rate=0.92,
                domain="insurance",
            )
        ]
        self.learnings = [
            LearningMemory(
                domain="insurance",
                language="ko",
                successful_patterns=["컨텍스트 확장"],
                failed_patterns=["근거 부족"],
                faithfulness_by_entity_type={"faithfulness": 0.68},
            )
        ]

    # -- Methods consumed by the services ---------------------------------
    def get_aggregated_reliability(self, domain: str, language: str) -> dict[str, float]:
        return self.reliability

    def search_facts(self, query: str, domain: str, language: str, limit: int = 5):
        return self.facts[:limit]

    def search_behaviors(self, context: str, domain: str, language: str, limit: int = 5):
        return self.behaviors[:limit]

    def list_learnings(self, domain: str, language: str, limit: int = 5):
        return self.learnings[:limit]

    def hybrid_search(self, query: str, domain: str, language: str, limit: int = 5):
        return {
            "facts": self.facts[:limit],
            "behaviors": self.behaviors[:limit],
            "learnings": self.learnings[:limit],
        }


@pytest.mark.asyncio
async def test_memory_aware_evaluator_adjusts_thresholds():
    dataset = Dataset(name="demo", version="1.0", test_cases=[], thresholds={"faithfulness": 0.8})
    evaluator = DummyEvaluator()
    memory_port = FakeMemoryPort()
    service = MemoryAwareEvaluator(evaluator=evaluator, memory_port=memory_port)

    await service.evaluate_with_memory(
        dataset=dataset,
        metrics=["faithfulness", "answer_relevancy"],
        llm=DummyLLM(),
        domain="insurance",
        thresholds={"answer_relevancy": 0.75},
    )

    assert evaluator.captured_thresholds["faithfulness"] == pytest.approx(0.7)
    assert evaluator.captured_thresholds["answer_relevancy"] == pytest.approx(0.8)


def test_memory_aware_evaluator_augment_context():
    service = MemoryAwareEvaluator(evaluator=DummyEvaluator(), memory_port=FakeMemoryPort())
    enriched = service.augment_context_with_facts(
        question="청약 철회 기한?",
        original_context="원문",
        domain="insurance",
    )
    assert "[관련 사실]" in enriched
    assert "청약" in enriched


def test_memory_aware_evaluator_augment_context_without_original():
    service = MemoryAwareEvaluator(evaluator=DummyEvaluator(), memory_port=FakeMemoryPort())
    enriched = service.augment_context_with_facts(
        question="청약 철회 기한?",
        original_context="",
        domain="insurance",
    )
    assert enriched.startswith("[관련 사실]")
    assert "청약" in enriched


def test_memory_based_analysis_generates_insights():
    analyzer = MemoryBasedAnalysis(memory_port=FakeMemoryPort())
    run = EvaluationRun(
        results=[
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[MetricScore(name="faithfulness", score=0.62, threshold=0.7)],
            )
        ],
        metrics_evaluated=["faithfulness"],
    )

    insights = analyzer.generate_insights(
        evaluation_run=run,
        domain="insurance",
        language="ko",
    )

    assert "faithfulness" in insights["trends"]
    assert insights["related_facts"]
    assert insights["recommendations"]


def test_memory_based_analysis_applies_behaviors():
    analyzer = MemoryBasedAnalysis(memory_port=FakeMemoryPort())
    test_case = TestCase(
        id="tc-1",
        question="보험금 산정 방법?",
        answer="",
        contexts=[],
    )

    actions = analyzer.apply_successful_behaviors(
        test_case=test_case,
        domain="insurance",
        language="ko",
        min_success_rate=0.8,
    )

    assert actions
