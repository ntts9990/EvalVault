"""Retriever context helpers tests."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from evalvault.domain.entities.dataset import Dataset, TestCase
from evalvault.domain.services.retriever_context import (
    _compact_values,
    _extract_graph_attributes,
    _normalize_retrieval_results,
    apply_retriever_to_dataset,
)


@dataclass
class DummyResult:
    document: str | None = None
    content: str | None = None
    score: float | None = None
    doc_id: int | str | None = None
    metadata: dict | None = None


class DummyRetriever:
    def __init__(self, results):
        self._results = results
        self.queries: list[tuple[str, int]] = []

    def search(self, query: str, top_k: int = 5):
        self.queries.append((query, top_k))
        return self._results


def test_apply_retriever_populates_contexts_and_metadata() -> None:
    test_cases = [
        TestCase(id="tc-1", question="Q1", answer="A1", contexts=[]),
        TestCase(id="tc-2", question="Q2", answer="A2", contexts=["existing"]),
    ]
    dataset = Dataset(name="test", version="1.0.0", test_cases=test_cases)
    results = [
        DummyResult(
            document="context-1",
            score=0.91,
            doc_id=1,
            metadata={"kg": {"entities": ["e1"], "relations": ["r1"], "community_id": "c1"}},
        )
    ]
    retriever = DummyRetriever(results)

    metadata = apply_retriever_to_dataset(
        dataset=dataset,
        retriever=retriever,
        top_k=2,
        doc_ids=["doc-a", "doc-b"],
    )

    assert retriever.queries == [("Q1", 2)]
    assert test_cases[0].contexts == ["context-1"]
    assert test_cases[1].contexts == ["existing"]
    assert metadata["tc-1"]["doc_ids"] == ["doc-b"]
    assert metadata["tc-1"]["scores"] == [0.91]
    assert metadata["tc-1"]["top_k"] == 2
    assert metadata["tc-1"]["graph_nodes"] == 1
    assert metadata["tc-1"]["graph_edges"] == 1
    assert metadata["tc-1"]["community_id"] == "c1"
    assert metadata["tc-1"]["retriever"] == "graphrag"
    assert metadata["tc-1"]["graphrag"]["docs"][0]["doc_id"] == "doc-b"
    assert metadata["tc-1"]["graphrag"]["docs"][0]["sources"]["kg"]["entities"] == ["e1"]


def test_normalize_retrieval_results_ignores_missing_scores() -> None:
    results = [
        DummyResult(document="doc-1", score=0.3, doc_id="id-1"),
        DummyResult(document="doc-2", score=None, doc_id=None),
    ]

    contexts, doc_ids, scores = _normalize_retrieval_results(results, doc_ids=["doc-a"])

    assert contexts == ["doc-1", "doc-2"]
    assert doc_ids == ["id-1", "doc_2"]
    assert scores == []


def test_normalize_retrieval_results_uses_content_field() -> None:
    results = [
        DummyResult(content="content-1", score=0.5),
        DummyResult(document="", content=None),
    ]

    contexts, doc_ids, scores = _normalize_retrieval_results(results, doc_ids=[])

    assert contexts == ["content-1"]
    assert doc_ids == ["doc_1"]
    assert scores == [0.5]


def test_extract_graph_attributes_collects_metadata() -> None:
    results = [
        DummyResult(metadata={"kg": {"entities": ["n1", "n2"], "relations": ["r1"]}}),
        DummyResult(metadata={"community_id": "c-2"}),
    ]

    attributes = _extract_graph_attributes(results)

    assert attributes["graph_nodes"] == 2
    assert attributes["graph_edges"] == 1
    assert attributes["subgraph_size"] == 3
    assert attributes["community_id"] == "c-2"


def test_compact_values_returns_sorted_list() -> None:
    values = {"b", "a"}
    assert _compact_values(values) == ["a", "b"]
    assert _compact_values({"only"}) == "only"


def test_extract_graph_attributes_empty_results() -> None:
    results = [SimpleNamespace(metadata=None)]
    assert _extract_graph_attributes(results) == {}
