"""Tests for LLMRelationAugmenter."""

import pytest

from evalvault.adapters.outbound.llm.llm_relation_augmenter import LLMRelationAugmenter
from evalvault.domain.services.entity_extractor import Entity, Relation
from evalvault.ports.outbound.llm_port import LLMPort


class _StubLLM:
    """Simple stub for LangChain-compatible LLM."""

    def __init__(self, response: str):
        self._response = response
        self.last_prompt = None

    def invoke(self, prompt: str):
        self.last_prompt = prompt
        return self._response


class _StubLLMPort(LLMPort):
    """LLMPort stub returning a controllable LLM."""

    def __init__(self, response: str):
        self._response = response
        self.llm = _StubLLM(response)

    def get_model_name(self) -> str:
        return "stub"

    def as_ragas_llm(self):
        return self.llm


def test_llm_relation_augmenter_parses_json():
    """LLM 응답을 Relation 객체로 파싱한다."""
    response = """
    [
        {
            "source": "종신보험",
            "target": "사망보험금",
            "relation_type": "has_coverage",
            "confidence": 0.88,
            "justification": "문장에서 명시적으로 설명됨"
        }
    ]
    """
    port = _StubLLMPort(response)
    augmenter = LLMRelationAugmenter(port)

    entities = [
        Entity(name="종신보험", entity_type="product", attributes={}, confidence=0.8),
        Entity(name="사망보험금", entity_type="coverage", attributes={}, confidence=0.8),
    ]
    low_conf_relations = [
        Relation(
            source="종신보험",
            target="사망보험금",
            relation_type="has_coverage",
            confidence=0.4,
        )
    ]

    augmented = augmenter.augment_relations(
        document_text="종신보험은 사망보험금을 보장합니다.",
        entities=entities,
        low_confidence_relations=low_conf_relations,
    )

    assert len(augmented) == 1
    assert augmented[0].provenance == "llm"
    assert augmented[0].confidence == pytest.approx(0.88, rel=1e-3)
    assert "문장에서" in augmented[0].evidence


def test_llm_relation_augmenter_handles_invalid_response():
    """잘못된 응답은 무시된다."""
    port = _StubLLMPort("not json")
    augmenter = LLMRelationAugmenter(port)

    relation = Relation(
        source="종신보험",
        target="사망보험금",
        relation_type="has_coverage",
        confidence=0.4,
    )

    result = augmenter.augment_relations("text", [], [relation])
    assert result == []
