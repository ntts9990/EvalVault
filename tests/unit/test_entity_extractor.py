"""Unit tests for entity extractor."""

import pytest

from evalvault.domain.services.entity_extractor import (
    Entity,
    EntityExtractor,
    Relation,
)


class TestEntity:
    """Test suite for Entity dataclass."""

    def test_entity_creation(self):
        """Test entity creation with basic attributes."""
        entity = Entity(
            name="삼성생명",
            entity_type="organization",
            attributes={"industry": "insurance"},
        )
        assert entity.name == "삼성생명"
        assert entity.entity_type == "organization"
        assert entity.attributes["industry"] == "insurance"
        assert entity.confidence == 1.0
        assert entity.provenance == "regex"

    def test_entity_with_empty_attributes(self):
        """Test entity with empty attributes."""
        entity = Entity(name="종신보험", entity_type="product", attributes={})
        assert entity.name == "종신보험"
        assert entity.attributes == {}
        assert entity.confidence == 1.0


class TestRelation:
    """Test suite for Relation dataclass."""

    def test_relation_creation(self):
        """Test relation creation."""
        relation = Relation(
            source="삼성생명",
            target="종신보험",
            relation_type="provides",
        )
        assert relation.source == "삼성생명"
        assert relation.target == "종신보험"
        assert relation.relation_type == "provides"


