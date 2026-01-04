"""Unit tests for NetworkX Knowledge Graph adapter and query strategies."""

from __future__ import annotations

import pytest

from evalvault.adapters.outbound.kg.networkx_adapter import NetworkXKnowledgeGraph
from evalvault.adapters.outbound.kg.query_strategies import (
    ComparisonStrategy,
    CompositeQueryStrategy,
    GeneratedQuery,
    MultiHopStrategy,
    QueryStrategy,
    SingleHopStrategy,
)
from evalvault.domain.entities.kg import EntityModel, RelationModel

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def empty_kg() -> NetworkXKnowledgeGraph:
    """빈 지식 그래프 fixture."""
    return NetworkXKnowledgeGraph()


@pytest.fixture
def sample_entity() -> EntityModel:
    """샘플 엔티티 fixture."""
    return EntityModel(
        name="삼성생명",
        entity_type="organization",
        confidence=0.95,
        provenance="regex",
    )


@pytest.fixture
def sample_entities() -> list[EntityModel]:
    """여러 샘플 엔티티 fixture."""
    return [
        EntityModel(
            name="삼성생명",
            entity_type="organization",
            confidence=0.95,
            provenance="regex",
        ),
        EntityModel(
            name="종신보험",
            entity_type="product",
            confidence=0.9,
            provenance="regex",
        ),
        EntityModel(
            name="사망보험금",
            entity_type="coverage",
            confidence=0.85,
            provenance="regex",
        ),
        EntityModel(
            name="1억원",
            entity_type="money",
            confidence=0.8,
            provenance="regex",
        ),
        EntityModel(
            name="한화생명",
            entity_type="organization",
            confidence=0.95,
            provenance="regex",
        ),
        EntityModel(
            name="정기보험",
            entity_type="product",
            confidence=0.9,
            provenance="regex",
        ),
    ]


@pytest.fixture
def sample_relations() -> list[RelationModel]:
    """샘플 관계 fixture."""
    return [
        RelationModel(
            source="삼성생명",
            target="종신보험",
            relation_type="provides",
            confidence=0.9,
            provenance="regex",
        ),
        RelationModel(
            source="종신보험",
            target="사망보험금",
            relation_type="has_coverage",
            confidence=0.85,
            provenance="regex",
        ),
        RelationModel(
            source="사망보험금",
            target="1억원",
            relation_type="has_amount",
            confidence=0.8,
            provenance="regex",
        ),
        RelationModel(
            source="한화생명",
            target="정기보험",
            relation_type="provides",
            confidence=0.9,
            provenance="regex",
        ),
    ]


@pytest.fixture
def populated_kg(
    sample_entities: list[EntityModel], sample_relations: list[RelationModel]
) -> NetworkXKnowledgeGraph:
    """엔티티와 관계가 추가된 지식 그래프 fixture."""
    kg = NetworkXKnowledgeGraph()
    for entity in sample_entities:
        kg.add_entity(entity)
    for relation in sample_relations:
        kg.add_relation(relation)
    return kg


# =============================================================================
# NetworkXKnowledgeGraph Tests
# =============================================================================


