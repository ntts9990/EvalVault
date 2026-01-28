from __future__ import annotations

from typing import Protocol

from evalvault.domain.entities.graph_rag import EntityNode, KnowledgeSubgraph


class GraphRetrieverPort(Protocol):
    def extract_entities(self, text: str) -> list[EntityNode]:
        """텍스트에서 엔티티 추출"""

    def build_subgraph(
        self,
        query: str,
        max_hops: int = 2,
        max_nodes: int = 20,
    ) -> KnowledgeSubgraph:
        """질의 관련 서브그래프 구축"""

    def generate_context(
        self,
        subgraph: KnowledgeSubgraph,
    ) -> str:
        """서브그래프를 LLM 컨텍스트로 변환"""
