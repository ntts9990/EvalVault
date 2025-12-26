"""Port for augmenting low-confidence relations via external services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from evalvault.domain.services.entity_extractor import Entity, Relation


class RelationAugmenterPort(ABC):
    """Outbound port for relation augmentation (e.g., LLM 보강)."""

    @abstractmethod
    def augment_relations(
        self,
        document_text: str,
        entities: Sequence[Entity],
        low_confidence_relations: Sequence[Relation],
    ) -> list[Relation]:
        """보강된 관계 목록을 반환."""
        raise NotImplementedError