class TestNetworkXKnowledgeGraphEntity:
    """NetworkXKnowledgeGraph 엔티티 관련 테스트."""

    def test_add_entity(self, empty_kg: NetworkXKnowledgeGraph, sample_entity: EntityModel) -> None:
        """엔티티 추가 테스트."""
        empty_kg.add_entity(sample_entity)

        assert empty_kg.has_entity(sample_entity.name)
        assert empty_kg.get_node_count() == 1

    def test_add_duplicate_entity_updates(
        self, empty_kg: NetworkXKnowledgeGraph, sample_entity: EntityModel
    ) -> None:
        """중복 엔티티 추가 시 갱신 테스트."""
        empty_kg.add_entity(sample_entity)

        updated_entity = EntityModel(
            name=sample_entity.name,
            entity_type="organization",
            confidence=0.99,
            provenance="llm",
        )
        empty_kg.add_entity(updated_entity)

        assert empty_kg.get_node_count() == 1
        retrieved = empty_kg.get_entity(sample_entity.name)
        assert retrieved is not None
        assert retrieved.confidence == 0.99
        assert retrieved.provenance == "llm"

    def test_get_entity(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """엔티티 조회 테스트."""
        entity = populated_kg.get_entity("삼성생명")

        assert entity is not None
        assert entity.entity_type == "organization"
        assert entity.confidence == 0.95

    def test_get_nonexistent_entity(self, empty_kg: NetworkXKnowledgeGraph) -> None:
        """존재하지 않는 엔티티 조회 테스트."""
        assert empty_kg.get_entity("없는엔티티") is None

    def test_has_entity(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """엔티티 존재 여부 확인 테스트."""
        assert populated_kg.has_entity("삼성생명")
        assert not populated_kg.has_entity("없는회사")

    def test_remove_entity(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """엔티티 삭제 테스트."""
        initial_count = populated_kg.get_node_count()

        result = populated_kg.remove_entity("삼성생명")

        assert result is True
        assert populated_kg.get_node_count() == initial_count - 1
        assert not populated_kg.has_entity("삼성생명")

    def test_remove_nonexistent_entity(self, empty_kg: NetworkXKnowledgeGraph) -> None:
        """존재하지 않는 엔티티 삭제 테스트."""
        result = empty_kg.remove_entity("없는엔티티")
        assert result is False

    def test_get_all_entities(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """모든 엔티티 조회 테스트."""
        entities = populated_kg.get_all_entities()

        assert len(entities) == 6
        names = [e.name for e in entities]
        assert "삼성생명" in names
        assert "종신보험" in names

    def test_get_entities_by_type(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """타입별 엔티티 조회 테스트."""
        organizations = populated_kg.get_entities_by_type("organization")
        products = populated_kg.get_entities_by_type("product")

        assert len(organizations) == 2
        assert len(products) == 2
        assert all(e.entity_type == "organization" for e in organizations)

    def test_get_entities_by_confidence(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """신뢰도 범위별 엔티티 조회 테스트."""
        high_conf = populated_kg.get_entities_by_confidence(min_confidence=0.9)
        low_conf = populated_kg.get_entities_by_confidence(max_confidence=0.85)

        assert len(high_conf) == 4  # 0.95, 0.95, 0.9, 0.9
        assert len(low_conf) == 2  # 0.85, 0.8

    def test_get_high_confidence_entities(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """고신뢰도 엔티티 조회 테스트."""
        high_conf = populated_kg.get_high_confidence_entities(threshold=0.9)

        assert len(high_conf) >= 2
        assert all(e.confidence >= 0.9 for e in high_conf)

    def test_get_low_confidence_entities(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """저신뢰도 엔티티 조회 테스트."""
        low_conf = populated_kg.get_low_confidence_entities(threshold=0.85)

        assert len(low_conf) >= 1
        assert all(e.confidence <= 0.85 for e in low_conf)


class TestNetworkXKnowledgeGraphRelation:
    """NetworkXKnowledgeGraph 관계 관련 테스트."""

    def test_add_relation(
        self, empty_kg: NetworkXKnowledgeGraph, sample_entities: list[EntityModel]
    ) -> None:
        """관계 추가 테스트."""
        for entity in sample_entities[:2]:
            empty_kg.add_entity(entity)

        relation = RelationModel(
            source="삼성생명",
            target="종신보험",
            relation_type="provides",
            confidence=0.9,
        )
        empty_kg.add_relation(relation)

        assert empty_kg.has_relation("삼성생명", "종신보험")
        assert empty_kg.get_edge_count() == 1

    def test_get_relations(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """관계 조회 테스트."""
        relations = populated_kg.get_relations("삼성생명", "종신보험")

        assert len(relations) == 1
        assert relations[0].relation_type == "provides"

    def test_has_relation(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """관계 존재 여부 확인 테스트."""
        assert populated_kg.has_relation("삼성생명", "종신보험")
        assert not populated_kg.has_relation("삼성생명", "없는상품")

    def test_get_relations_for_entity(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """엔티티 관련 모든 관계 조회 테스트."""
        relations = populated_kg.get_relations_for_entity("종신보험")

        # 들어오는 관계 1개 (삼성생명 -> 종신보험)
        # 나가는 관계 1개 (종신보험 -> 사망보험금)
        assert len(relations) == 2

    def test_get_outgoing_relations(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """나가는 관계만 조회 테스트."""
        outgoing = populated_kg.get_outgoing_relations("삼성생명")

        assert len(outgoing) == 1
        assert outgoing[0].target == "종신보험"

    def test_get_incoming_relations(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """들어오는 관계만 조회 테스트."""
        incoming = populated_kg.get_incoming_relations("종신보험")

        assert len(incoming) == 1
        assert incoming[0].source == "삼성생명"

    def test_get_all_relations(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """모든 관계 조회 테스트."""
        relations = populated_kg.get_all_relations()

        assert len(relations) == 4


class TestNetworkXKnowledgeGraphTraversal:
    """NetworkXKnowledgeGraph 그래프 탐색 테스트."""

    def test_find_neighbors_depth_1(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """1-hop 이웃 탐색 테스트."""
        neighbors = populated_kg.find_neighbors("삼성생명", depth=1)

        assert len(neighbors) == 1
        assert neighbors[0].name == "종신보험"

    def test_find_neighbors_depth_2(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """2-hop 이웃 탐색 테스트."""
        neighbors = populated_kg.find_neighbors("삼성생명", depth=2)

        names = [n.name for n in neighbors]
        assert "종신보험" in names
        assert "사망보험금" in names

    def test_find_neighbors_nonexistent_entity(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """존재하지 않는 엔티티의 이웃 탐색 테스트."""
        neighbors = populated_kg.find_neighbors("없는엔티티", depth=1)
        assert neighbors == []

    def test_find_neighbors_zero_depth(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """0 깊이 이웃 탐색 테스트."""
        neighbors = populated_kg.find_neighbors("삼성생명", depth=0)
        assert neighbors == []

    def test_find_path(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """경로 탐색 테스트."""
        path = populated_kg.find_path("삼성생명", "사망보험금")

        assert path is not None
        assert path == ["삼성생명", "종신보험", "사망보험금"]

    def test_find_path_no_connection(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """연결되지 않은 노드 간 경로 탐색 테스트."""
        path = populated_kg.find_path("삼성생명", "정기보험")
        assert path is None

    def test_find_all_paths(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """모든 경로 탐색 테스트."""
        paths = populated_kg.find_all_paths("삼성생명", "1억원", max_depth=5)

        assert len(paths) >= 1
        assert paths[0] == ["삼성생명", "종신보험", "사망보험금", "1억원"]

    def test_get_successors(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """후속 노드 조회 테스트."""
        successors = populated_kg.get_successors("삼성생명")

        assert "종신보험" in successors

    def test_get_predecessors(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """선행 노드 조회 테스트."""
        predecessors = populated_kg.get_predecessors("종신보험")

        assert "삼성생명" in predecessors


class TestNetworkXKnowledgeGraphSubgraph:
    """NetworkXKnowledgeGraph 서브그래프 테스트."""

    def test_get_subgraph(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """서브그래프 추출 테스트."""
        subgraph = populated_kg.get_subgraph(["삼성생명", "종신보험"])

        assert subgraph.get_node_count() == 2
        assert subgraph.has_entity("삼성생명")
        assert subgraph.has_entity("종신보험")
        assert subgraph.has_relation("삼성생명", "종신보험")

    def test_get_subgraph_with_invalid_ids(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """존재하지 않는 ID로 서브그래프 추출 테스트."""
        subgraph = populated_kg.get_subgraph(["삼성생명", "없는엔티티"])

        assert subgraph.get_node_count() == 1
        assert subgraph.has_entity("삼성생명")

    def test_get_neighborhood_subgraph(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """이웃 서브그래프 추출 테스트."""
        subgraph = populated_kg.get_neighborhood_subgraph("종신보험", radius=1)

        assert subgraph.get_node_count() >= 2
        assert subgraph.has_entity("종신보험")
        assert subgraph.has_entity("삼성생명") or subgraph.has_entity("사망보험금")


class TestNetworkXKnowledgeGraphStatistics:
    """NetworkXKnowledgeGraph 통계 테스트."""

    def test_get_node_count(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """노드 개수 조회 테스트."""
        assert populated_kg.get_node_count() == 6

    def test_get_edge_count(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """엣지 개수 조회 테스트."""
        assert populated_kg.get_edge_count() == 4

    def test_get_degree(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """노드 차수 조회 테스트."""
        # 종신보험: in 1 (삼성생명) + out 1 (사망보험금) = 2
        assert populated_kg.get_degree("종신보험") == 2

    def test_get_in_degree(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """노드 입차수 조회 테스트."""
        assert populated_kg.get_in_degree("종신보험") == 1

    def test_get_out_degree(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """노드 출차수 조회 테스트."""
        assert populated_kg.get_out_degree("삼성생명") == 1

    def test_get_isolated_entities(self, empty_kg: NetworkXKnowledgeGraph) -> None:
        """고립된 엔티티 조회 테스트."""
        entity = EntityModel(
            name="고립된엔티티",
            entity_type="organization",
            confidence=0.9,
        )
        empty_kg.add_entity(entity)

        isolated = empty_kg.get_isolated_entities()

        assert len(isolated) == 1
        assert isolated[0].name == "고립된엔티티"

    def test_get_hub_entities(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """허브 엔티티 조회 테스트 (고차수 노드)."""
        # 현재 그래프에서 차수가 5 이상인 노드는 없음
        hubs = populated_kg.get_hub_entities(min_degree=5)
        assert len(hubs) == 0

        # 차수 1 이상인 노드는 있음
        hubs_low = populated_kg.get_hub_entities(min_degree=1)
        assert len(hubs_low) >= 1

    def test_get_statistics(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """통계 정보 조회 테스트."""
        stats = populated_kg.get_statistics()

        assert stats["num_entities"] == 6
        assert stats["num_relations"] == 4
        assert "entity_types" in stats
        assert "relation_types" in stats
        assert stats["entity_types"]["organization"] == 2


class TestNetworkXKnowledgeGraphSerialization:
    """NetworkXKnowledgeGraph 직렬화 테스트."""

    def test_to_dict(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """딕셔너리 직렬화 테스트."""
        data = populated_kg.to_dict()

        assert "entities" in data
        assert "relations" in data
        assert "statistics" in data
        assert len(data["entities"]) == 6
        assert len(data["relations"]) == 4

    def test_from_dict(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """딕셔너리에서 복원 테스트."""
        data = populated_kg.to_dict()
        restored = NetworkXKnowledgeGraph.from_dict(data)

        assert restored.get_node_count() == populated_kg.get_node_count()
        assert restored.get_edge_count() == populated_kg.get_edge_count()
        assert restored.has_entity("삼성생명")

    def test_clear(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """그래프 초기화 테스트."""
        populated_kg.clear()

        assert populated_kg.get_node_count() == 0
        assert populated_kg.get_edge_count() == 0


class TestNetworkXKnowledgeGraphMerge:
    """NetworkXKnowledgeGraph 병합 테스트."""

    def test_merge_adds_entities_and_relations(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        delta = NetworkXKnowledgeGraph()
        delta.add_entity(
            EntityModel(
                name="추가회사",
                entity_type="organization",
                confidence=0.8,
                provenance="manual",
            )
        )
        delta.add_entity(
            EntityModel(
                name="추가상품",
                entity_type="product",
                confidence=0.7,
                provenance="manual",
            )
        )
        delta.add_relation(
            RelationModel(
                source="추가회사",
                target="추가상품",
                relation_type="provides",
                confidence=0.6,
                provenance="manual",
            )
        )

        stats = populated_kg.merge(delta)

        assert stats["entities_added"] == 2
        assert stats["relations_added"] == 1
        assert populated_kg.has_entity("추가회사")

    def test_merge_updates_existing_entity(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        delta = NetworkXKnowledgeGraph()
        delta.add_entity(
            EntityModel(
                name="삼성생명",
                entity_type="organization",
                confidence=0.99,
                provenance="manual",
            )
        )

        stats = populated_kg.merge(delta)

        assert stats["entities_updated"] == 1
        updated = populated_kg.get_entity("삼성생명")
        assert updated is not None
        assert updated.confidence == 0.99


class TestNetworkXKnowledgeGraphIterator:
    """NetworkXKnowledgeGraph 이터레이터 테스트."""

    def test_iter(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """이터레이터 테스트."""
        entities = list(populated_kg)

        assert len(entities) == 6

    def test_len(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """길이 테스트."""
        assert len(populated_kg) == 6

    def test_contains(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """포함 여부 테스트."""
        assert "삼성생명" in populated_kg
        assert "없는회사" not in populated_kg


# =============================================================================
# Query Strategy Tests
# =============================================================================


class TestSingleHopStrategy:
    """SingleHopStrategy 테스트."""

    def test_strategy_name(self) -> None:
        """전략 이름 테스트."""
        strategy = SingleHopStrategy()
        assert strategy.get_strategy_name() == "single_hop"

    def test_generate_queries_with_relations(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """관계가 있는 엔티티에 대한 쿼리 생성 테스트."""
        strategy = SingleHopStrategy()
        entity = populated_kg.get_entity("삼성생명")
        assert entity is not None

        queries = strategy.generate_queries(populated_kg, entity)

        assert len(queries) >= 1
        assert all(isinstance(q, GeneratedQuery) for q in queries)
        assert all(q.query_type == "single_hop" for q in queries)

    def test_generate_queries_without_relations(self, empty_kg: NetworkXKnowledgeGraph) -> None:
        """관계가 없는 엔티티에 대한 쿼리 생성 테스트."""
        entity = EntityModel(
            name="고립된엔티티",
            entity_type="organization",
            confidence=0.9,
        )
        empty_kg.add_entity(entity)

        strategy = SingleHopStrategy()
        queries = strategy.generate_queries(empty_kg, entity)

        assert len(queries) == 1
        assert queries[0].metadata is not None
        assert queries[0].metadata.get("no_relations") is True

    def test_query_contains_entity_name(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """생성된 쿼리에 엔티티 이름이 포함되는지 테스트."""
        strategy = SingleHopStrategy()
        entity = populated_kg.get_entity("삼성생명")
        assert entity is not None

        queries = strategy.generate_queries(populated_kg, entity)

        for query in queries:
            assert entity.name in query.query or any(entity.name in e for e in query.entities)

    def test_is_query_strategy(self) -> None:
        """QueryStrategy 프로토콜 호환성 테스트."""
        strategy = SingleHopStrategy()
        assert isinstance(strategy, QueryStrategy)


class TestMultiHopStrategy:
    """MultiHopStrategy 테스트."""

    def test_strategy_name(self) -> None:
        """전략 이름 테스트."""
        strategy = MultiHopStrategy()
        assert strategy.get_strategy_name() == "multi_hop"

    def test_generate_2hop_queries(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """2-hop 쿼리 생성 테스트."""
        strategy = MultiHopStrategy(max_hops=2)
        entity = populated_kg.get_entity("삼성생명")
        assert entity is not None

        queries = strategy.generate_queries(populated_kg, entity)

        if queries:  # 경로가 존재하는 경우만
            assert all(q.query_type == "multi_hop" for q in queries)
            assert all(len(q.entities) >= 3 for q in queries)

    def test_max_hops_limit(self) -> None:
        """최대 홉 수 제한 테스트."""
        strategy = MultiHopStrategy(max_hops=5)
        # 내부적으로 3으로 제한됨
        assert strategy._max_hops == 3

    def test_is_query_strategy(self) -> None:
        """QueryStrategy 프로토콜 호환성 테스트."""
        strategy = MultiHopStrategy()
        assert isinstance(strategy, QueryStrategy)


class TestComparisonStrategy:
    """ComparisonStrategy 테스트."""

    def test_strategy_name(self) -> None:
        """전략 이름 테스트."""
        strategy = ComparisonStrategy()
        assert strategy.get_strategy_name() == "comparison"

    def test_generate_comparison_queries(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """비교 쿼리 생성 테스트."""
        strategy = ComparisonStrategy()
        entity = populated_kg.get_entity("삼성생명")
        assert entity is not None

        queries = strategy.generate_queries(populated_kg, entity)

        # 같은 타입 (organization) 엔티티가 있으므로 비교 쿼리 생성
        assert len(queries) >= 1
        assert all(q.query_type == "comparison" for q in queries)

    def test_no_queries_when_no_comparable_entities(self, empty_kg: NetworkXKnowledgeGraph) -> None:
        """비교 가능한 엔티티가 없을 때 테스트."""
        entity = EntityModel(
            name="유일한엔티티",
            entity_type="unique_type",
            confidence=0.9,
        )
        empty_kg.add_entity(entity)

        strategy = ComparisonStrategy()
        queries = strategy.generate_queries(empty_kg, entity)

        assert len(queries) == 0

    def test_comparison_query_contains_both_entities(
        self, populated_kg: NetworkXKnowledgeGraph
    ) -> None:
        """비교 쿼리에 두 엔티티가 모두 포함되는지 테스트."""
        strategy = ComparisonStrategy()
        entity = populated_kg.get_entity("삼성생명")
        assert entity is not None

        queries = strategy.generate_queries(populated_kg, entity)

        for query in queries:
            assert len(query.entities) >= 2

    def test_is_query_strategy(self) -> None:
        """QueryStrategy 프로토콜 호환성 테스트."""
        strategy = ComparisonStrategy()
        assert isinstance(strategy, QueryStrategy)


class TestCompositeQueryStrategy:
    """CompositeQueryStrategy 테스트."""

    def test_default_strategies(self) -> None:
        """기본 전략 설정 테스트."""
        composite = CompositeQueryStrategy()
        names = composite.get_strategy_names()

        assert "single_hop" in names
        assert "multi_hop" in names
        assert "comparison" in names

    def test_custom_strategies(self) -> None:
        """커스텀 전략 설정 테스트."""
        strategies = [SingleHopStrategy()]
        composite = CompositeQueryStrategy(strategies=strategies)

        assert len(composite.get_strategy_names()) == 1
        assert "single_hop" in composite.get_strategy_names()

    def test_generate_queries(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """복합 전략 쿼리 생성 테스트."""
        composite = CompositeQueryStrategy()
        entity = populated_kg.get_entity("삼성생명")
        assert entity is not None

        queries = composite.generate_queries(populated_kg, entity)

        assert len(queries) >= 1
        query_types = {q.query_type for q in queries}
        # 최소 하나의 쿼리 타입이 생성되어야 함
        assert len(query_types) >= 1

    def test_generate_queries_for_all_entities(self, populated_kg: NetworkXKnowledgeGraph) -> None:
        """모든 엔티티에 대한 쿼리 생성 테스트."""
        composite = CompositeQueryStrategy()
        queries = composite.generate_queries_for_all_entities(populated_kg, max_per_entity=2)

        assert len(queries) >= 1

    def test_add_strategy(self) -> None:
        """전략 추가 테스트."""
        composite = CompositeQueryStrategy(strategies=[])
        composite.add_strategy(SingleHopStrategy())

        assert len(composite.get_strategy_names()) == 1


class TestGeneratedQuery:
    """GeneratedQuery 데이터클래스 테스트."""

    def test_required_fields(self) -> None:
        """필수 필드 테스트."""
        query = GeneratedQuery(
            query="테스트 질문",
            query_type="single_hop",
            entities=["entity1"],
        )

        assert query.query == "테스트 질문"
        assert query.query_type == "single_hop"
        assert query.entities == ["entity1"]

    def test_optional_fields(self) -> None:
        """옵션 필드 테스트."""
        query = GeneratedQuery(
            query="테스트 질문",
            query_type="single_hop",
            entities=["entity1"],
            expected_answer_hint="힌트",
            difficulty=2,
            metadata={"key": "value"},
        )

        assert query.expected_answer_hint == "힌트"
        assert query.difficulty == 2
        assert query.metadata == {"key": "value"}

    def test_default_values(self) -> None:
        """기본값 테스트."""
        query = GeneratedQuery(
            query="테스트 질문",
            query_type="single_hop",
            entities=["entity1"],
        )

        assert query.expected_answer_hint is None
        assert query.difficulty == 1
        assert query.metadata is None
