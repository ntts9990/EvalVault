"""Knowledge graph-based testset generation."""

import random
from collections import defaultdict
from datetime import datetime
from uuid import uuid4

from evalvault.domain.entities import Dataset, TestCase
from evalvault.domain.services.entity_extractor import (
    Entity,
    EntityExtractor,
    Relation,
)


class KnowledgeGraph:
    """지식 그래프 자료구조.

    엔티티를 노드로, 관계를 엣지로 표현하는 그래프.
    """

    def __init__(self):
        """Initialize knowledge graph."""
        self._nodes: dict[str, Entity] = {}  # entity_name -> Entity
        self._edges: dict[str, list[tuple[str, str]]] = defaultdict(
            list
        )  # source -> [(target, relation_type)]
        self._reverse_edges: dict[str, list[tuple[str, str]]] = defaultdict(
            list
        )  # target -> [(source, relation_type)]

    def add_entity(self, entity: Entity) -> None:
        """그래프에 엔티티 추가.

        Args:
            entity: 추가할 엔티티
        """
        self._nodes[entity.name] = entity

    def add_relation(self, relation: Relation) -> None:
        """그래프에 관계 추가.

        Args:
            relation: 추가할 관계
        """
        self._edges[relation.source].append((relation.target, relation.relation_type))
        self._reverse_edges[relation.target].append(
            (relation.source, relation.relation_type)
        )

    def has_entity(self, name: str) -> bool:
        """엔티티 존재 여부 확인.

        Args:
            name: 엔티티 이름

        Returns:
            존재 여부
        """
        return name in self._nodes

    def has_relation(self, source: str, target: str) -> bool:
        """관계 존재 여부 확인.

        Args:
            source: 출발 엔티티
            target: 도착 엔티티

        Returns:
            관계 존재 여부
        """
        if source not in self._edges:
            return False
        return any(t == target for t, _ in self._edges[source])

    def get_entity(self, name: str) -> Entity | None:
        """엔티티 조회.

        Args:
            name: 엔티티 이름

        Returns:
            엔티티 객체 또는 None
        """
        return self._nodes.get(name)

    def get_neighbors(self, name: str) -> list[str]:
        """노드의 이웃 노드 조회 (나가는 엣지).

        Args:
            name: 엔티티 이름

        Returns:
            이웃 노드 이름 리스트
        """
        if name not in self._edges:
            return []
        return [target for target, _ in self._edges[name]]

    def get_relations_for_entity(self, name: str) -> list[Relation]:
        """엔티티와 관련된 모든 관계 조회.

        Args:
            name: 엔티티 이름

        Returns:
            관계 리스트
        """
        relations = []

        # Outgoing relations
        if name in self._edges:
            for target, rel_type in self._edges[name]:
                relations.append(Relation(source=name, target=target, relation_type=rel_type))

        # Incoming relations
        if name in self._reverse_edges:
            for source, rel_type in self._reverse_edges[name]:
                relations.append(Relation(source=source, target=name, relation_type=rel_type))

        return relations

    def get_node_count(self) -> int:
        """노드 개수 조회.

        Returns:
            노드 개수
        """
        return len(self._nodes)

    def get_edge_count(self) -> int:
        """엣지 개수 조회.

        Returns:
            엣지 개수
        """
        total = 0
        for edges in self._edges.values():
            total += len(edges)
        return total

    def get_all_entities(self) -> list[Entity]:
        """모든 엔티티 조회.

        Returns:
            엔티티 리스트
        """
        return list(self._nodes.values())

    def get_entities_by_type(self, entity_type: str) -> list[Entity]:
        """특정 타입의 엔티티 조회.

        Args:
            entity_type: 엔티티 타입

        Returns:
            해당 타입의 엔티티 리스트
        """
        return [e for e in self._nodes.values() if e.entity_type == entity_type]


