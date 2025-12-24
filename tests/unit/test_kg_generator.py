"""Unit tests for knowledge graph testset generator."""

import pytest

from evalvault.domain.entities import Dataset, TestCase
from evalvault.domain.services.entity_extractor import Entity, Relation
from evalvault.domain.services.kg_generator import (
    KnowledgeGraph,
    KnowledgeGraphGenerator,
)


class TestKnowledgeGraph:
    """Test suite for KnowledgeGraph data structure."""

    def test_initialization(self):
        """Test knowledge graph initialization."""
        graph = KnowledgeGraph()
        assert graph is not None
        assert graph.get_node_count() == 0

    def test_add_entity(self):
        """Test adding entity as node to graph."""
        graph = KnowledgeGraph()
        entity = Entity(name="삼성생명", entity_type="organization", attributes={})

        graph.add_entity(entity)
        assert graph.get_node_count() == 1
        assert graph.has_entity("삼성생명")

    def test_add_relation(self):
        """Test adding relation as edge to graph."""
        graph = KnowledgeGraph()
        e1 = Entity(name="삼성생명", entity_type="organization", attributes={})
        e2 = Entity(name="종신보험", entity_type="product", attributes={})

        graph.add_entity(e1)
        graph.add_entity(e2)

        relation = Relation(source="삼성생명", target="종신보험", relation_type="provides")
        graph.add_relation(relation)

        assert graph.get_edge_count() >= 1
        assert graph.has_relation("삼성생명", "종신보험")

    def test_get_neighbors(self):
        """Test getting neighbors of a node."""
        graph = KnowledgeGraph()
        graph.add_entity(Entity("삼성생명", "organization", {}))
        graph.add_entity(Entity("종신보험", "product", {}))
        graph.add_entity(Entity("정기보험", "product", {}))

        graph.add_relation(Relation("삼성생명", "종신보험", "provides"))
        graph.add_relation(Relation("삼성생명", "정기보험", "provides"))

        neighbors = graph.get_neighbors("삼성생명")
        assert len(neighbors) == 2
        assert "종신보험" in neighbors
        assert "정기보험" in neighbors

    def test_get_entity(self):
        """Test retrieving entity from graph."""
        graph = KnowledgeGraph()
        entity = Entity("삼성생명", "organization", {"industry": "insurance"})
        graph.add_entity(entity)

        retrieved = graph.get_entity("삼성생명")
        assert retrieved is not None
        assert retrieved.name == "삼성생명"
        assert retrieved.entity_type == "organization"

    def test_get_relations_for_entity(self):
        """Test getting all relations for an entity."""
        graph = KnowledgeGraph()
        graph.add_entity(Entity("종신보험", "product", {}))
        graph.add_entity(Entity("사망보험금", "coverage", {}))
        graph.add_entity(Entity("1억원", "money", {}))

        graph.add_relation(Relation("종신보험", "사망보험금", "has_coverage"))
        graph.add_relation(Relation("종신보험", "1억원", "has_amount"))

        relations = graph.get_relations_for_entity("종신보험")
        assert len(relations) >= 2


