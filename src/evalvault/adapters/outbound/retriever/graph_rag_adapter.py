"""GraphRAG adapter that exposes graph-centric retrieval helpers."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import Any

from evalvault.adapters.outbound.kg.networkx_adapter import NetworkXKnowledgeGraph
from evalvault.domain.entities.graph_rag import EntityNode, KnowledgeSubgraph, RelationEdge
from evalvault.domain.entities.kg import EntityModel, RelationModel
from evalvault.domain.services.entity_extractor import EntityExtractor
from evalvault.ports.outbound.graph_retriever_port import GraphRetrieverPort


class GraphRAGAdapter(GraphRetrieverPort):
    """GraphRAG adapter over NetworkXKnowledgeGraph."""

    def __init__(
        self,
        kg: NetworkXKnowledgeGraph,
        *,
        entity_extractor: EntityExtractor | None = None,
    ) -> None:
        self._kg = kg
        self._entity_extractor = entity_extractor or EntityExtractor()

    def extract_entities(self, text: str) -> list[EntityNode]:
        names = self._extract_entity_names(text)
        return [self._entity_to_node(entity) for entity in self._resolve_entities(names)]

    def build_subgraph(
        self,
        query: str,
        max_hops: int = 2,
        max_nodes: int = 20,
    ) -> KnowledgeSubgraph:
        if not query:
            return KnowledgeSubgraph(nodes=[], edges=[], relevance_score=0.0)

        resolved_max_hops = max(max_hops, 0)
        resolved_max_nodes = max(max_nodes, 1)
        names = self._extract_entity_names(query)
        seeds = self._resolve_entities(names)
        if not seeds:
            return KnowledgeSubgraph(nodes=[], edges=[], relevance_score=0.0)

        selected = self._select_entities(seeds, resolved_max_hops, resolved_max_nodes)
        edges = self._collect_edges(selected)
        relevance_score = self._compute_relevance(selected, edges)

        return KnowledgeSubgraph(
            nodes=[self._entity_to_node(entity) for entity in selected],
            edges=[self._relation_to_edge(edge) for edge in edges],
            relevance_score=relevance_score,
        )

    def generate_context(self, subgraph: KnowledgeSubgraph) -> str:
        if not subgraph.nodes and not subgraph.edges:
            return ""

        lines: list[str] = []
        if subgraph.nodes:
            lines.append("Entities:")
            for node in subgraph.nodes:
                label = f"{node.name} ({node.entity_type})"
                lines.append(f"- {label}")

        if subgraph.edges:
            if lines:
                lines.append("")
            lines.append("Relations:")
            for edge in subgraph.edges:
                label = f"{edge.source_id} -[{edge.relation_type}]-> {edge.target_id}"
                lines.append(f"- {label}")

        return "\n".join(lines)

    def _extract_entity_names(self, text: str) -> list[str]:
        names: list[str] = []
        for entity in self._entity_extractor.extract_entities(text):
            if entity.name:
                names.append(entity.name)
        names.extend(self._match_known_entities(text))
        return self._dedupe(names)

    def _match_known_entities(self, text: str) -> list[str]:
        if not text:
            return []
        query_lower = text.lower()
        matches: list[str] = []
        for entity in self._kg.get_all_entities():
            name = entity.name
            if name and name.lower() in query_lower:
                matches.append(name)
                continue
            canonical = entity.canonical_name
            if canonical and canonical in query_lower:
                matches.append(entity.name)
        return matches

    def _resolve_entities(self, names: Iterable[str]) -> list[EntityModel]:
        resolved: dict[str, EntityModel] = {}
        for name in names:
            entity = self._kg.get_entity(name)
            if entity:
                resolved[entity.name] = entity
        return list(resolved.values())

    def _select_entities(
        self,
        seeds: list[EntityModel],
        max_hops: int,
        max_nodes: int,
    ) -> list[EntityModel]:
        selected: dict[str, EntityModel] = {entity.name: entity for entity in seeds}
        if max_hops > 0:
            for seed in seeds:
                for neighbor in self._kg.find_neighbors(seed.name, depth=max_hops):
                    selected.setdefault(neighbor.name, neighbor)

        if len(selected) <= max_nodes:
            return list(selected.values())

        seed_names = {entity.name for entity in seeds}
        prioritized = sorted(
            selected.values(),
            key=lambda entity: (entity.name not in seed_names, -entity.confidence, entity.name),
        )
        return prioritized[:max_nodes]

    def _collect_edges(self, entities: list[EntityModel]) -> list[RelationModel]:
        selected = {entity.name for entity in entities}
        edges: list[RelationModel] = []
        seen: set[tuple[str, str, str]] = set()
        for entity in entities:
            for relation in self._kg.get_outgoing_relations(entity.name):
                if relation.target not in selected:
                    continue
                key = (relation.source, relation.target, relation.relation_type)
                if key in seen:
                    continue
                seen.add(key)
                edges.append(relation)
        return edges

    @staticmethod
    def _compute_relevance(
        entities: list[EntityModel],
        edges: list[RelationModel],
    ) -> float:
        if not entities and not edges:
            return 0.0
        scores = [entity.confidence for entity in entities] + [edge.confidence for edge in edges]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    @staticmethod
    def _entity_to_node(entity: EntityModel) -> EntityNode:
        attributes = {
            **entity.attributes,
            "confidence": entity.confidence,
            "provenance": entity.provenance,
            "source_document_id": entity.source_document_id,
            "canonical_name": entity.canonical_name,
        }
        return EntityNode(
            entity_id=entity.name,
            name=entity.name,
            entity_type=entity.entity_type,
            attributes=attributes,
        )

    @staticmethod
    def _relation_to_edge(edge: RelationModel) -> RelationEdge:
        attributes = {**edge.attributes, "provenance": edge.provenance}
        return RelationEdge(
            source_id=edge.source,
            target_id=edge.target,
            relation_type=edge.relation_type,
            weight=edge.confidence,
            attributes=attributes,
        )

    @staticmethod
    def _dedupe(values: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            deduped.append(value)
        return deduped


class LightRAGGraphAdapter(GraphRetrieverPort):
    """LightRAG-backed adapter that returns graph contexts."""

    def __init__(
        self,
        lightrag_client: Any,
        *,
        query_mode: str = "mix",
        query_param: Any | None = None,
        entity_extractor: EntityExtractor | None = None,
    ) -> None:
        self._client = lightrag_client
        self._query_mode = query_mode
        self._query_param = query_param
        self._entity_extractor = entity_extractor or EntityExtractor()

    def extract_entities(self, text: str) -> list[EntityNode]:
        names = [entity.name for entity in self._entity_extractor.extract_entities(text)]
        return [
            EntityNode(entity_id=name, name=name, entity_type="mention")
            for name in _dedupe_values(names)
        ]

    def build_subgraph(
        self,
        query: str,
        max_hops: int = 2,
        max_nodes: int = 20,
    ) -> KnowledgeSubgraph:
        if not query:
            return KnowledgeSubgraph(nodes=[], edges=[], relevance_score=0.0)

        param = self._build_query_param()
        response = self._run_query(query, param)
        context, references = self._extract_context_and_refs(response)
        nodes = self._references_to_nodes(references, max_nodes=max_nodes)
        relevance_score = 1.0 if context else 0.0
        return KnowledgeSubgraph(nodes=nodes, edges=[], relevance_score=relevance_score)

    def generate_context(self, subgraph: KnowledgeSubgraph) -> str:
        if not subgraph.nodes:
            return ""
        lines = ["References:"]
        for node in subgraph.nodes:
            label = node.name
            if node.attributes:
                ref_id = node.attributes.get("id")
                if ref_id and ref_id != node.name:
                    label = f"{node.name} ({ref_id})"
            lines.append(f"- {label}")
        return "\n".join(lines)

    def _build_query_param(self) -> Any | None:
        if self._query_param is not None:
            return self._query_param
        try:
            from lightrag import QueryParam

            return QueryParam(
                mode=self._query_mode,
                only_need_context=True,
                include_references=True,
            )
        except Exception:
            return None

    def _run_query(self, query: str, param: Any | None) -> Any:
        if hasattr(self._client, "query"):
            return self._client.query(query, param=param)
        if hasattr(self._client, "aquery"):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return asyncio.run(self._client.aquery(query, param=param))
            if loop.is_running():
                raise RuntimeError("LightRAG aquery requires async context")
        raise RuntimeError("LightRAG client must provide query or aquery")

    @staticmethod
    def _extract_context_and_refs(response: Any) -> tuple[str, list[Any]]:
        if isinstance(response, str):
            return response, []
        if isinstance(response, dict):
            context = response.get("context") or response.get("response") or response.get("answer")
            references = response.get("references") or response.get("refs") or []
            return str(context or ""), list(references) if references else []
        return "", []

    @staticmethod
    def _references_to_nodes(references: list[Any], *, max_nodes: int) -> list[EntityNode]:
        nodes: list[EntityNode] = []
        for idx, ref in enumerate(references, start=1):
            if len(nodes) >= max_nodes:
                break
            if isinstance(ref, dict):
                ref_id = ref.get("id") or ref.get("doc_id") or ref.get("source_id")
                name = str(ref.get("title") or ref_id or f"ref-{idx}")
                attrs = {k: v for k, v in ref.items() if k not in {"title"}}
                nodes.append(
                    EntityNode(
                        entity_id=str(ref_id or name),
                        name=name,
                        entity_type="reference",
                        attributes={"id": ref_id, **attrs},
                    )
                )
            else:
                nodes.append(
                    EntityNode(
                        entity_id=str(ref),
                        name=str(ref),
                        entity_type="reference",
                    )
                )
        return nodes


def _dedupe_values(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


__all__ = ["GraphRAGAdapter", "LightRAGGraphAdapter"]
