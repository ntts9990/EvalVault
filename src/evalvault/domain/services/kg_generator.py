"""Knowledge graph-based testset generation."""

import random
from collections import defaultdict
from datetime import datetime
from uuid import uuid4

import networkx as nx

from evalvault.domain.entities import Dataset, EntityModel, RelationModel, TestCase
from evalvault.domain.services.entity_extractor import (
    Entity as ExtractedEntity,
)
from evalvault.domain.services.entity_extractor import (
    EntityExtractor,
)
from evalvault.domain.services.entity_extractor import (
    Relation as ExtractedRelation,
)
from evalvault.ports.outbound.relation_augmenter_port import RelationAugmenterPort


class KnowledgeGraph:
    """지식 그래프 자료구조.

    엔티티를 노드로, 관계를 엣지로 표현하는 그래프.
    """

    def __init__(self):
        """Initialize knowledge graph."""
        self._graph = nx.MultiDiGraph()
        self._entity_metadata: dict[str, EntityModel] = {}

    def add_entity(self, entity: EntityModel) -> None:
        """그래프에 엔티티 추가.

        Args:
            entity: 추가할 엔티티
        """
        attributes = entity.to_node_attributes()
        if self._graph.has_node(entity.name):
            self._graph.nodes[entity.name].update(attributes)
        else:
            self._graph.add_node(entity.name, **attributes)
        self._entity_metadata[entity.name] = entity

    def add_relation(self, relation: RelationModel) -> None:
        """그래프에 관계 추가.

        Args:
            relation: 추가할 관계
        """
        attrs = relation.to_edge_attributes()
        attrs["model"] = relation
        self._graph.add_edge(relation.source, relation.target, **attrs)

    def has_entity(self, name: str) -> bool:
        """엔티티 존재 여부 확인.

        Args:
            name: 엔티티 이름

        Returns:
            존재 여부
        """
        return self._graph.has_node(name)

    def has_relation(self, source: str, target: str) -> bool:
        """관계 존재 여부 확인.

        Args:
            source: 출발 엔티티
            target: 도착 엔티티

        Returns:
            관계 존재 여부
        """
        return self._graph.has_edge(source, target)

    def get_entity(self, name: str) -> EntityModel | None:
        """엔티티 조회.

        Args:
            name: 엔티티 이름

        Returns:
            엔티티 객체 또는 None
        """
        return self._entity_metadata.get(name)

    def get_neighbors(self, name: str) -> list[str]:
        """노드의 이웃 노드 조회 (나가는 엣지).

        Args:
            name: 엔티티 이름

        Returns:
            이웃 노드 이름 리스트
        """
        if not self._graph.has_node(name):
            return []
        return list(self._graph.successors(name))

    def get_relations_for_entity(self, name: str) -> list[RelationModel]:
        """엔티티와 관련된 모든 관계 조회.

        Args:
            name: 엔티티 이름

        Returns:
            관계 리스트
        """
        if not self._graph.has_node(name):
            return []

        relations: list[RelationModel] = []

        for _, target, data in self._graph.out_edges(name, data=True):
            relations.append(self._relation_from_edge(name, target, data))

        for source, _, data in self._graph.in_edges(name, data=True):
            relations.append(self._relation_from_edge(source, name, data))

        return relations

    def get_node_count(self) -> int:
        """노드 개수 조회.

        Returns:
            노드 개수
        """
        return self._graph.number_of_nodes()

    def get_edge_count(self) -> int:
        """엣지 개수 조회.

        Returns:
            엣지 개수
        """
        return self._graph.number_of_edges()

    def get_all_entities(self) -> list[EntityModel]:
        """모든 엔티티 조회.

        Returns:
            엔티티 리스트
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

    def get_isolated_entities(self) -> list[EntityModel]:
        """엣지가 연결되지 않은 엔티티 목록."""
        isolated = []
        for node in self._graph.nodes():
            if self._graph.degree(node) == 0:
                entity = self._entity_metadata.get(node)
                if entity:
                    isolated.append(entity)
        return isolated

    def get_sample_entities(self, limit: int = 5) -> list[dict]:
        """엔티티 샘플을 직렬화."""
        samples = []
        for entity in list(self._entity_metadata.values())[:limit]:
            samples.append(
                {
                    "name": entity.name,
                    "entity_type": entity.entity_type,
                    "provenance": entity.provenance,
                    "confidence": entity.confidence,
                }
            )
        return samples

    def get_sample_relations(self, limit: int = 5) -> list[dict]:
        """관계 샘플 직렬화."""
        samples = []
        for source, target, data in list(self._graph.edges(data=True))[:limit]:
            relation = self._relation_from_edge(source, target, data)
            samples.append(
                {
                    "source": relation.source,
                    "target": relation.target,
                    "relation_type": relation.relation_type,
                    "provenance": relation.provenance,
                    "confidence": relation.confidence,
                }
            )
        return samples

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


class KnowledgeGraphGenerator:
    """지식 그래프 기반 테스트셋 생성기.

    문서에서 엔티티와 관계를 추출하여 지식 그래프를 구축하고,
    그래프를 탐색하여 다양한 유형의 질문을 생성합니다.
    """

    def __init__(
        self,
        relation_augmenter: RelationAugmenterPort | None = None,
        low_confidence_threshold: float = 0.6,
    ):
        """Initialize knowledge graph generator."""
        self._graph = KnowledgeGraph()
        self._extractor = EntityExtractor()
        self._document_chunks: dict[str, str] = {}  # entity_name -> source_text
        self._build_metrics: dict[str, int] = {
            "documents_processed": 0,
            "entities_processed": 0,
            "entities_added": 0,
            "relations_added": 0,
        }
        self._relation_augmenter = relation_augmenter
        self._low_confidence_threshold = low_confidence_threshold

    def build_graph(self, documents: list[str]) -> None:
        """문서에서 지식 그래프 구축.

        Args:
            documents: 문서 리스트
        """
        self._build_metrics = {
            "documents_processed": len(documents),
            "entities_processed": 0,
            "entities_added": 0,
            "relations_added": 0,
        }

        for doc_index, doc in enumerate(documents):
            doc_id = f"doc-{doc_index}"
            # Extract entities from document
            entities = self._extractor.extract_entities(doc)
            self._build_metrics["entities_processed"] += len(entities)

            # Add entities to graph
            for entity in entities:
                entity_model = self._to_entity_model(entity, doc_id)
                if not self._graph.has_entity(entity_model.name):
                    self._graph.add_entity(entity_model)
                    self._document_chunks[entity_model.name] = doc
                    self._build_metrics["entities_added"] += 1

            # Extract and add relations
            relations = self._extractor.extract_relations(doc, entities)
            relations = self._maybe_augment_relations(doc, entities, relations)
            for relation in relations:
                relation_model = self._to_relation_model(relation)
                if not (
                    self._graph.has_entity(relation_model.source)
                    and self._graph.has_entity(relation_model.target)
                ):
                    continue
                self._graph.add_relation(relation_model)
                self._build_metrics["relations_added"] += 1

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
            "build_metrics": self._build_metrics.copy(),
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
            "build_metrics": self._build_metrics.copy(),
            "relation_types": self._get_relation_type_counts(),
            "isolated_entities": [e.name for e in self._graph.get_isolated_entities()],
            "sample_entities": self._graph.get_sample_entities(),
            "sample_relations": self._graph.get_sample_relations(),
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

    def _generate_simple_question(self, entity: EntityModel) -> tuple[str, str]:
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
                products = [r.target for r in relations if r.relation_type == "provides"]
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

    def _generate_comparison_question(self, e1: EntityModel, e2: EntityModel) -> tuple[str, str]:
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

    def _get_relation_type_counts(self) -> dict[str, int]:
        """관계 타입별 개수."""
        counts = defaultdict(int)
        for entity in self._graph.get_all_entities():
            relations = self._graph.get_relations_for_entity(entity.name)
            for relation in relations:
                if relation.source == entity.name:
                    counts[relation.relation_type] += 1
        return dict(counts)

    @staticmethod
    def _to_entity_model(entity: ExtractedEntity, document_id: str) -> EntityModel:
        """추출된 엔티티를 정규화."""
        return EntityModel(
            name=entity.name,
            entity_type=entity.entity_type,
            attributes=entity.attributes,
            provenance=entity.provenance,
            confidence=entity.confidence,
            source_document_id=document_id,
        )

    @staticmethod
    def _to_relation_model(relation: ExtractedRelation) -> RelationModel:
        """추출된 관계를 정규화."""
        return RelationModel(
            source=relation.source,
            target=relation.target,
            relation_type=relation.relation_type,
            provenance=relation.provenance,
            confidence=relation.confidence,
            attributes={"evidence": relation.evidence} if relation.evidence else {},
        )

    def get_build_metrics(self) -> dict[str, int]:
        """그래프 구축 시 수집한 기본 통계."""
        return self._build_metrics.copy()

    def _maybe_augment_relations(
        self,
        document_text: str,
        entities: list[ExtractedEntity],
        relations: list[ExtractedRelation],
    ) -> list[ExtractedRelation]:
        """LLM 보강기로 저신뢰 관계 보완."""
        deduped = self._deduplicate_relations(relations)
        if not self._relation_augmenter:
            return deduped

        low_conf_relations = [
            relation for relation in deduped if relation.confidence < self._low_confidence_threshold
        ]
        if not low_conf_relations:
            return deduped

        augmented = self._relation_augmenter.augment_relations(
            document_text=document_text,
            entities=entities,
            low_confidence_relations=low_conf_relations,
        )
        if not augmented:
            return deduped

        return self._deduplicate_relations(deduped + augmented)

    @staticmethod
    def _deduplicate_relations(relations: list[ExtractedRelation]) -> list[ExtractedRelation]:
        """중복 관계 제거 (높은 confidence 우선)."""
        best: dict[tuple[str, str, str], ExtractedRelation] = {}
        for relation in relations:
            key = (relation.source, relation.target, relation.relation_type)
            current = best.get(key)
            if not current or relation.confidence > current.confidence:
                best[key] = relation
        return list(best.values())