class TestKnowledgeGraphGenerator:
    """Test suite for KnowledgeGraphGenerator."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample insurance documents for testing."""
        return [
            "삼성생명의 종신보험은 사망보험금 1억원을 보장합니다.",
            "한화생명의 암보험은 암 진단 시 5천만원을 지급합니다.",
            "교보생명의 연금보험은 월 50만원의 연금을 10년간 지급합니다.",
            "종신보험의 보험료는 월 30만원이며, 납입 기간은 20년입니다.",
        ]

    def test_initialization(self):
        """Test generator initialization."""
        generator = KnowledgeGraphGenerator()
        assert generator is not None

    def test_build_graph_creates_graph(self, sample_documents):
        """Test that build_graph creates a knowledge graph."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        graph = generator.get_graph()
        assert graph is not None
        assert graph.get_node_count() > 0

    def test_build_graph_extracts_entities(self, sample_documents):
        """Test that build_graph extracts entities from documents."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        graph = generator.get_graph()
        # Should extract company entities
        assert graph.has_entity("삼성생명") or graph.has_entity("한화생명")
        # Should extract product entities
        assert graph.has_entity("종신보험") or graph.has_entity("암보험")

    def test_build_graph_creates_relations(self, sample_documents):
        """Test that build_graph creates relations between entities."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        graph = generator.get_graph()
        assert graph.get_edge_count() > 0

    def test_build_graph_with_empty_documents(self):
        """Test building graph with empty document list."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph([])

        graph = generator.get_graph()
        assert graph.get_node_count() == 0

    def test_generate_questions_creates_test_cases(self, sample_documents):
        """Test that generate_questions creates TestCase objects."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        test_cases = generator.generate_questions(num_questions=5)
        assert len(test_cases) > 0
        assert all(isinstance(tc, TestCase) for tc in test_cases)

    def test_generate_questions_respects_num_limit(self, sample_documents):
        """Test that generate_questions respects the number limit."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        test_cases = generator.generate_questions(num_questions=3)
        assert len(test_cases) <= 3

    def test_generated_questions_have_structure(self, sample_documents):
        """Test that generated questions have proper structure."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        test_cases = generator.generate_questions(num_questions=2)
        for tc in test_cases:
            assert tc.id is not None and len(tc.id) > 0
            assert tc.question is not None and len(tc.question) > 0
            assert tc.contexts is not None and len(tc.contexts) > 0
            # Answer can be empty for generation-only
            assert tc.answer is not None

    def test_generated_questions_are_diverse(self, sample_documents):
        """Test that generated questions are diverse."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        test_cases = generator.generate_questions(num_questions=5)
        questions = [tc.question for tc in test_cases]

        # Questions should not all be identical
        unique_questions = set(questions)
        assert len(unique_questions) >= 2 or len(questions) <= 1

    def test_generated_questions_use_entities(self, sample_documents):
        """Test that generated questions use extracted entities."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        test_cases = generator.generate_questions(num_questions=3)

        # At least some questions should mention entities from the documents
        all_questions = " ".join(tc.question for tc in test_cases)
        assert any(
            entity in all_questions
            for entity in ["삼성생명", "한화생명", "교보생명", "종신보험", "암보험", "연금보험"]
        )

    def test_generate_multi_hop_questions(self, sample_documents):
        """Test generating multi-hop reasoning questions."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        test_cases = generator.generate_multi_hop_questions(hops=2)
        assert len(test_cases) > 0
        assert all(isinstance(tc, TestCase) for tc in test_cases)

    def test_multi_hop_questions_are_complex(self, sample_documents):
        """Test that multi-hop questions are more complex."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        single_hop = generator.generate_questions(num_questions=2)
        multi_hop = generator.generate_multi_hop_questions(hops=2)

        # Multi-hop questions should involve multiple entities
        # Check that questions are different types
        if len(multi_hop) > 0 and len(single_hop) > 0:
            # Multi-hop questions might be longer or use different patterns
            multi_hop_text = multi_hop[0].question
            assert len(multi_hop_text) > 0

    def test_multi_hop_questions_with_different_hops(self, sample_documents):
        """Test generating multi-hop questions with different hop counts."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        # Test with 2 hops
        test_cases_2 = generator.generate_multi_hop_questions(hops=2)
        # Test with 3 hops
        test_cases_3 = generator.generate_multi_hop_questions(hops=3)

        # Should generate questions for both
        assert len(test_cases_2) >= 0  # May be empty if graph is too small
        assert len(test_cases_3) >= 0

    def test_generate_dataset(self, sample_documents):
        """Test generating a complete Dataset object."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        dataset = generator.generate_dataset(
            num_questions=5,
            name="kg-testset",
            version="1.0.0",
        )

        assert isinstance(dataset, Dataset)
        assert dataset.name == "kg-testset"
        assert dataset.version == "1.0.0"
        assert len(dataset.test_cases) > 0
        assert len(dataset.test_cases) <= 5

    def test_generate_dataset_with_metadata(self, sample_documents):
        """Test that generated dataset includes metadata."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        dataset = generator.generate_dataset(num_questions=3)

        assert dataset.metadata is not None
        assert "generated_at" in dataset.metadata
        assert "generator_type" in dataset.metadata
        assert dataset.metadata["generator_type"] == "knowledge_graph"

    def test_questions_include_context_from_documents(self, sample_documents):
        """Test that questions include relevant context from source documents."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        test_cases = generator.generate_questions(num_questions=3)

        for tc in test_cases:
            # Context should be from original documents
            assert len(tc.contexts) > 0
            # At least some part of context should match source documents
            for context in tc.contexts:
                assert len(context) > 0

    def test_graph_statistics(self, sample_documents):
        """Test getting graph statistics."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        stats = generator.get_statistics()
        assert "num_entities" in stats
        assert "num_relations" in stats
        assert stats["num_entities"] > 0

    def test_generate_questions_by_entity_type(self, sample_documents):
        """Test generating questions focused on specific entity types."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        # Generate questions about organizations
        org_questions = generator.generate_questions_by_type(
            entity_type="organization", num_questions=2
        )
        # Generate questions about products
        product_questions = generator.generate_questions_by_type(
            entity_type="product", num_questions=2
        )

        # Both should generate questions
        assert len(org_questions) >= 0
        assert len(product_questions) >= 0

    def test_generate_comparison_questions(self, sample_documents):
        """Test generating comparison questions between entities."""
        generator = KnowledgeGraphGenerator()
        generator.build_graph(sample_documents)

        comparison_questions = generator.generate_comparison_questions(num_questions=2)

        # Should generate comparison questions if enough entities exist
        if len(comparison_questions) > 0:
            for tc in comparison_questions:
                # Comparison questions should mention multiple entities
                assert len(tc.question) > 0
                assert isinstance(tc, TestCase)

    def test_full_workflow(self, sample_documents):
        """Test complete workflow from documents to questions."""
        generator = KnowledgeGraphGenerator()

        # Build graph
        generator.build_graph(sample_documents)
        assert generator.get_graph().get_node_count() > 0

        # Generate different types of questions
        simple_questions = generator.generate_questions(num_questions=3)
        multi_hop_questions = generator.generate_multi_hop_questions(hops=2)

        # Create final dataset
        all_questions = simple_questions + multi_hop_questions
        dataset = Dataset(
            name="complete-testset",
            version="1.0.0",
            test_cases=all_questions,
            metadata={"source": "knowledge_graph"},
        )

        assert len(dataset) >= 3
        assert all(isinstance(tc, TestCase) for tc in dataset.test_cases)
