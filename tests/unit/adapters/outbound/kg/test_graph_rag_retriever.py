"""Unit tests for GraphRAGRetriever."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from evalvault.adapters.outbound.kg.graph_rag_retriever import GraphRAGResult, GraphRAGRetriever
from evalvault.adapters.outbound.kg.networkx_adapter import NetworkXKnowledgeGraph
from evalvault.domain.entities.kg import EntityModel


@dataclass
class _FakeResult:
    doc_id: str
    score: float = 0.0


class _FakeRetriever:
    def __init__(self, results: list[_FakeResult]) -> None:
        self._results = results

    def search(self, query: str, top_k: int = 5) -> list[_FakeResult]:
        return self._results[:top_k]


@pytest.fixture
def sample_kg() -> NetworkXKnowledgeGraph:
    fixture_path = Path("tests/fixtures/kg/minimal_graph.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    return NetworkXKnowledgeGraph.from_dict(data)


def test_graphrag_search_schema_and_rrf(sample_kg: NetworkXKnowledgeGraph) -> None:
    bm25 = _FakeRetriever(
        [
            _FakeResult(doc_id="doc-002", score=0.9),
            _FakeResult(doc_id="doc-003", score=0.8),
        ]
    )
    dense = _FakeRetriever(
        [
            _FakeResult(doc_id="doc-003", score=0.95),
            _FakeResult(doc_id="doc-001", score=0.7),
        ]
    )
    retriever = GraphRAGRetriever(sample_kg, bm25_retriever=bm25, dense_retriever=dense)

    results = retriever.search("AlphaCorp provides BetaPlan", top_k=3)

    assert results
    assert all(isinstance(result, GraphRAGResult) for result in results)
    assert results[0].doc_id == "doc-001"
    assert results[1].doc_id == "doc-002"
    assert "kg" in results[0].metadata


def test_graphrag_search_falls_back_to_chunks(sample_kg: NetworkXKnowledgeGraph) -> None:
    bm25 = _FakeRetriever(
        [
            _FakeResult(doc_id="doc-002", score=0.9),
            _FakeResult(doc_id="doc-001", score=0.5),
        ]
    )
    retriever = GraphRAGRetriever(sample_kg, bm25_retriever=bm25)

    results = retriever.search("Unrelated query", top_k=2)

    assert [result.doc_id for result in results] == ["doc-002", "doc-001"]
    assert results[0].metadata["bm25"]["rank"] == 1


def test_graphrag_doc_id_mapping(sample_kg: NetworkXKnowledgeGraph) -> None:
    bm25 = _FakeRetriever([_FakeResult(doc_id=0, score=0.9)])
    documents = ["문서 A", "문서 B"]
    document_ids = ["doc-001", "doc-002"]
    retriever = GraphRAGRetriever(
        sample_kg,
        bm25_retriever=bm25,
        documents=documents,
        document_ids=document_ids,
    )

    results = retriever.search("AlphaCorp", top_k=1)

    assert results
    assert results[0].doc_id == "doc-001"
    assert results[0].document == "문서 A"


def test_graphrag_keyword_extractor_matches_entities(sample_kg: NetworkXKnowledgeGraph) -> None:
    def keyword_extractor(text: str) -> list[str]:
        return ["AlphaCorp"]

    retriever = GraphRAGRetriever(sample_kg, keyword_extractor=keyword_extractor)

    results = retriever.search("Unrelated query", top_k=1)

    assert results
    assert results[0].doc_id == "doc-001"


def test_graphrag_update_graph_merges_entities(sample_kg: NetworkXKnowledgeGraph) -> None:
    retriever = GraphRAGRetriever(sample_kg)
    delta = NetworkXKnowledgeGraph()
    delta.add_entity(
        EntityModel(
            name="GammaCorp",
            entity_type="organization",
            source_document_id="doc-003",
            confidence=0.9,
            provenance="manual",
        )
    )

    stats = retriever.update_graph(delta)
    results = retriever.search("GammaCorp", top_k=1)

    assert stats["entities_added"] == 1
    assert results
    assert results[0].doc_id == "doc-003"
