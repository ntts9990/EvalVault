"""Hybrid RRF search module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import recall_at_k, safe_mean


class HybridRRFModule(BaseAnalysisModule):
    """Combine BM25 and embedding results using RRF."""

    module_id = "hybrid_rrf"
    name = "Hybrid RRF"
    description = "Blend sparse and dense retrieval scores using RRF."
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
        rrf_k = int(params.get("rrf_k", 60))

        bm25_output = inputs.get("bm25_search", {})
        embedding_output = inputs.get("embedding_search", {})

        bm25_queries = {item["query_id"]: item for item in bm25_output.get("per_query", [])}
        emb_queries = {item["query_id"]: item for item in embedding_output.get("per_query", [])}

        if not bm25_queries and not emb_queries:
            return {
                "method": "hybrid_rrf",
                "available": False,
                "errors": ["No upstream search results"],
            }

        per_query = []
        recall_scores: list[float] = []

        for query_id in sorted(set(bm25_queries) | set(emb_queries)):
            bm25_entry = bm25_queries.get(query_id, {})
            emb_entry = emb_queries.get(query_id, {})

            bm25_docs = bm25_entry.get("top_doc_ids", [])
            emb_docs = emb_entry.get("top_doc_ids", [])
            relevant_ids = (
                bm25_entry.get("relevant_doc_ids") or emb_entry.get("relevant_doc_ids") or []
            )

            scores: dict[int, float] = {}
            for rank, doc_id in enumerate(bm25_docs, start=1):
                scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank)
            for rank, doc_id in enumerate(emb_docs, start=1):
                scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank)

            ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
            top_doc_ids = [doc_id for doc_id, _ in ranked[:top_k]]
            top_scores = [score for _, score in ranked[:top_k]]

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
            "method": "hybrid_rrf",
            "available": True,
            "score": round(avg_recall, 4),
            "summary": {
                "avg_recall_at_k": round(avg_recall, 4),
                "query_count": len(per_query),
            },
            "per_query": per_query,
        }
