from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EntityNode:
    entity_id: str
    name: str
    entity_type: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationEdge:
    source_id: str
    target_id: str
    relation_type: str
    weight: float = 1.0
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeSubgraph:
    """질의에 대해 추출된 관련 서브그래프."""

    nodes: list[EntityNode]
    edges: list[RelationEdge]
    relevance_score: float
