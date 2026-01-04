"""NetworkX-based Knowledge Graph adapter.

This adapter provides a flexible graph-based data structure for knowledge graph
operations, supporting entity and relation management with confidence scores.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import networkx as nx

from evalvault.domain.entities.kg import EntityModel, RelationModel

if TYPE_CHECKING:
    from collections.abc import Iterator


class NetworkXKnowledgeGraph:
    """NetworkX 기반 지식 그래프 어댑터.

    엔티티를 노드로, 관계를 엣지로 표현하는 방향성 멀티그래프.
    신뢰도 점수를 지원하며, 그래프 탐색 및 서브그래프 추출 기능을 제공합니다.
    """

    def __init__(self) -> None:
        """Initialize the NetworkX knowledge graph."""
        self._graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self._entity_metadata: dict[str, EntityModel] = {}
        self._relation_metadata: dict[tuple[str, str, int], RelationModel] = {}

    @property
    def graph(self) -> nx.MultiDiGraph:
        """Return the underlying NetworkX graph."""
        return self._graph

    # -------------------------------------------------------------------------
    # Entity Operations
    # -------------------------------------------------------------------------

    def add_entity(self, entity: EntityModel) -> None:
        """그래프에 엔티티 추가.

        Args:
            entity: 추가할 엔티티 모델

        Note:
            동일한 이름의 엔티티가 존재하면 속성을 갱신합니다.
        """
        attributes = entity.to_node_attributes()
        if self._graph.has_node(entity.name):
            self._graph.nodes[entity.name].update(attributes)
        else:
            self._graph.add_node(entity.name, **attributes)
        self._entity_metadata[entity.name] = entity

    def get_entity(self, name: str) -> EntityModel | None:
        """엔티티 조회.

        Args:
            name: 엔티티 이름

        Returns:
            엔티티 모델 또는 None
        """
        return self._entity_metadata.get(name)

    def has_entity(self, name: str) -> bool:
        """엔티티 존재 여부 확인.

        Args:
            name: 엔티티 이름

        Returns:
            존재 여부
        """
        return self._graph.has_node(name)

    def remove_entity(self, name: str) -> bool:
        """엔티티 삭제.

        Args:
            name: 삭제할 엔티티 이름

        Returns:
            삭제 성공 여부
        """
        if not self._graph.has_node(name):
            return False

        self._graph.remove_node(name)
        self._entity_metadata.pop(name, None)

        # 관련 관계 메타데이터 정리
        keys_to_remove = [
            key for key in self._relation_metadata if key[0] == name or key[1] == name
        ]
        for key in keys_to_remove:
            del self._relation_metadata[key]

        return True

    def get_all_entities(self) -> list[EntityModel]:
        """모든 엔티티 조회.

        Returns:
            엔티티 모델 리스트
        """
        return list(self._entity_metadata.values())

    def get_entities_by_type(self, entity_type: str) -> list[EntityModel]:
        """특정 타입의 엔티티 조회.

        Args:
            entity_type: 엔티티 타입

        Returns:
            해당 타입의 엔티티 리스트
        """
        return [e for e in self._entity_metadata.values() if e.entity_type == entity_type]

    def get_entities_by_confidence(
        self, min_confidence: float = 0.0, max_confidence: float = 1.0
    ) -> list[EntityModel]:
        """신뢰도 범위 내의 엔티티 조회.

        Args:
            min_confidence: 최소 신뢰도
            max_confidence: 최대 신뢰도

        Returns:
            조건에 맞는 엔티티 리스트
        """
        return [
            e
            for e in self._entity_metadata.values()
            if min_confidence <= e.confidence <= max_confidence
        ]

    def get_high_confidence_entities(self, threshold: float = 0.8) -> list[EntityModel]:
        """고신뢰도 엔티티 조회.

        Args:
            threshold: 신뢰도 임계값

        Returns:
            임계값 이상의 엔티티 리스트
        """
        return self.get_entities_by_confidence(min_confidence=threshold)

    def get_low_confidence_entities(self, threshold: float = 0.6) -> list[EntityModel]:
        """저신뢰도 엔티티 조회.

        Args:
            threshold: 신뢰도 임계값

        Returns:
            임계값 미만의 엔티티 리스트
        """
        return self.get_entities_by_confidence(max_confidence=threshold)

    # -------------------------------------------------------------------------
    # Relation Operations
    # -------------------------------------------------------------------------

    def add_relation(self, relation: RelationModel) -> None:
        """그래프에 관계 추가.

        Args:
            relation: 추가할 관계 모델
        """
        attrs = relation.to_edge_attributes()
        attrs["model"] = relation
        key = self._graph.add_edge(relation.source, relation.target, **attrs)
        self._relation_metadata[(relation.source, relation.target, key)] = relation

    def merge(self, other: NetworkXKnowledgeGraph) -> dict[str, int]:
        """다른 Knowledge Graph를 병합합니다."""

        stats = {"entities_added": 0, "entities_updated": 0, "relations_added": 0}

        for entity in other.get_all_entities():
            if self.has_entity(entity.name):
                stats["entities_updated"] += 1
            else:
                stats["entities_added"] += 1
            self.add_entity(entity)

        for relation in other.get_all_relations():
            if not (self.has_entity(relation.source) and self.has_entity(relation.target)):
                continue
            existing = self.get_relations(relation.source, relation.target)
            if any(rel.relation_type == relation.relation_type for rel in existing):
                continue
            self.add_relation(relation)
            stats["relations_added"] += 1

        return stats

    def get_relations(self, source: str, target: str) -> list[RelationModel]:
        """두 엔티티 간의 모든 관계 조회.

        Args:
            source: 출발 엔티티
            target: 도착 엔티티

        Returns:
            관계 모델 리스트
        """
        if not self._graph.has_edge(source, target):
            return []

        relations = []
        for _key, data in self._graph[source][target].items():
            model = data.get("model")
            if isinstance(model, RelationModel):
                relations.append(model)
            else:
                relations.append(self._relation_from_edge(source, target, data))
        return relations

    def has_relation(self, source: str, target: str) -> bool:
        """관계 존재 여부 확인.

        Args:
            source: 출발 엔티티
            target: 도착 엔티티

        Returns:
            관계 존재 여부
        """
        return self._graph.has_edge(source, target)

    def get_relations_for_entity(self, name: str) -> list[RelationModel]:
        """엔티티와 관련된 모든 관계 조회 (in/out 모두).

        Args:
            name: 엔티티 이름

        Returns:
            관계 모델 리스트
        """
        if not self._graph.has_node(name):
            return []

        relations: list[RelationModel] = []

        # 나가는 관계
        for _, target, data in self._graph.out_edges(name, data=True):
            relations.append(self._relation_from_edge(name, target, data))

        # 들어오는 관계
        for source, _, data in self._graph.in_edges(name, data=True):
            relations.append(self._relation_from_edge(source, name, data))

        return relations

    def get_outgoing_relations(self, name: str) -> list[RelationModel]:
        """엔티티에서 나가는 관계만 조회.

        Args:
            name: 엔티티 이름

        Returns:
            나가는 관계 리스트
        """
        if not self._graph.has_node(name):
            return []

        return [
            self._relation_from_edge(name, target, data)
            for _, target, data in self._graph.out_edges(name, data=True)
        ]

    def get_incoming_relations(self, name: str) -> list[RelationModel]:
        """엔티티로 들어오는 관계만 조회.

        Args:
            name: 엔티티 이름

        Returns:
            들어오는 관계 리스트
        """
        if not self._graph.has_node(name):
            return []

        return [
            self._relation_from_edge(source, name, data)
            for source, _, data in self._graph.in_edges(name, data=True)
        ]

    def get_all_relations(self) -> list[RelationModel]:
        """모든 관계 조회.

        Returns:
            관계 모델 리스트
        """
        relations = []
        for source, target, data in self._graph.edges(data=True):
            relations.append(self._relation_from_edge(source, target, data))
        return relations

    # -------------------------------------------------------------------------
    # Graph Traversal
    # -------------------------------------------------------------------------

    def find_neighbors(self, entity_id: str, depth: int = 1) -> list[EntityModel]:
        """이웃 엔티티 탐색 (BFS).

        Args:
            entity_id: 시작 엔티티 이름
            depth: 탐색 깊이 (기본값: 1)

        Returns:
            이웃 엔티티 리스트
        """
        if not self._graph.has_node(entity_id):
            return []

        if depth < 1:
            return []

        visited: set[str] = {entity_id}
        current_level: set[str] = {entity_id}

        for _ in range(depth):
            next_level: set[str] = set()
            for node in current_level:
                # 나가는 방향
                for successor in self._graph.successors(node):
                    if successor not in visited:
                        next_level.add(successor)
                        visited.add(successor)
                # 들어오는 방향도 고려
                for predecessor in self._graph.predecessors(node):
                    if predecessor not in visited:
                        next_level.add(predecessor)
                        visited.add(predecessor)
            current_level = next_level

            if not current_level:
                break

        # 시작 노드 제외
        visited.discard(entity_id)

        return [self._entity_metadata[name] for name in visited if name in self._entity_metadata]

    def find_path(self, start: str, end: str, max_depth: int = 5) -> list[str] | None:
        """두 엔티티 간 최단 경로 탐색.

        Args:
            start: 시작 엔티티
            end: 도착 엔티티
            max_depth: 최대 탐색 깊이

        Returns:
            경로 (엔티티 이름 리스트) 또는 None
        """
        if not self._graph.has_node(start) or not self._graph.has_node(end):
            return None

        try:
            path = nx.shortest_path(self._graph, source=start, target=end, weight=None)
            if len(path) - 1 <= max_depth:
                return list(path)
            return None
        except nx.NetworkXNoPath:
            return None

    def find_all_paths(self, start: str, end: str, max_depth: int = 3) -> list[list[str]]:
        """두 엔티티 간 모든 경로 탐색.

        Args:
            start: 시작 엔티티
            end: 도착 엔티티
            max_depth: 최대 경로 길이

        Returns:
            경로 리스트
        """
        if not self._graph.has_node(start) or not self._graph.has_node(end):
            return []

        try:
            paths = nx.all_simple_paths(self._graph, source=start, target=end, cutoff=max_depth)
            return list(paths)
        except nx.NetworkXError:
            return []

    def get_successors(self, name: str) -> list[str]:
        """노드의 후속 노드 조회 (나가는 엣지).

        Args:
            name: 엔티티 이름

        Returns:
            후속 노드 이름 리스트
        """
        if not self._graph.has_node(name):
            return []
        return list(self._graph.successors(name))

    def get_predecessors(self, name: str) -> list[str]:
        """노드의 선행 노드 조회 (들어오는 엣지).

        Args:
            name: 엔티티 이름

        Returns:
            선행 노드 이름 리스트
        """
        if not self._graph.has_node(name):
            return []
        return list(self._graph.predecessors(name))

    # -------------------------------------------------------------------------
    # Subgraph Operations
    # -------------------------------------------------------------------------

    def get_subgraph(self, entity_ids: list[str]) -> NetworkXKnowledgeGraph:
        """특정 엔티티들로 서브그래프 생성.

        Args:
            entity_ids: 포함할 엔티티 이름 리스트

        Returns:
            새로운 NetworkXKnowledgeGraph 인스턴스
        """
        subgraph = NetworkXKnowledgeGraph()

        valid_ids = [eid for eid in entity_ids if eid in self._entity_metadata]

        # 엔티티 추가
        for entity_id in valid_ids:
            entity = self._entity_metadata.get(entity_id)
            if entity:
                subgraph.add_entity(entity)

        # 관계 추가 (두 엔티티 모두 서브그래프에 포함된 경우만)
        valid_set = set(valid_ids)
        for source, target, data in self._graph.edges(data=True):
            if source in valid_set and target in valid_set:
                model = data.get("model")
                if isinstance(model, RelationModel):
                    subgraph.add_relation(model)
                else:
                    relation = self._relation_from_edge(source, target, data)
                    subgraph.add_relation(relation)

        return subgraph

    def get_neighborhood_subgraph(self, center: str, radius: int = 1) -> NetworkXKnowledgeGraph:
        """중심 엔티티 주변의 서브그래프 생성.

        Args:
            center: 중심 엔티티
            radius: 탐색 반경

        Returns:
            새로운 NetworkXKnowledgeGraph 인스턴스
        """
        if not self._graph.has_node(center):
            return NetworkXKnowledgeGraph()

        neighbors = self.find_neighbors(center, depth=radius)
        entity_ids = [center] + [n.name for n in neighbors]
        return self.get_subgraph(entity_ids)

    # -------------------------------------------------------------------------
    # Graph Statistics
    # -------------------------------------------------------------------------

    def get_node_count(self) -> int:
        """노드 개수 조회."""
        return self._graph.number_of_nodes()

    def get_edge_count(self) -> int:
        """엣지 개수 조회."""
        return self._graph.number_of_edges()

    def get_degree(self, name: str) -> int:
        """노드의 차수 조회.

        Args:
            name: 엔티티 이름

        Returns:
            차수 (in + out)
        """
        if not self._graph.has_node(name):
            return 0
        return self._graph.degree(name)

    def get_in_degree(self, name: str) -> int:
        """노드의 입차수 조회."""
        if not self._graph.has_node(name):
            return 0
        return self._graph.in_degree(name)

    def get_out_degree(self, name: str) -> int:
        """노드의 출차수 조회."""
        if not self._graph.has_node(name):
            return 0
        return self._graph.out_degree(name)

    def get_isolated_entities(self) -> list[EntityModel]:
        """고립된 엔티티 조회 (엣지 없음)."""
        isolated = []
        for node in self._graph.nodes():
            if self._graph.degree(node) == 0:
                entity = self._entity_metadata.get(node)
                if entity:
                    isolated.append(entity)
        return isolated

    def get_hub_entities(self, min_degree: int = 5) -> list[EntityModel]:
        """허브 엔티티 조회 (고차수 노드).

        Args:
            min_degree: 최소 차수

        Returns:
            허브 엔티티 리스트
        """
        hubs = []
        for node in self._graph.nodes():
            if self._graph.degree(node) >= min_degree:
                entity = self._entity_metadata.get(node)
                if entity:
                    hubs.append(entity)
        return hubs

    def get_statistics(self) -> dict[str, Any]:
        """그래프 통계 정보 조회.

        Returns:
            통계 정보 딕셔너리
        """
        entity_types: dict[str, int] = {}
        for entity in self._entity_metadata.values():
            entity_types[entity.entity_type] = entity_types.get(entity.entity_type, 0) + 1

        relation_types: dict[str, int] = {}
        for _, _, data in self._graph.edges(data=True):
            rel_type = data.get("relation_type", "unknown")
            relation_types[rel_type] = relation_types.get(rel_type, 0) + 1

        avg_confidence = 0.0
        if self._entity_metadata:
            avg_confidence = sum(e.confidence for e in self._entity_metadata.values()) / len(
                self._entity_metadata
            )

        return {
            "num_entities": self.get_node_count(),
            "num_relations": self.get_edge_count(),
            "entity_types": entity_types,
            "relation_types": relation_types,
            "isolated_entities": len(self.get_isolated_entities()),
            "average_entity_confidence": round(avg_confidence, 3),
        }

    # -------------------------------------------------------------------------
    # Import/Export
    # -------------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """그래프를 딕셔너리로 직렬화.

        Returns:
            직렬화된 딕셔너리
        """
        entities = [e.model_dump() for e in self._entity_metadata.values()]
        relations = [
            self._relation_from_edge(s, t, d).model_dump()
            for s, t, d in self._graph.edges(data=True)
        ]
        return {
            "entities": entities,
            "relations": relations,
            "statistics": self.get_statistics(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetworkXKnowledgeGraph:
        """딕셔너리에서 그래프 복원.

        Args:
            data: 직렬화된 딕셔너리

        Returns:
            복원된 NetworkXKnowledgeGraph 인스턴스
        """
        kg = cls()

        for entity_data in data.get("entities", []):
            entity = EntityModel(**entity_data)
            kg.add_entity(entity)

        for relation_data in data.get("relations", []):
            relation = RelationModel(**relation_data)
            if kg.has_entity(relation.source) and kg.has_entity(relation.target):
                kg.add_relation(relation)

        return kg

    def clear(self) -> None:
        """그래프 초기화."""
        self._graph.clear()
        self._entity_metadata.clear()
        self._relation_metadata.clear()

    # -------------------------------------------------------------------------
    # Iterator Support
    # -------------------------------------------------------------------------

    def __iter__(self) -> Iterator[EntityModel]:
        """엔티티 이터레이터."""
        return iter(self._entity_metadata.values())

    def __len__(self) -> int:
        """엔티티 개수."""
        return len(self._entity_metadata)

    def __contains__(self, name: str) -> bool:
        """엔티티 포함 여부."""
        return name in self._entity_metadata

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _relation_from_edge(source: str, target: str, data: dict) -> RelationModel:
        """NetworkX 엣지 데이터에서 RelationModel 복원."""
        model = data.get("model")
        if isinstance(model, RelationModel):
            return model

        attributes = data.get("attributes") or {}
        return RelationModel(
            source=source,
            target=target,
            relation_type=data.get("relation_type", "unknown"),
            confidence=data.get("confidence", 1.0),
            provenance=data.get("provenance", "unknown"),
            attributes=attributes,
        )
