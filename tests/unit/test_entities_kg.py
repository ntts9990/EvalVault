"""Unit tests for knowledge graph entity and relation models."""

import pytest

from evalvault.domain.entities.kg import EntityModel, RelationModel


def test_entity_model_normalizes_and_defaults():
    """엔티티는 canonical_name, provenance, confidence 기본값을 가진다."""
    entity = EntityModel(
        name=" 삼성생명  ",
        entity_type="organization",
        attributes={"domain": "insurance"},
    )

    assert entity.name == " 삼성생명  "
    assert entity.canonical_name == "삼성생명"
    assert entity.confidence == 1.0
    assert entity.provenance == "unknown"
    assert entity.attributes["domain"] == "insurance"


def test_entity_model_rejects_invalid_confidence():
    """confidence 범위가 0~1을 벗어나면 예외를 발생시킨다."""
    with pytest.raises(ValueError):
        EntityModel(
            name="암보험",
            entity_type="product",
            confidence=1.5,
        )


def test_relation_model_validates_source_and_target():
    """관계는 source와 target이 동일할 수 없다."""
    with pytest.raises(ValueError):
        RelationModel(
            source="암보험",
            target="암보험",
            relation_type="has_coverage",
        )


def test_relation_model_to_attributes():
    """엣지 속성 직렬화 함수는 provenance와 confidence를 포함한다."""
    relation = RelationModel(
        source="삼성생명",
        target="종신보험",
        relation_type="provides",
        confidence=0.8,
        provenance="regex",
        attributes={"note": "부모와 30자 이내 등장"},
    )

    attrs = relation.to_edge_attributes()
    assert attrs["relation_type"] == "provides"
    assert attrs["confidence"] == pytest.approx(0.8)
    assert attrs["provenance"] == "regex"
    assert attrs["attributes"]["note"].startswith("부모")
