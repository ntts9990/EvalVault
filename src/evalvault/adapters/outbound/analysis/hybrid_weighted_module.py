"""Weighted hybrid search module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import recall_at_k, safe_mean


class HybridWeightedModule(BaseAnalysisModule):
    """Combine BM25 and embedding scores with weighted averaging."""

    module_id = "hybrid_weighted"
    name = "Hybrid Weighted"
    description = "Blend sparse and dense retrieval scores using weighted average."
    input_types = ["search_score"]
    output_types = ["search_score"]
    requires = ["bm25_searcher", "embedding_searcher"]
    tags = ["search", "hybrid"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        top_k = int(params.get("top_k", 5))
        bm25_weight = float(params.get("bm25_weight", 0.4))
        embedding_weight = float(params.get("embedding_weight", 0.6))

        bm25_output = inputs.get("bm25_search", {})
        embedding_output = inputs.get("embedding_search", {})

        bm25_queries = {item["query_id"]: item for item in bm25_output.get("per_query", [])}
        emb_queries = {item["query_id"]: item for item in embedding_output.get("per_query", [])}

        if not bm25_queries and not emb_queries:
            return {
                "method": "hybrid_weighted",
                "available": False,
                "errors": ["No upstream search results"],
            }

        total_weight = bm25_weight + embedding_weight
        if total_weight == 0:
            total_weight = 1.0

        per_query = []
        recall_scores: list[float] = []

        for query_id in sorted(set(bm25_queries) | set(emb_queries)):
            bm25_entry = bm25_queries.get(query_id, {})
            emb_entry = emb_queries.get(query_id, {})

            bm25_docs = bm25_entry.get("top_doc_ids", [])
            bm25_scores = bm25_entry.get("top_scores", [])
            emb_docs = emb_entry.get("top_doc_ids", [])
            emb_scores = emb_entry.get("top_scores", [])
            relevant_ids = (
                bm25_entry.get("relevant_doc_ids") or emb_entry.get("relevant_doc_ids") or []
            )

            scores: dict[int, float] = {}
            for doc_id, score in zip(bm25_docs, bm25_scores, strict=False):
                scores[doc_id] = scores.get(doc_id, 0.0) + score * bm25_weight
            for doc_id, score in zip(emb_docs, emb_scores, strict=False):
                scores[doc_id] = scores.get(doc_id, 0.0) + score * embedding_weight

            ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
            top_doc_ids = [doc_id for doc_id, _ in ranked[:top_k]]
            top_scores = [score / total_weight for _, score in ranked[:top_k]]

            recall = recall_at_k(top_doc_ids, relevant_ids, k=top_k)
            recall_scores.append(recall)

            per_query.append(
                {
                    "query_id": query_id,
                    "recall_at_k": recall,
                    "top_doc_ids": top_doc_ids,
                    "top_scores": top_scores,
                    "relevant_doc_ids": relevant_ids,
                }
            )

        avg_recall = safe_mean(recall_scores)
        return {
            "method": "hybrid_weighted",
            "available": True,
            "score": round(avg_recall, 4),
            "summary": {
                "avg_recall_at_k": round(avg_recall, 4),
                "query_count": len(per_query),
            },
            "per_query": per_query,
        }
