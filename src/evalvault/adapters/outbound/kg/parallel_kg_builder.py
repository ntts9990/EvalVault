"""Parallel KG builder for large document collections."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from itertools import islice
from typing import Any

from evalvault.adapters.outbound.kg.networkx_adapter import NetworkXKnowledgeGraph
from evalvault.domain.entities.kg import EntityModel, RelationModel
from evalvault.domain.services.entity_extractor import (
    Entity as ExtractedEntity,
)
from evalvault.domain.services.entity_extractor import (
    EntityExtractor,
)
from evalvault.domain.services.entity_extractor import (
    Relation as ExtractedRelation,
)

logger = logging.getLogger(__name__)


@dataclass
class KGBuilderStats:
    """Build metrics for KG construction."""

    documents_processed: int = 0
    entities_processed: int = 0
    entities_added: int = 0
    relations_added: int = 0
    chunks_processed: int = 0
    started_at: float = field(default_factory=time.perf_counter)
    last_updated_at: float = field(default_factory=time.perf_counter)

    def touch(self) -> None:
        self.last_updated_at = time.perf_counter()

    @property
    def elapsed_ms(self) -> float:
        return (self.last_updated_at - self.started_at) * 1000

    def snapshot(self) -> dict[str, Any]:
        return {
            "documents_processed": self.documents_processed,
            "entities_processed": self.entities_processed,
            "entities_added": self.entities_added,
            "relations_added": self.relations_added,
            "chunks_processed": self.chunks_processed,
            "elapsed_ms": round(self.elapsed_ms, 3),
        }


@dataclass
class KGBuildResult:
    """Build output for KG construction."""

    graph: NetworkXKnowledgeGraph
    stats: KGBuilderStats
    documents_by_id: dict[str, str] = field(default_factory=dict)


@dataclass
class _ExtractionResult:
    doc_id: str
    entities: list[ExtractedEntity]
    relations: list[ExtractedRelation]
    document: str | None = None


def _extract_document(payload: tuple[str, str, bool]) -> _ExtractionResult:
    doc_id, document, keep_document = payload
    extractor = EntityExtractor()
    entities = extractor.extract_entities(document)
    relations = extractor.extract_relations(document, entities)
    stored = document if keep_document else None
    return _ExtractionResult(
        doc_id=doc_id,
        entities=entities,
        relations=relations,
        document=stored,
    )


class ParallelKGBuilder:
    """Parallel Knowledge Graph builder.

    This builder supports large document collections by processing documents in
    batches and optionally parallelizing entity extraction with process workers.
    """

    def __init__(
        self,
        *,
        workers: int = 4,
        batch_size: int = 32,
        store_documents: bool = False,
        progress_callback: Callable[[KGBuilderStats], None] | None = None,
    ) -> None:
        self._workers = max(1, workers)
        self._batch_size = max(1, batch_size)
        self._store_documents = store_documents
        self._progress_callback = progress_callback
        self._stats = KGBuilderStats()

    @property
    def stats(self) -> KGBuilderStats:
        return self._stats

    def build(
        self,
        documents: Iterable[str],
        *,
        document_ids: Iterable[str] | None = None,
        id_prefix: str = "doc-",
    ) -> KGBuildResult:
        graph = NetworkXKnowledgeGraph()
        documents_by_id: dict[str, str] = {}
        relation_keys: set[tuple[str, str, str]] = set()
        self._stats = KGBuilderStats()

        if self._workers > 1:
            with ProcessPoolExecutor(max_workers=self._workers) as executor:
                for batch in self._iter_batches(documents, document_ids, id_prefix):
                    payloads = [(doc_id, doc, self._store_documents) for doc_id, doc in batch]
                    results = executor.map(
                        _extract_document,
                        payloads,
                        chunksize=max(1, len(payloads) // self._workers),
                    )
                    self._consume_results(results, graph, documents_by_id, relation_keys)
                    self._stats.chunks_processed += 1
                    self._notify_progress()
        else:
            extractor = EntityExtractor()
            for batch in self._iter_batches(documents, document_ids, id_prefix):
                results = []
                for doc_id, doc in batch:
                    entities = extractor.extract_entities(doc)
                    relations = extractor.extract_relations(doc, entities)
                    stored = doc if self._store_documents else None
                    results.append(
                        _ExtractionResult(
                            doc_id=doc_id,
                            entities=entities,
                            relations=relations,
                            document=stored,
                        )
                    )
                self._consume_results(results, graph, documents_by_id, relation_keys)
                self._stats.chunks_processed += 1
                self._notify_progress()

        return KGBuildResult(
            graph=graph,
            stats=self._stats,
            documents_by_id=documents_by_id,
        )

    def _iter_batches(
        self,
        documents: Iterable[str],
        document_ids: Iterable[str] | None,
        id_prefix: str,
    ) -> Iterator[list[tuple[str, str]]]:
        if document_ids is not None:
            pairs = zip(document_ids, documents, strict=False)
        else:
            pairs = ((f"{id_prefix}{idx}", doc) for idx, doc in enumerate(documents))

        iterator = iter(pairs)
        while True:
            batch = list(islice(iterator, self._batch_size))
            if not batch:
                break
            yield batch

    def _consume_results(
        self,
        results: Iterable[_ExtractionResult],
        graph: NetworkXKnowledgeGraph,
        documents_by_id: dict[str, str],
        relation_keys: set[tuple[str, str, str]],
    ) -> None:
        for result in results:
            self._stats.documents_processed += 1
            if result.document and self._store_documents:
                documents_by_id[result.doc_id] = result.document

            for entity in result.entities:
                self._stats.entities_processed += 1
                model = self._to_entity_model(entity, result.doc_id)
                added = self._upsert_entity(graph, model)
                if added:
                    self._stats.entities_added += 1

            for relation in result.relations:
                try:
                    model = self._to_relation_model(relation)
                except ValueError:
                    continue

                if not graph.has_entity(model.source) or not graph.has_entity(model.target):
                    continue

                key = (model.source, model.target, model.relation_type)
                if key in relation_keys:
                    continue
                relation_keys.add(key)
                graph.add_relation(model)
                self._stats.relations_added += 1

        self._stats.touch()

    def _notify_progress(self) -> None:
        if self._progress_callback:
            try:
                self._progress_callback(self._stats)
            except Exception:  # pragma: no cover - progress hooks are best-effort
                logger.debug("progress_callback failed", exc_info=True)

    @staticmethod
    def _to_entity_model(entity: ExtractedEntity, document_id: str) -> EntityModel:
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
        attributes = {"evidence": relation.evidence} if relation.evidence else {}
        return RelationModel(
            source=relation.source,
            target=relation.target,
            relation_type=relation.relation_type,
            provenance=relation.provenance,
            confidence=relation.confidence,
            attributes=attributes,
        )

    @staticmethod
    def _upsert_entity(graph: NetworkXKnowledgeGraph, model: EntityModel) -> bool:
        existing = graph.get_entity(model.name)
        if existing and existing.confidence >= model.confidence:
            return False
        graph.add_entity(model)
        return existing is None


__all__ = ["KGBuildResult", "KGBuilderStats", "ParallelKGBuilder"]
