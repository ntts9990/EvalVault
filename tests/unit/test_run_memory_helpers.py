"""Tests for helper utilities in the run CLI module."""

from __future__ import annotations

from evalvault.adapters.inbound.cli.commands.run import (
    enrich_dataset_with_memory,
    log_phoenix_traces,
)
from evalvault.domain.entities import (
    Dataset,
    EvaluationRun,
    MetricScore,
    TestCase,
    TestCaseResult,
)


class DummyMemoryEvaluator:
    def augment_context_with_facts(self, **_: str) -> str:
        return "[관련 사실]\n- 보험 약관을 검토하세요."


class DummyTracker:
    def __init__(self) -> None:
        self.calls: list = []

    def log_rag_trace(self, data) -> None:
        self.calls.append(data)


def test_enrich_dataset_with_memory_appends_contexts():
    dataset = Dataset(
        name="demo",
        version="1.0",
        test_cases=[
            TestCase(id="tc-1", question="질문", answer="답변", contexts=[]),
            TestCase(id="tc-2", question="질문2", answer="답변2", contexts=["기존"]),
        ],
    )
    added = enrich_dataset_with_memory(
        dataset=dataset,
        memory_evaluator=DummyMemoryEvaluator(),
        domain="insurance",
        language="ko",
    )
    assert added == 2
    assert any("보험" in ctx for ctx in dataset.test_cases[0].contexts)


def test_log_phoenix_traces_uses_tracker_interface():
    tracker = DummyTracker()
    run = EvaluationRun(
        model_name="demo-model",
        results=[
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[MetricScore(name="faithfulness", score=0.8, threshold=0.7)],
                tokens_used=42,
                latency_ms=1200,
                question="보험료는?",
                answer="보험료는 ...",
                contexts=["컨텍스트"],
            )
        ],
        metrics_evaluated=["faithfulness"],
    )
    count = log_phoenix_traces(tracker, run, max_traces=5)
    assert count == 1
    assert tracker.calls
    recorded = tracker.calls[0]
    assert recorded.retrieval is not None
    assert recorded.generation.response.startswith("보험료")
