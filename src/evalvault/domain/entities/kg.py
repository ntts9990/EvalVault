"""Pydantic models for knowledge graph entities and relations."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ProvenanceType = Literal["regex", "llm", "manual", "unknown"]


class EntityModel(BaseModel):
    """정규화된 지식그래프 엔티티."""

    name: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    canonical_name: str | None = None
    source_document_id: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance: ProvenanceType = "unknown"

    @field_validator("attributes")
    @classmethod
    def ensure_attributes_dict(cls, value: dict[str, Any] | None) -> dict[str, Any]:
        """None 값을 빈 dict로 변환."""
        return value or {}

    @model_validator(mode="after")
    def set_canonical_name(self) -> EntityModel:
        """canonical_name이 없으면 기본값을 채운다."""
        if not self.canonical_name:
            self.canonical_name = self._normalize(self.name)
        else:
            self.canonical_name = self._normalize(self.canonical_name)
        return self

    @staticmethod
    def _normalize(value: str) -> str:
        """간단한 정규화 (trim + lower)."""
        return value.strip().lower()

    def to_node_attributes(self) -> dict[str, Any]:
        """NetworkX 노드 속성 직렬화."""
        return {
            "entity_type": self.entity_type,
            "canonical_name": self.canonical_name,
            "source_document_id": self.source_document_id,
            "confidence": self.confidence,
            "provenance": self.provenance,
            "attributes": self.attributes.copy(),
        }


class RelationModel(BaseModel):
    """정규화된 지식그래프 관계."""

    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    relation_type: str = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance: ProvenanceType = "unknown"

    @field_validator("attributes")
    @classmethod
    def ensure_attributes_dict(cls, value: dict[str, Any] | None) -> dict[str, Any]:
        """None 값을 빈 dict로 변환."""
        return value or {}

    @model_validator(mode="after")
    def validate_source_target(self) -> RelationModel:
        """source와 target이 동일하면 예외."""
        if self.source == self.target:
            msg = "source와 target은 동일할 수 없습니다."
            raise ValueError(msg)
        return self

    def to_edge_attributes(self) -> dict[str, Any]:
        """NetworkX 엣지 속성 직렬화."""
        return {
            "relation_type": self.relation_type,
            "confidence": self.confidence,
            "provenance": self.provenance,
            "attributes": self.attributes.copy(),
        }