class TestEntityExtractor:
    """Test suite for EntityExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create entity extractor instance."""
        return EntityExtractor()

    def test_initialization(self, extractor):
        """Test extractor initialization."""
        assert extractor is not None

    def test_extract_entities_from_insurance_text(self, extractor):
        """Test extracting entities from insurance text."""
        text = "삼성생명의 종신보험 상품은 사망보험금 1억원을 보장합니다."
        entities = extractor.extract_entities(text)

        assert len(entities) > 0
        # Should extract company name
        assert any(e.name == "삼성생명" and e.entity_type == "organization" for e in entities)
        # Should extract product type
        assert any(e.name == "종신보험" and e.entity_type == "product" for e in entities)

    def test_extract_money_entities(self, extractor):
        """Test extracting money amount entities."""
        text = "보험료는 월 50,000원이며, 보장금액은 1억원입니다."
        entities = extractor.extract_entities(text)

        money_entities = [e for e in entities if e.entity_type == "money"]
        assert len(money_entities) >= 2
        assert any("50,000원" in e.name for e in money_entities)
        assert any("1억원" in e.name or "1억" in e.name for e in money_entities)

    def test_extract_period_entities(self, extractor):
        """Test extracting period/duration entities."""
        text = "보험 기간은 10년이며, 납입 기간은 5년입니다."
        entities = extractor.extract_entities(text)

        period_entities = [e for e in entities if e.entity_type == "period"]
        assert len(period_entities) >= 2
        assert any("10년" in e.name for e in period_entities)
        assert any("5년" in e.name for e in period_entities)

    def test_extract_coverage_entities(self, extractor):
        """Test extracting coverage/benefit entities."""
        text = "사망보험금, 암진단비, 입원비를 보장합니다."
        entities = extractor.extract_entities(text)

        coverage_entities = [e for e in entities if e.entity_type == "coverage"]
        assert len(coverage_entities) >= 3
        assert any("사망보험금" in e.name for e in coverage_entities)
        assert any("암진단비" in e.name or "진단비" in e.name for e in coverage_entities)
        assert any("입원비" in e.name for e in coverage_entities)

    def test_extract_multiple_companies(self, extractor):
        """Test extracting multiple insurance companies."""
        text = "삼성생명, 한화생명, 교보생명은 대표적인 생명보험사입니다."
        entities = extractor.extract_entities(text)

        companies = [e for e in entities if e.entity_type == "organization"]
        assert len(companies) >= 3
        assert any("삼성생명" in e.name for e in companies)
        assert any("한화생명" in e.name for e in companies)
        assert any("교보생명" in e.name for e in companies)

    def test_extract_product_types(self, extractor):
        """Test extracting various insurance product types."""
        text = "종신보험, 정기보험, 연금보험, 암보험 등 다양한 상품이 있습니다."
        entities = extractor.extract_entities(text)

        products = [e for e in entities if e.entity_type == "product"]
        assert len(products) >= 4
        assert any("종신보험" in e.name for e in products)
        assert any("정기보험" in e.name for e in products)
        assert any("연금보험" in e.name for e in products)
        assert any("암보험" in e.name for e in products)

    def test_extract_from_empty_text(self, extractor):
        """Test extracting entities from empty text."""
        entities = extractor.extract_entities("")
        assert entities == []

    def test_extract_from_text_without_entities(self, extractor):
        """Test extracting entities from text without recognizable entities."""
        text = "이것은 일반적인 텍스트입니다."
        entities = extractor.extract_entities(text)
        # May be empty or contain generic entities depending on implementation
        assert isinstance(entities, list)

    def test_extract_entities_with_attributes(self, extractor):
        """Test that extracted entities have meaningful attributes."""
        text = "삼성생명의 종신보험은 사망 시 1억원을 보장합니다."
        entities = extractor.extract_entities(text)

        for entity in entities:
            assert entity.name is not None
            assert entity.entity_type is not None
            assert isinstance(entity.attributes, dict)

    def test_extract_relations_basic(self, extractor):
        """Test extracting basic relations between entities."""
        text = "삼성생명은 종신보험을 제공합니다."
        entities = extractor.extract_entities(text)
        relations = extractor.extract_relations(text, entities)

        assert len(relations) > 0
        # Should find relation between company and product
        assert any(r.source == "삼성생명" and r.target == "종신보험" for r in relations)

    def test_extract_relations_coverage(self, extractor):
        """Test extracting relations for coverage/benefits."""
        text = "종신보험은 사망보험금을 보장합니다."
        entities = extractor.extract_entities(text)
        relations = extractor.extract_relations(text, entities)

        assert len(relations) > 0
        # Should find relation between product and coverage
        assert any("종신보험" in r.source for r in relations)

    def test_extract_relations_money(self, extractor):
        """Test extracting relations involving money amounts."""
        text = "사망보험금은 1억원입니다."
        entities = extractor.extract_entities(text)
        relations = extractor.extract_relations(text, entities)

        assert len(relations) > 0
        # Should find relation between coverage and amount
        assert any("보험금" in r.source or "보험금" in r.target for r in relations)

    def test_extract_relations_period(self, extractor):
        """Test extracting relations involving periods."""
        text = "보험 기간은 10년입니다."
        entities = extractor.extract_entities(text)
        relations = extractor.extract_relations(text, entities)

        assert len(relations) > 0
        # Should find relation between insurance and period
        assert any("10년" in r.target for r in relations)

    def test_extract_relations_with_no_entities(self, extractor):
        """Test extracting relations when no entities present."""
        relations = extractor.extract_relations("일반 텍스트", [])
        assert relations == []

    def test_extract_relations_complex_text(self, extractor):
        """Test extracting multiple relations from complex text."""
        text = "삼성생명의 종신보험은 사망보험금 1억원을 10년간 보장합니다."
        entities = extractor.extract_entities(text)
        relations = extractor.extract_relations(text, entities)

        assert len(relations) >= 2
        # Should have multiple relations connecting different entities
        sources = {r.source for r in relations}
        targets = {r.target for r in relations}
        assert len(sources) >= 2 or len(targets) >= 2

    def test_relation_types_are_meaningful(self, extractor):
        """Test that relation types are meaningful and categorized."""
        text = "삼성생명은 종신보험을 제공하며, 이는 사망보험금을 보장합니다."
        entities = extractor.extract_entities(text)
        relations = extractor.extract_relations(text, entities)

        # Check that relation types are not empty and are meaningful
        for relation in relations:
            assert relation.relation_type is not None
            assert len(relation.relation_type) > 0
            # Relation types should be categorized
            assert relation.relation_type in [
                "provides",
                "has_coverage",
                "has_amount",
                "has_period",
                "belongs_to",
                "is_a",
            ]
            assert 0.3 <= relation.confidence <= 1.0
            assert relation.provenance in {"regex", "llm"}

    def test_extract_entities_deduplication(self, extractor):
        """Test that duplicate entities are handled properly."""
        text = "삼성생명, 삼성생명의 종신보험, 삼성생명 상품"
        entities = extractor.extract_entities(text)

        # Should not have too many duplicates of same entity
        samsung_entities = [e for e in entities if "삼성생명" in e.name]
        # Allow some duplicates but not for every mention
        assert len(samsung_entities) <= 3
