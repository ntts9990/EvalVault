"""Tests for helper utilities in the run CLI module."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from evalvault.adapters.inbound.cli.commands.run import (
    apply_retriever_to_dataset,
    enrich_dataset_with_memory,
    load_knowledge_graph,
    load_retriever_documents,
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


@dataclass(frozen=True)
class DummyRetrievalResult:
    document: str
    doc_id: int
    score: float


class DummyRetriever:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def search(self, query: str, top_k: int = 5):
        self.calls.append(query)
        return [
            DummyRetrievalResult(document="컨텍스트 A", doc_id=0, score=0.9),
            DummyRetrievalResult(document="컨텍스트 B", doc_id=1, score=0.8),
        ][:top_k]


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


def test_apply_retriever_to_dataset_populates_contexts() -> None:
    dataset = Dataset(
        name="demo",
        version="1.0",
        test_cases=[
            TestCase(id="tc-1", question="질문", answer="답변", contexts=[]),
            TestCase(id="tc-2", question="질문2", answer="답변2", contexts=["기존"]),
        ],
    )

    metadata = apply_retriever_to_dataset(
        dataset=dataset,
        retriever=DummyRetriever(),
        top_k=2,
        doc_ids=["doc-1", "doc-2"],
    )

    assert "tc-1" in metadata
    assert metadata["tc-1"]["doc_ids"] == ["doc-1", "doc-2"]
    assert metadata["tc-1"]["scores"] == [0.9, 0.8]
    assert metadata["tc-1"]["retrieval_time_ms"] > 0
    assert any("컨텍스트" in ctx for ctx in dataset.test_cases[0].contexts)
    assert dataset.test_cases[1].contexts == ["기존"]


def test_load_retriever_documents_supports_json(tmp_path: Path) -> None:
    docs_path = tmp_path / "docs.json"
    docs_path.write_text(
        json.dumps(
            {
                "documents": [
                    {"doc_id": "doc-1", "content": "보험료 정보"},
                    {"doc_id": "doc-2", "content": "보장금액 정보"},
                ]
            }
        ),
        encoding="utf-8",
    )

    documents, doc_ids = load_retriever_documents(docs_path)

    assert documents == ["보험료 정보", "보장금액 정보"]
    assert doc_ids == ["doc-1", "doc-2"]


def test_load_knowledge_graph_supports_wrapped_payload(tmp_path: Path) -> None:
    kg_path = tmp_path / "kg.json"
    kg_path.write_text(
        json.dumps(
            {
                "knowledge_graph": {
                    "entities": [
                        {
                            "name": "AlphaCorp",
                            "entity_type": "organization",
                            "source_document_id": "doc-1",
                            "confidence": 0.9,
                            "provenance": "manual",
                        }
                    ],
                    "relations": [],
                }
            }
        ),
        encoding="utf-8",
    )

    kg = load_knowledge_graph(kg_path)

    assert kg.get_node_count() == 1
