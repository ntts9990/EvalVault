"""Query generation strategies for Knowledge Graph-based testset generation.

This module provides different strategies for generating evaluation queries
from the knowledge graph structure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from evalvault.adapters.outbound.kg.networkx_adapter import NetworkXKnowledgeGraph
    from evalvault.domain.entities.kg import EntityModel


@dataclass
class GeneratedQuery:
    """생성된 쿼리 정보.

    Attributes:
        query: 생성된 질문 텍스트
        query_type: 쿼리 유형 (single_hop, multi_hop, comparison)
        entities: 관련 엔티티 이름 리스트
        expected_answer_hint: 예상 답변에 대한 힌트
        difficulty: 난이도 (1: 쉬움, 2: 보통, 3: 어려움)
        metadata: 추가 메타데이터
    """

    query: str
    query_type: str
    entities: list[str]
    expected_answer_hint: str | None = None
    difficulty: int = 1
    metadata: dict | None = None


@runtime_checkable
class QueryStrategy(Protocol):
    """쿼리 생성 전략 프로토콜.

    Knowledge Graph에서 다양한 유형의 평가 쿼리를 생성하기 위한
    전략 패턴 인터페이스입니다.
    """

    def generate_queries(
        self, kg: NetworkXKnowledgeGraph, entity: EntityModel
    ) -> list[GeneratedQuery]:
        """엔티티 기반 쿼리 생성.

        Args:
            kg: 지식 그래프 인스턴스
            entity: 시작 엔티티

        Returns:
            생성된 쿼리 리스트
        """
        ...

    def get_strategy_name(self) -> str:
        """전략 이름 반환."""
        ...


class BaseQueryStrategy(ABC):
    """쿼리 생성 전략 기본 클래스."""

    @abstractmethod
    def generate_queries(
        self, kg: NetworkXKnowledgeGraph, entity: EntityModel
    ) -> list[GeneratedQuery]:
        """엔티티 기반 쿼리 생성."""
        ...

    @abstractmethod
    def get_strategy_name(self) -> str:
        """전략 이름 반환."""
        ...

    def _get_question_template(self, entity_type: str, relation_type: str | None = None) -> str:
        """엔티티 타입과 관계 타입에 따른 질문 템플릿 반환."""
        templates = {
            ("organization", None): "{entity}에 대해 설명해주세요.",
            ("organization", "provides"): "{entity}에서 제공하는 보험 상품은 무엇인가요?",
            ("product", None): "{entity}에 대해 설명해주세요.",
            ("product", "has_coverage"): "{entity}의 보장 내용은 무엇인가요?",
            ("product", "has_period"): "{entity}의 보험 기간은 어떻게 되나요?",
            ("coverage", None): "{entity}에 대해 설명해주세요.",
            ("coverage", "has_amount"): "{entity}의 지급 금액은 얼마인가요?",
            ("money", None): "{entity}에 해당하는 보장은 무엇인가요?",
            ("period", None): "보험 기간 {entity}과 관련된 내용은 무엇인가요?",
        }
        return templates.get((entity_type, relation_type), "{entity}에 대해 설명해주세요.")


class SingleHopStrategy(BaseQueryStrategy):
    """단일 관계 기반 쿼리 생성 전략.

    엔티티와 직접 연결된 관계(1-hop)를 기반으로 쿼리를 생성합니다.
    가장 단순한 형태의 질문을 생성하며, RAG 시스템의 기본적인
    정보 검색 능력을 평가하는 데 적합합니다.
    """

    def get_strategy_name(self) -> str:
        """전략 이름 반환."""
        return "single_hop"

    def generate_queries(
        self, kg: NetworkXKnowledgeGraph, entity: EntityModel
    ) -> list[GeneratedQuery]:
        """단일 홉 쿼리 생성.

        Args:
            kg: 지식 그래프
            entity: 시작 엔티티

        Returns:
            생성된 쿼리 리스트
        """
        queries: list[GeneratedQuery] = []

        # 나가는 관계 기반 쿼리
        outgoing = kg.get_outgoing_relations(entity.name)
        for relation in outgoing:
            template = self._get_question_template(entity.entity_type, relation.relation_type)
            query_text = template.format(entity=entity.name)

            target_entity = kg.get_entity(relation.target)
            answer_hint = None
            if target_entity:
                answer_hint = f"{relation.target} ({target_entity.entity_type})"

            queries.append(
                GeneratedQuery(
                    query=query_text,
                    query_type="single_hop",
                    entities=[entity.name, relation.target],
                    expected_answer_hint=answer_hint,
                    difficulty=1,
                    metadata={
                        "relation_type": relation.relation_type,
                        "confidence": relation.confidence,
                        "direction": "outgoing",
                    },
                )
            )

        # 들어오는 관계 기반 쿼리 (역방향 질문)
        incoming = kg.get_incoming_relations(entity.name)
        for relation in incoming:
            query_text = self._generate_reverse_question(
                entity, relation.source, relation.relation_type
            )
            if query_text:
                source_entity = kg.get_entity(relation.source)
                answer_hint = None
                if source_entity:
                    answer_hint = f"{relation.source} ({source_entity.entity_type})"

                queries.append(
                    GeneratedQuery(
                        query=query_text,
                        query_type="single_hop",
                        entities=[relation.source, entity.name],
                        expected_answer_hint=answer_hint,
                        difficulty=1,
                        metadata={
                            "relation_type": relation.relation_type,
                            "confidence": relation.confidence,
                            "direction": "incoming",
                        },
                    )
                )

        # 관계가 없는 경우 기본 쿼리
        if not queries:
            template = self._get_question_template(entity.entity_type)
            queries.append(
                GeneratedQuery(
                    query=template.format(entity=entity.name),
                    query_type="single_hop",
                    entities=[entity.name],
                    difficulty=1,
                    metadata={"no_relations": True},
                )
            )

        return queries

    def _generate_reverse_question(
        self, target_entity: EntityModel, source_name: str, relation_type: str
    ) -> str | None:
        """역방향 관계 기반 질문 생성."""
        reverse_templates = {
            ("coverage", "has_coverage"): "{entity}을 보장하는 보험 상품은 무엇인가요?",
            ("money", "has_amount"): "{entity}을 지급하는 보장 항목은 무엇인가요?",
            ("period", "has_period"): "{entity} 기간과 관련된 보험 상품은 무엇인가요?",
            ("product", "provides"): "{entity}을 제공하는 보험사는 어디인가요?",
        }

        template = reverse_templates.get((target_entity.entity_type, relation_type))
        if template:
            return template.format(entity=target_entity.name)
        return None


class MultiHopStrategy(BaseQueryStrategy):
    """다중 관계 기반 쿼리 생성 전략 (최대 2-hop).

    2개 이상의 관계를 거쳐야 답변할 수 있는 복합 질문을 생성합니다.
    RAG 시스템의 추론 능력과 다중 컨텍스트 통합 능력을 평가합니다.
    """

    def __init__(self, max_hops: int = 2):
        """초기화.

        Args:
            max_hops: 최대 홉 수 (기본값: 2)
        """
        self._max_hops = min(max_hops, 3)  # 최대 3홉으로 제한

    def get_strategy_name(self) -> str:
        """전략 이름 반환."""
        return "multi_hop"

    def generate_queries(
        self, kg: NetworkXKnowledgeGraph, entity: EntityModel
    ) -> list[GeneratedQuery]:
        """다중 홉 쿼리 생성.

        Args:
            kg: 지식 그래프
            entity: 시작 엔티티

        Returns:
            생성된 쿼리 리스트
        """
        queries: list[GeneratedQuery] = []

        # 2-hop 경로 탐색
        neighbors_1hop = kg.get_successors(entity.name)

        for neighbor in neighbors_1hop:
            neighbors_2hop = kg.get_successors(neighbor)
            for target in neighbors_2hop:
                if target != entity.name:  # 순환 방지
                    query = self._generate_2hop_query(kg, entity, neighbor, target)
                    if query:
                        queries.append(query)

        # 3-hop 경로 (max_hops가 3인 경우)
        if self._max_hops >= 3:
            for neighbor1 in neighbors_1hop:
                neighbors_2hop = kg.get_successors(neighbor1)
                for neighbor2 in neighbors_2hop:
                    if neighbor2 == entity.name:
                        continue
                    neighbors_3hop = kg.get_successors(neighbor2)
                    for target in neighbors_3hop:
                        if target not in (entity.name, neighbor1):
                            query = self._generate_3hop_query(
                                kg, entity, neighbor1, neighbor2, target
                            )
                            if query:
                                queries.append(query)

        return queries

    def _generate_2hop_query(
        self,
        kg: NetworkXKnowledgeGraph,
        start: EntityModel,
        middle: str,
        end: str,
    ) -> GeneratedQuery | None:
        """2-hop 경로 기반 쿼리 생성."""
        middle_entity = kg.get_entity(middle)
        end_entity = kg.get_entity(end)

        if not middle_entity or not end_entity:
            return None

        # 관계 정보 추출
        relation1 = kg.get_relations(start.name, middle)
        relation2 = kg.get_relations(middle, end)

        if not relation1 or not relation2:
            return None

        # 질문 생성
        query_text = self._build_2hop_question(
            start, middle_entity, end_entity, relation1[0], relation2[0]
        )

        return GeneratedQuery(
            query=query_text,
            query_type="multi_hop",
            entities=[start.name, middle, end],
            expected_answer_hint=f"{end_entity.name} ({end_entity.entity_type})",
            difficulty=2,
            metadata={
                "hops": 2,
                "path": [start.name, middle, end],
                "relations": [relation1[0].relation_type, relation2[0].relation_type],
            },
        )

    def _generate_3hop_query(
        self,
        kg: NetworkXKnowledgeGraph,
        start: EntityModel,
        middle1: str,
        middle2: str,
        end: str,
    ) -> GeneratedQuery | None:
        """3-hop 경로 기반 쿼리 생성."""
        end_entity = kg.get_entity(end)
        if not end_entity:
            return None

        query_text = (
            f"{start.name}과 {end}의 관계를 설명해주세요. "
            f"중간에 {middle1}와 {middle2}가 어떻게 연결되어 있나요?"
        )

        return GeneratedQuery(
            query=query_text,
            query_type="multi_hop",
            entities=[start.name, middle1, middle2, end],
            expected_answer_hint=f"경로: {start.name} -> {middle1} -> {middle2} -> {end}",
            difficulty=3,
            metadata={
                "hops": 3,
                "path": [start.name, middle1, middle2, end],
            },
        )

    def _build_2hop_question(
        self,
        start: EntityModel,
        middle: EntityModel,
        end: EntityModel,
        rel1: object,
        rel2: object,
    ) -> str:
        """2-hop 관계 기반 질문 문장 구성."""
        # 엔티티 타입 조합에 따른 질문 템플릿
        type_combo = (start.entity_type, middle.entity_type, end.entity_type)

        templates = {
            ("organization", "product", "coverage"): (
                f"{start.name}의 {middle.name}에서 제공하는 보장 내용은 무엇인가요?"
            ),
            ("organization", "product", "money"): (
                f"{start.name}의 {middle.name}에서 보장하는 금액은 얼마인가요?"
            ),
            ("product", "coverage", "money"): (
                f"{start.name}의 {middle.name}에 대한 지급 금액은 얼마인가요?"
            ),
            ("organization", "product", "period"): (
                f"{start.name}의 {middle.name}의 보험 기간은 어떻게 되나요?"
            ),
        }

        if type_combo in templates:
            return templates[type_combo]

        # 기본 템플릿
        return f"{start.name}에서 {middle.name}를 통해 연결된 {end.name}에 대해 설명해주세요."


class ComparisonStrategy(BaseQueryStrategy):
    """엔티티 비교 쿼리 생성 전략.

    같은 타입의 엔티티들을 비교하는 질문을 생성합니다.
    RAG 시스템의 정보 통합 및 비교 분석 능력을 평가합니다.
    """

    def __init__(self, min_entities_for_comparison: int = 2):
        """초기화.

        Args:
            min_entities_for_comparison: 비교에 필요한 최소 엔티티 수
        """
        self._min_entities = min_entities_for_comparison

    def get_strategy_name(self) -> str:
        """전략 이름 반환."""
        return "comparison"

    def generate_queries(
        self, kg: NetworkXKnowledgeGraph, entity: EntityModel
    ) -> list[GeneratedQuery]:
        """비교 쿼리 생성.

        Args:
            kg: 지식 그래프
            entity: 비교 대상 엔티티

        Returns:
            생성된 쿼리 리스트
        """
        queries: list[GeneratedQuery] = []

        # 같은 타입의 다른 엔티티 찾기
        same_type_entities = kg.get_entities_by_type(entity.entity_type)

        # 비교 가능한 엔티티 필터링 (자기 자신 제외)
        comparable = [e for e in same_type_entities if e.name != entity.name]

        if not comparable:
            return queries

        # 각 비교 대상에 대해 쿼리 생성
        for other in comparable[:3]:  # 최대 3개까지만 비교
            query = self._generate_comparison_query(entity, other)
            queries.append(query)

        # 다중 비교 쿼리 (3개 이상인 경우)
        if len(comparable) >= 2:
            multi_query = self._generate_multi_comparison_query(entity, comparable[:2])
            queries.append(multi_query)

        return queries

    def _generate_comparison_query(
        self, entity1: EntityModel, entity2: EntityModel
    ) -> GeneratedQuery:
        """두 엔티티 비교 쿼리 생성."""
        query_templates = {
            "organization": f"{entity1.name}과 {entity2.name}의 보험 상품을 비교해주세요.",
            "product": f"{entity1.name}과 {entity2.name}의 차이점은 무엇인가요?",
            "coverage": f"{entity1.name}과 {entity2.name}의 보장 내용을 비교해주세요.",
            "money": f"{entity1.name}과 {entity2.name}의 금액 차이는 얼마인가요?",
            "period": f"{entity1.name}과 {entity2.name}의 기간 차이는 어떻게 되나요?",
        }

        query_text = query_templates.get(
            entity1.entity_type,
            f"{entity1.name}과 {entity2.name}을 비교해주세요.",
        )

        return GeneratedQuery(
            query=query_text,
            query_type="comparison",
            entities=[entity1.name, entity2.name],
            expected_answer_hint=f"{entity1.entity_type} 비교",
            difficulty=2,
            metadata={
                "entity_type": entity1.entity_type,
                "comparison_entities": [entity1.name, entity2.name],
            },
        )

    def _generate_multi_comparison_query(
        self, entity: EntityModel, others: list[EntityModel]
    ) -> GeneratedQuery:
        """다중 엔티티 비교 쿼리 생성."""
        all_names = [entity.name] + [e.name for e in others]
        names_str = ", ".join(all_names[:-1]) + f" 및 {all_names[-1]}"

        query_templates = {
            "organization": f"{names_str}의 주요 보험 상품들을 비교 분석해주세요.",
            "product": f"{names_str}의 장단점을 비교해주세요.",
            "coverage": f"{names_str}의 보장 범위를 비교해주세요.",
        }

        query_text = query_templates.get(
            entity.entity_type,
            f"{names_str}을 종합적으로 비교해주세요.",
        )

        return GeneratedQuery(
            query=query_text,
            query_type="comparison",
            entities=all_names,
            expected_answer_hint=f"다중 {entity.entity_type} 비교",
            difficulty=3,
            metadata={
                "entity_type": entity.entity_type,
                "comparison_count": len(all_names),
            },
        )


class CompositeQueryStrategy:
    """복합 쿼리 생성 전략.

    여러 전략을 조합하여 다양한 유형의 쿼리를 생성합니다.
    """

    def __init__(self, strategies: list[QueryStrategy] | None = None):
        """초기화.

        Args:
            strategies: 사용할 전략 리스트 (기본값: 모든 전략)
        """
        if strategies is None:
            strategies = [
                SingleHopStrategy(),
                MultiHopStrategy(),
                ComparisonStrategy(),
            ]
        self._strategies = strategies

    def generate_queries(
        self, kg: NetworkXKnowledgeGraph, entity: EntityModel
    ) -> list[GeneratedQuery]:
        """모든 전략을 사용하여 쿼리 생성.

        Args:
            kg: 지식 그래프
            entity: 시작 엔티티

        Returns:
            생성된 쿼리 리스트
        """
        all_queries: list[GeneratedQuery] = []

        for strategy in self._strategies:
            queries = strategy.generate_queries(kg, entity)
            all_queries.extend(queries)

        return all_queries

    def generate_queries_for_all_entities(
        self, kg: NetworkXKnowledgeGraph, max_per_entity: int = 5
    ) -> list[GeneratedQuery]:
        """모든 엔티티에 대해 쿼리 생성.

        Args:
            kg: 지식 그래프
            max_per_entity: 엔티티당 최대 쿼리 수

        Returns:
            생성된 쿼리 리스트
        """
        all_queries: list[GeneratedQuery] = []

        for entity in kg.get_all_entities():
            entity_queries = self.generate_queries(kg, entity)
            all_queries.extend(entity_queries[:max_per_entity])

        return all_queries

    def add_strategy(self, strategy: QueryStrategy) -> None:
        """전략 추가."""
        self._strategies.append(strategy)

    def get_strategy_names(self) -> list[str]:
        """사용 중인 전략 이름 리스트 반환."""
        return [s.get_strategy_name() for s in self._strategies]
