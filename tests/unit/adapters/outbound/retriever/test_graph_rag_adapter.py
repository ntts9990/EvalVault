"""Unit tests for GraphRAGAdapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evalvault.adapters.outbound.kg.networkx_adapter import NetworkXKnowledgeGraph
from evalvault.adapters.outbound.retriever.graph_rag_adapter import GraphRAGAdapter


@pytest.fixture
def sample_kg() -> NetworkXKnowledgeGraph:
    fixture_path = Path("tests/fixtures/kg/minimal_graph.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    return NetworkXKnowledgeGraph.from_dict(data)


def test_extract_entities_matches_known_kg(sample_kg: NetworkXKnowledgeGraph) -> None:
    adapter = GraphRAGAdapter(sample_kg)

    nodes = adapter.extract_entities("AlphaCorp provides BetaPlan")

    names = {node.name for node in nodes}
    assert {"AlphaCorp", "BetaPlan"}.issubset(names)


def test_build_subgraph_returns_nodes_and_edges(sample_kg: NetworkXKnowledgeGraph) -> None:
    adapter = GraphRAGAdapter(sample_kg)

    subgraph = adapter.build_subgraph("AlphaCorp provides BetaPlan", max_hops=1, max_nodes=5)

    assert len(subgraph.nodes) == 2
    assert len(subgraph.edges) == 1
    assert subgraph.edges[0].relation_type == "provides"
    assert subgraph.relevance_score > 0


def test_generate_context_from_subgraph(sample_kg: NetworkXKnowledgeGraph) -> None:
    adapter = GraphRAGAdapter(sample_kg)

    subgraph = adapter.build_subgraph("AlphaCorp provides BetaPlan", max_hops=1, max_nodes=5)
    context = adapter.generate_context(subgraph)

    assert "Entities:" in context
    assert "Relations:" in context
    assert "AlphaCorp" in context
    assert "BetaPlan" in context