class KnowledgeGraphGenerator:
    """지식 그래프 기반 테스트셋 생성기.

    문서에서 엔티티와 관계를 추출하여 지식 그래프를 구축하고,
    그래프를 탐색하여 다양한 유형의 질문을 생성합니다.
    """

    def __init__(self):
        """Initialize knowledge graph generator."""
        self._graph = KnowledgeGraph()
        self._extractor = EntityExtractor()
        self._document_chunks: dict[str, str] = {}  # entity_name -> source_text

    def build_graph(self, documents: list[str]) -> None:
        """문서에서 지식 그래프 구축.

        Args:
            documents: 문서 리스트
        """
        for doc in documents:
            # Extract entities from document
            entities = self._extractor.extract_entities(doc)

            # Add entities to graph
            for entity in entities:
                if not self._graph.has_entity(entity.name):
                    self._graph.add_entity(entity)
                    self._document_chunks[entity.name] = doc

            # Extract and add relations
            relations = self._extractor.extract_relations(doc, entities)
            for relation in relations:
                self._graph.add_relation(relation)

    def get_graph(self) -> KnowledgeGraph:
        """지식 그래프 조회.

        Returns:
            KnowledgeGraph 객체
        """
        return self._graph

    def generate_questions(self, num_questions: int = 10) -> list[TestCase]:
        """그래프 순회를 통한 질문 생성.

        Args:
            num_questions: 생성할 질문 개수

        Returns:
            생성된 TestCase 리스트
        """
        if self._graph.get_node_count() == 0:
            return []

        test_cases = []
        all_entities = self._graph.get_all_entities()

        # Shuffle for variety
        random.shuffle(all_entities)

        for entity in all_entities[:num_questions]:
            question, context = self._generate_simple_question(entity)
            if question:
                test_case = TestCase(
                    id=f"kg-{uuid4().hex[:8]}",
                    question=question,
                    answer="",  # To be filled by RAG system
                    contexts=[context],
                    ground_truth=None,
                    metadata={
                        "generated": True,
                        "generator": "knowledge_graph",
                        "entity": entity.name,
                        "entity_type": entity.entity_type,
                    },
                )
                test_cases.append(test_case)

                if len(test_cases) >= num_questions:
                    break

        return test_cases

    def generate_multi_hop_questions(self, hops: int = 2) -> list[TestCase]:
        """다중 홉 추론 질문 생성.

        Args:
            hops: 홉 개수 (엔티티 간 거리)

        Returns:
            생성된 TestCase 리스트
        """
        if self._graph.get_node_count() < hops + 1:
            return []

        test_cases = []
        all_entities = self._graph.get_all_entities()
        random.shuffle(all_entities)

        # Try to find multi-hop paths
        for start_entity in all_entities:
            path = self._find_path(start_entity.name, hops)
            if path and len(path) >= hops + 1:
                question, context = self._generate_multi_hop_question(path)
                if question:
                    test_case = TestCase(
                        id=f"kg-mh-{uuid4().hex[:8]}",
                        question=question,
                        answer="",
                        contexts=[context],
                        ground_truth=None,
                        metadata={
                            "generated": True,
                            "generator": "knowledge_graph_multi_hop",
                            "path": path,
                            "hops": hops,
                        },
                    )
                    test_cases.append(test_case)

                    # Limit to reasonable number
                    if len(test_cases) >= 5:
                        break

        return test_cases

    def generate_dataset(
        self,
        num_questions: int = 10,
        name: str = "kg-testset",
        version: str = "1.0.0",
    ) -> Dataset:
        """완전한 Dataset 생성.

        Args:
            num_questions: 생성할 질문 개수
            name: 데이터셋 이름
            version: 데이터셋 버전

        Returns:
            생성된 Dataset
        """
        test_cases = self.generate_questions(num_questions)

        metadata = {
            "generated_at": datetime.now().isoformat(),
            "generator_type": "knowledge_graph",
            "num_entities": self._graph.get_node_count(),
            "num_relations": self._graph.get_edge_count(),
        }

        return Dataset(
            name=name,
            version=version,
            test_cases=test_cases,
            metadata=metadata,
        )

    def get_statistics(self) -> dict:
        """그래프 통계 정보 조회.

        Returns:
            통계 정보 딕셔너리
        """
        return {
            "num_entities": self._graph.get_node_count(),
            "num_relations": self._graph.get_edge_count(),
            "entity_types": self._get_entity_type_counts(),
        }

    def generate_questions_by_type(
        self, entity_type: str, num_questions: int = 5
    ) -> list[TestCase]:
        """특정 엔티티 타입에 대한 질문 생성.

        Args:
            entity_type: 엔티티 타입
            num_questions: 생성할 질문 개수

        Returns:
            생성된 TestCase 리스트
        """
        entities = self._graph.get_entities_by_type(entity_type)
        if not entities:
            return []

        random.shuffle(entities)
        test_cases = []

        for entity in entities[:num_questions]:
            question, context = self._generate_simple_question(entity)
            if question:
                test_case = TestCase(
                    id=f"kg-type-{uuid4().hex[:8]}",
                    question=question,
                    answer="",
                    contexts=[context],
                    ground_truth=None,
                    metadata={
                        "generated": True,
                        "generator": "knowledge_graph_by_type",
                        "entity": entity.name,
                        "entity_type": entity.entity_type,
                    },
                )
                test_cases.append(test_case)

        return test_cases

    def generate_comparison_questions(self, num_questions: int = 5) -> list[TestCase]:
        """비교 질문 생성.

        같은 타입의 엔티티 간 비교 질문을 생성합니다.

        Args:
            num_questions: 생성할 질문 개수

        Returns:
            생성된 TestCase 리스트
        """
        test_cases = []

        # Get entities by type
        type_counts = self._get_entity_type_counts()

        # Find types with multiple entities
        for entity_type, count in type_counts.items():
            if count >= 2:
                entities = self._graph.get_entities_by_type(entity_type)
                # Generate comparison questions
                for i in range(min(num_questions, len(entities) - 1)):
                    e1, e2 = entities[i], entities[i + 1]
                    question, context = self._generate_comparison_question(e1, e2)
                    if question:
                        test_case = TestCase(
                            id=f"kg-comp-{uuid4().hex[:8]}",
                            question=question,
                            answer="",
                            contexts=[context],
                            ground_truth=None,
                            metadata={
                                "generated": True,
                                "generator": "knowledge_graph_comparison",
                                "entities": [e1.name, e2.name],
                            },
                        )
                        test_cases.append(test_case)

                        if len(test_cases) >= num_questions:
                            break

            if len(test_cases) >= num_questions:
                break

        return test_cases

    def _generate_simple_question(self, entity: Entity) -> tuple[str, str]:
        """단일 엔티티에 대한 질문 생성.

        Args:
            entity: 엔티티

        Returns:
            (질문, 컨텍스트) 튜플
        """
        # Get relations for this entity
        relations = self._graph.get_relations_for_entity(entity.name)
        context = self._document_chunks.get(entity.name, "")

        # Generate questions based on entity type and relations
        if entity.entity_type == "organization":
            if any(r.relation_type == "provides" for r in relations):
                products = [
                    r.target for r in relations if r.relation_type == "provides"
                ]
                if products:
                    question = f"{entity.name}에서 제공하는 보험 상품은 무엇인가요?"
                else:
                    question = f"{entity.name}의 주요 보험 상품에 대해 설명해주세요."
            else:
                question = f"{entity.name}에 대해 설명해주세요."

        elif entity.entity_type == "product":
            if any(r.relation_type == "has_coverage" for r in relations):
                question = f"{entity.name}의 보장 내용은 무엇인가요?"
            else:
                question = f"{entity.name}에 대해 설명해주세요."

        elif entity.entity_type == "coverage":
            if any(r.relation_type == "has_amount" for r in relations):
                question = f"{entity.name}의 지급 금액은 얼마인가요?"
            else:
                question = f"{entity.name}에 대해 설명해주세요."

        elif entity.entity_type == "money":
            question = f"{entity.name}에 해당하는 보장은 무엇인가요?"

        elif entity.entity_type == "period":
            question = f"보험 기간 {entity.name}과 관련된 내용은 무엇인가요?"

        else:
            question = f"{entity.name}에 대해 설명해주세요."

        return question, context

    def _generate_multi_hop_question(self, path: list[str]) -> tuple[str, str]:
        """다중 홉 경로에서 질문 생성.

        Args:
            path: 엔티티 이름 경로

        Returns:
            (질문, 컨텍스트) 튜플
        """
        if len(path) < 2:
            return "", ""

        # Combine contexts from all entities in path
        contexts = []
        for entity_name in path:
            if entity_name in self._document_chunks:
                contexts.append(self._document_chunks[entity_name])

        context = " ".join(contexts) if contexts else ""

        # Generate question based on path
        start_entity = self._graph.get_entity(path[0])
        end_entity = self._graph.get_entity(path[-1])

        if start_entity and end_entity:
            question = f"{start_entity.name}과 {end_entity.name}의 관계는 무엇인가요?"
        else:
            question = f"{path[0]}에서 {path[-1]}까지의 연결 관계를 설명해주세요."

        return question, context

    def _generate_comparison_question(
        self, e1: Entity, e2: Entity
    ) -> tuple[str, str]:
        """비교 질문 생성.

        Args:
            e1: 첫 번째 엔티티
            e2: 두 번째 엔티티

        Returns:
            (질문, 컨텍스트) 튜플
        """
        context1 = self._document_chunks.get(e1.name, "")
        context2 = self._document_chunks.get(e2.name, "")
        context = f"{context1} {context2}".strip()

        if e1.entity_type == "organization":
            question = f"{e1.name}과 {e2.name}의 보험 상품을 비교해주세요."
        elif e1.entity_type == "product":
            question = f"{e1.name}과 {e2.name}의 차이점은 무엇인가요?"
        elif e1.entity_type == "coverage":
            question = f"{e1.name}과 {e2.name}의 보장 내용을 비교해주세요."
        else:
            question = f"{e1.name}과 {e2.name}을 비교해주세요."

        return question, context

    def _find_path(self, start: str, hops: int) -> list[str]:
        """시작 노드에서 특정 홉 수만큼의 경로 찾기 (BFS).

        Args:
            start: 시작 노드
            hops: 찾을 홉 수

        Returns:
            경로 (노드 이름 리스트)
        """
        if not self._graph.has_entity(start):
            return []

        # BFS to find path of specific length
        queue = [(start, [start])]
        visited = {start}

        while queue:
            current, path = queue.pop(0)

            if len(path) == hops + 1:
                return path

            neighbors = self._graph.get_neighbors(current)
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return []

    def _get_entity_type_counts(self) -> dict[str, int]:
        """엔티티 타입별 개수 집계.

        Returns:
            타입별 개수 딕셔너리
        """
        counts = defaultdict(int)
        for entity in self._graph.get_all_entities():
            counts[entity.entity_type] += 1
        return dict(counts)
