"""LLM-backed relation augmenter for knowledge graph generation."""

from __future__ import annotations

import json
from collections.abc import Sequence

from evalvault.domain.services.entity_extractor import Entity, Relation
from evalvault.ports.outbound.llm_port import LLMPort
from evalvault.ports.outbound.relation_augmenter_port import RelationAugmenterPort


class LLMRelationAugmenter(RelationAugmenterPort):
    """LLM을 사용해 저신뢰 관계를 검증/보강."""

    def __init__(
        self,
        llm_port: LLMPort,
        max_relations: int = 5,
        system_prompt: str | None = None,
    ):
        self._llm_port = llm_port
        self._max_relations = max_relations
        self._system_prompt = system_prompt or (
            "You are a knowledge graph auditor for Korean insurance documents. "
            "Review the provided document snippet and confirm or fix the relations."
        )

    def augment_relations(
        self,
        document_text: str,
        entities: Sequence[Entity],
        low_confidence_relations: Sequence[Relation],
    ) -> list[Relation]:
        if not low_confidence_relations:
            return []

        prompt = self._build_prompt(document_text, entities, low_confidence_relations)
        llm = self._llm_port.as_ragas_llm()

        try:
            raw_response = self._invoke_llm(llm, prompt)
            parsed = self._parse_response(raw_response)
        except Exception:
            return []

        relations: list[Relation] = []
        for item in parsed[: self._max_relations]:
            try:
                relation = Relation(
                    source=item["source"],
                    target=item["target"],
                    relation_type=item["relation_type"],
                    confidence=float(item.get("confidence", 0.7)),
                    provenance="llm",
                    evidence=item.get("justification"),
                )
            except (KeyError, ValueError, TypeError):
                continue
            relations.append(relation)

        return relations

    def _build_prompt(
        self,
        document_text: str,
        entities: Sequence[Entity],
        relations: Sequence[Relation],
    ) -> str:
        entity_lines = [
            f"- {entity.entity_type}: {entity.name} (confidence={entity.confidence:.2f})"
            for entity in entities
        ]
        relation_lines = [
            f"- {rel.source} -> {rel.target} [{rel.relation_type}] conf={rel.confidence:.2f}"
            for rel in relations
        ]
        return (
            f"{self._system_prompt}\n"
            "Return a JSON array of objects with keys "
            "source, target, relation_type, confidence, justification.\n\n"
            "Document:\n"
            f"{document_text}\n\n"
            "Entities:\n"
            f"{chr(10).join(entity_lines)}\n\n"
            "Low-confidence relations:\n"
            f"{chr(10).join(relation_lines)}"
        )

    @staticmethod
    def _invoke_llm(llm, prompt: str) -> str:
        """LLM 호출 추상화."""
        if hasattr(llm, "invoke"):
            result = llm.invoke(prompt)
        elif hasattr(llm, "predict"):
            result = llm.predict(prompt)
        else:
            result = llm(prompt)

        if hasattr(result, "content"):
            return str(result.content)
        return str(result)

    @staticmethod
    def _parse_response(response_text: str) -> list[dict]:
        """LLM 응답에서 JSON 배열 추출."""
        text = response_text.strip()
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            text = text[start : end + 1]

        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("LLM response is not a list")
        return data
