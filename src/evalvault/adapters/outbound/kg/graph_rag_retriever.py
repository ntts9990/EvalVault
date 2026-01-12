"""GraphRAG-style retriever combining KG signals with BM25/Dense results."""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from evalvault.adapters.outbound.kg.networkx_adapter import NetworkXKnowledgeGraph
from evalvault.config.phoenix_support import instrumentation_span, set_span_attributes
from evalvault.domain.entities.kg import EntityModel, RelationModel
from evalvault.domain.services.entity_extractor import EntityExtractor
from evalvault.ports.outbound.korean_nlp_port import RetrieverResultProtocol

logger = logging.getLogger(__name__)


@dataclass
class GraphRAGResult(RetrieverResultProtocol):
    """Unified GraphRAG retrieval result."""

    doc_id: str
    score: float
    rank: int
    document: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class GraphRAGRetriever:
    """LightRAG-inspired retriever.

    It fuses KG-derived candidates with BM25/Dense retrieval using RRF.
    """

    def __init__(
        self,
        kg: NetworkXKnowledgeGraph,
        *,
        bm25_retriever: Any | None = None,
        dense_retriever: Any | None = None,
        entity_extractor: EntityExtractor | None = None,
        keyword_extractor: Callable[[str], Sequence[str]] | None = None,
        hop_limit: int = 2,
        entity_weight: float = 0.4,
        relation_weight: float = 0.3,
        chunk_weight: float = 0.3,
        rrf_k: int = 60,
        candidate_multiplier: int = 2,
        min_entity_match_length: int = 2,
        cache_size: int = 128,
        documents: list[str] | None = None,
        document_ids: list[str] | None = None,
    ) -> None:
        if hop_limit < 0:
            msg = "hop_limit must be >= 0"
            raise ValueError(msg)
        if documents and document_ids and len(documents) != len(document_ids):
            msg = "documents and document_ids length must match"
            raise ValueError(msg)

        self._kg = kg
        self._bm25_retriever = bm25_retriever
        self._dense_retriever = dense_retriever
        self._entity_extractor = entity_extractor or EntityExtractor()
        self._keyword_extractor = keyword_extractor or self._build_keyword_extractor()
        self._keyword_extractor_failed = False
        self._hop_limit = hop_limit
        self._entity_weight = max(entity_weight, 0.0)
        self._relation_weight = max(relation_weight, 0.0)
        self._chunk_weight = max(chunk_weight, 0.0)
        self._rrf_k = max(rrf_k, 1)
        self._candidate_multiplier = max(candidate_multiplier, 1)
        self._min_entity_match_length = max(min_entity_match_length, 1)
        self._cache_size = max(cache_size, 0)
        self._document_ids = document_ids
        self._documents_by_id = self._build_document_lookup(documents, document_ids)
        self._canonical_lookup = self._build_canonical_lookup()
        self._query_cache: OrderedDict[str, tuple[list[str], dict[str, dict[str, Any]]]] = (
            OrderedDict()
        )

    def search(self, query: str, top_k: int = 5) -> list[GraphRAGResult]:
        """Search documents with KG + BM25 + Dense fusion."""
        if not query or top_k <= 0:
            return []

        span_attrs = {
            "retriever.graphrag.top_k": top_k,
            "retriever.graphrag.hop_limit": self._hop_limit,
            "retriever.graphrag.rrf_k": self._rrf_k,
            "retriever.graphrag.candidate_multiplier": self._candidate_multiplier,
            "retriever.graphrag.entity_weight": self._entity_weight,
            "retriever.graphrag.relation_weight": self._relation_weight,
            "retriever.graphrag.chunk_weight": self._chunk_weight,
            "retriever.graphrag.min_entity_match_length": self._min_entity_match_length,
        }

        with instrumentation_span("retriever.graphrag.search", span_attrs) as span:
            started_at = time.perf_counter()
            kg_candidates, kg_metadata = self._retrieve_from_kg(query)
            bm25_candidates, bm25_metadata = self._retrieve_from_chunks(
                self._bm25_retriever,
                query,
                top_k,
                source="bm25",
            )
            dense_candidates, dense_metadata = self._retrieve_from_chunks(
                self._dense_retriever,
                query,
                top_k,
                source="dense",
            )

            ranked_lists = {
                "kg": kg_candidates,
                "bm25": bm25_candidates,
                "dense": dense_candidates,
            }
            weights = self._resolve_rrf_weights(
                has_bm25=bool(bm25_candidates),
                has_dense=bool(dense_candidates),
            )
            fused_scores = self._rrf_merge(ranked_lists, weights)
            if not fused_scores:
                return []

            merged_metadata = self._merge_metadata(kg_metadata, bm25_metadata, dense_metadata)
            ranked = sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)[:top_k]

            results: list[GraphRAGResult] = []
            for rank, (doc_id, score) in enumerate(ranked, start=1):
                results.append(
                    GraphRAGResult(
                        doc_id=doc_id,
                        score=score,
                        rank=rank,
                        document=self._documents_by_id.get(doc_id),
                        metadata=merged_metadata.get(doc_id, {}),
                    )
                )

            elapsed_ms = (time.perf_counter() - started_at) * 1000
            if span:
                set_span_attributes(
                    span,
                    {
                        "retriever.graphrag.search_ms": round(elapsed_ms, 3),
                        "retriever.graphrag.result_count": len(results),
                        "retriever.graphrag.kg_candidates": len(kg_candidates),
                        "retriever.graphrag.bm25_candidates": len(bm25_candidates),
                        "retriever.graphrag.dense_candidates": len(dense_candidates),
                    },
                )

            return results

    def update_graph(self, kg: NetworkXKnowledgeGraph) -> dict[str, int]:
        """Merge a new graph into the retriever's KG."""

        stats = self._kg.merge(kg)
        self._canonical_lookup = self._build_canonical_lookup()
        self._query_cache.clear()
        return stats

    def update_documents(
        self,
        documents: list[str],
        *,
        document_ids: list[str] | None = None,
    ) -> None:
        """Update the document lookup used for result hydration."""

        if not documents:
            return

        updates = self._build_document_lookup(documents, document_ids)
        self._documents_by_id.update(updates)
        if document_ids:
            if self._document_ids is None:
                self._document_ids = list(document_ids)
            else:
                for doc_id in document_ids:
                    if doc_id not in self._document_ids:
                        self._document_ids.append(doc_id)

    def _retrieve_from_kg(self, query: str) -> tuple[list[str], dict[str, dict[str, Any]]]:
        cache_key = self._cache_key(query)
        if self._cache_size > 0:
            cached = self._query_cache.get(cache_key)
            if cached:
                self._query_cache.move_to_end(cache_key)
                return cached

        entity_names = self._extract_query_entities(query)
        if not entity_names:
            return [], {}

        entities = self._expand_entities(entity_names)
        relations = self._collect_relations(entities)
        kg_scores = self._score_kg_documents(entities, relations)
        if not kg_scores:
            return [], {}

        ranked = sorted(kg_scores.items(), key=lambda item: item[1]["score"], reverse=True)
        ranked_doc_ids = [self._normalize_doc_id(doc_id) for doc_id, _ in ranked]
        metadata = {self._normalize_doc_id(doc_id): info for doc_id, info in ranked}
        self._cache_kg_result(cache_key, ranked_doc_ids, metadata)
        return ranked_doc_ids, metadata

    def _retrieve_from_chunks(
        self,
        retriever: Any | None,
        query: str,
        top_k: int,
        *,
        source: str,
    ) -> tuple[list[str], dict[str, dict[str, Any]]]:
        if retriever is None:
            return [], {}

        candidate_k = max(top_k, top_k * self._candidate_multiplier)
        try:
            results = retriever.search(query, top_k=candidate_k)
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Failed %s retrieval: %s", source, exc)
            return [], {}

        ranked_doc_ids: list[str] = []
        metadata: dict[str, dict[str, Any]] = {}
        for rank, result in enumerate(results, start=1):
            doc_id = self._normalize_doc_id(getattr(result, "doc_id", result))
            ranked_doc_ids.append(doc_id)
            entry = metadata.setdefault(doc_id, {})
            entry["rank"] = rank
            score = getattr(result, "score", None)
            if score is not None:
                entry["score"] = float(score)
        return ranked_doc_ids, metadata

    def _extract_query_entities(self, query: str) -> list[str]:
        matched: set[str] = set()

        for entity in self._entity_extractor.extract_entities(query):
            resolved = self._resolve_entity_name(entity.name)
            if resolved:
                matched.add(resolved)

        for keyword in self._extract_keywords(query):
            resolved = self._resolve_entity_name(keyword)
            if resolved:
                matched.add(resolved)

        query_lower = query.lower()
        for entity in self._kg.get_all_entities():
            if len(entity.name) < self._min_entity_match_length:
                continue
            if entity.name.lower() in query_lower:
                matched.add(entity.name)
                continue
            if entity.canonical_name and entity.canonical_name in query_lower:
                matched.add(entity.name)

        return list(matched)

    def _resolve_entity_name(self, name: str) -> str | None:
        if self._kg.has_entity(name):
            return name
        normalized = name.strip().lower()
        return self._canonical_lookup.get(normalized)

    def _extract_keywords(self, query: str) -> list[str]:
        if not self._keyword_extractor or not query:
            return []
        try:
            keywords = self._keyword_extractor(query)
        except ImportError as exc:
            if not self._keyword_extractor_failed:
                logger.warning("Keyword extractor unavailable: %s", exc)
                self._keyword_extractor_failed = True
            self._keyword_extractor = None
            return []
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Keyword extractor failed: %s", exc)
            return []

        normalized: list[str] = []
        for keyword in keywords:
            if not isinstance(keyword, str):
                continue
            trimmed = keyword.strip()
            if len(trimmed) < self._min_entity_match_length:
                continue
            normalized.append(trimmed)
        return normalized

    def _build_keyword_extractor(
        self,
    ) -> Callable[[str], Sequence[str]] | None:
        try:
            from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer
        except Exception:  # pragma: no cover - optional dependency
            return None

        tokenizer = KiwiTokenizer()
        return tokenizer.extract_keywords

    def _expand_entities(self, entity_names: list[str]) -> list[EntityModel]:
        expanded: dict[str, EntityModel] = {}
        for name in entity_names:
            entity = self._kg.get_entity(name)
            if entity:
                expanded[entity.name] = entity
            if self._hop_limit > 0:
                for neighbor in self._kg.find_neighbors(name, depth=self._hop_limit):
                    expanded[neighbor.name] = neighbor
        return list(expanded.values())

    def _collect_relations(self, entities: list[EntityModel]) -> list[RelationModel]:
        names = {entity.name for entity in entities}
        relations: list[RelationModel] = []
        seen: set[tuple[str, str, str]] = set()

        for entity in entities:
            for relation in self._kg.get_outgoing_relations(entity.name):
                if relation.target not in names:
                    continue
                key = (relation.source, relation.target, relation.relation_type)
                if key in seen:
                    continue
                seen.add(key)
                relations.append(relation)
        return relations

    def _score_kg_documents(
        self,
        entities: list[EntityModel],
        relations: list[RelationModel],
    ) -> dict[str, dict[str, Any]]:
        scores: dict[str, dict[str, Any]] = {}

        for entity in entities:
            if not entity.source_document_id:
                continue
            doc_id = str(entity.source_document_id)
            entry = scores.setdefault(
                doc_id,
                {
                    "score": 0.0,
                    "entity_score": 0.0,
                    "relation_score": 0.0,
                    "entities": set(),
                    "relations": set(),
                },
            )
            entity_score = self._entity_weight * entity.confidence
            entry["score"] += entity_score
            entry["entity_score"] += entity_score
            entry["entities"].add(entity.name)

        for relation in relations:
            relation_score = self._relation_weight * relation.confidence
            relation_key = f"{relation.source}->{relation.target}:{relation.relation_type}"
            for entity_name in (relation.source, relation.target):
                entity = self._kg.get_entity(entity_name)
                if not entity or not entity.source_document_id:
                    continue
                doc_id = str(entity.source_document_id)
                entry = scores.setdefault(
                    doc_id,
                    {
                        "score": 0.0,
                        "entity_score": 0.0,
                        "relation_score": 0.0,
                        "entities": set(),
                        "relations": set(),
                    },
                )
                entry["score"] += relation_score
                entry["relation_score"] += relation_score
                entry["relations"].add(relation_key)

        for entry in scores.values():
            entry["entities"] = sorted(entry["entities"])
            entry["relations"] = sorted(entry["relations"])
        return scores

    def _rrf_merge(
        self,
        ranked_lists: dict[str, list[str]],
        weights: dict[str, float],
    ) -> dict[str, float]:
        scores: dict[str, float] = {}
        for source, doc_ids in ranked_lists.items():
            weight = weights.get(source, 0.0)
            if weight <= 0.0:
                continue
            for rank, doc_id in enumerate(doc_ids, start=1):
                scores[doc_id] = scores.get(doc_id, 0.0) + weight / (self._rrf_k + rank)
        return scores

    def _merge_metadata(
        self,
        kg_metadata: dict[str, dict[str, Any]],
        bm25_metadata: dict[str, dict[str, Any]],
        dense_metadata: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        all_doc_ids = set(kg_metadata) | set(bm25_metadata) | set(dense_metadata)
        for doc_id in all_doc_ids:
            merged_entry: dict[str, Any] = {}
            if doc_id in kg_metadata:
                merged_entry["kg"] = kg_metadata[doc_id]
            if doc_id in bm25_metadata:
                merged_entry["bm25"] = bm25_metadata[doc_id]
            if doc_id in dense_metadata:
                merged_entry["dense"] = dense_metadata[doc_id]
            merged[doc_id] = merged_entry
        return merged

    def _resolve_rrf_weights(self, *, has_bm25: bool, has_dense: bool) -> dict[str, float]:
        kg_weight = self._entity_weight + self._relation_weight
        if not has_bm25 and not has_dense:
            return {"kg": kg_weight, "bm25": 0.0, "dense": 0.0}
        if has_bm25 and not has_dense:
            return {"kg": kg_weight, "bm25": self._chunk_weight, "dense": 0.0}
        if has_dense and not has_bm25:
            return {"kg": kg_weight, "bm25": 0.0, "dense": self._chunk_weight}
        chunk_each = self._chunk_weight / 2
        return {"kg": kg_weight, "bm25": chunk_each, "dense": chunk_each}

    def _normalize_doc_id(self, doc_id: str | int) -> str:
        if isinstance(doc_id, int) and self._document_ids and 0 <= doc_id < len(self._document_ids):
            return self._document_ids[doc_id]
        if isinstance(doc_id, str):
            normalized = doc_id.strip()
            if normalized.isdigit() and self._document_ids:
                idx = int(normalized)
                if 0 <= idx < len(self._document_ids):
                    return self._document_ids[idx]
            return normalized
        return str(doc_id)

    def _build_document_lookup(
        self, documents: list[str] | None, document_ids: list[str] | None
    ) -> dict[str, str]:
        if not documents:
            return {}
        if document_ids:
            return {document_ids[idx]: doc for idx, doc in enumerate(documents)}
        return {str(idx): doc for idx, doc in enumerate(documents)}

    def _build_canonical_lookup(self) -> dict[str, str]:
        lookup: dict[str, str] = {}
        for entity in self._kg.get_all_entities():
            if entity.canonical_name and entity.canonical_name not in lookup:
                lookup[entity.canonical_name] = entity.name
        return lookup

    @staticmethod
    def _cache_key(query: str) -> str:
        return query.strip().lower()

    def _cache_kg_result(
        self,
        cache_key: str,
        ranked_doc_ids: list[str],
        metadata: dict[str, dict[str, Any]],
    ) -> None:
        if self._cache_size <= 0:
            return
        self._query_cache[cache_key] = (ranked_doc_ids, metadata)
        self._query_cache.move_to_end(cache_key)
        if len(self._query_cache) > self._cache_size:
            self._query_cache.popitem(last=False)
