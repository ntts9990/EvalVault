"""BM25 searcher module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import (
    build_query_set,
    build_retrieval_corpus,
    get_upstream_output,
    recall_at_k,
    safe_mean,
)
from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer
from evalvault.adapters.outbound.nlp.korean.bm25_retriever import KoreanBM25Retriever
from evalvault.domain.entities import EvaluationRun


class BM25SearcherModule(BaseAnalysisModule):
    """BM25 search evaluation module."""

    module_id = "bm25_searcher"
    name = "BM25 Searcher"
    description = "Evaluate BM25 retrieval over evaluation contexts."
    input_types = ["morpheme_stats"]
    output_types = ["search_score"]
    requires = ["morpheme_analyzer"]
    tags = ["search", "bm25"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")
        if not isinstance(run, EvaluationRun):
            return {
                "method": "bm25",
                "available": False,
                "errors": ["No run data available"],
            }

        params = params or {}
        max_documents = int(params.get("max_documents", 1000))
        max_queries = int(params.get("max_queries", 200))
        top_k = int(params.get("top_k", 5))

        documents, index_map = build_retrieval_corpus(run, max_documents=max_documents)
        queries = build_query_set(run, index_map=index_map, max_queries=max_queries)

        if not documents or not queries:
            return {
                "method": "bm25",
                "available": False,
                "errors": ["No documents or queries for retrieval"],
            }

        errors: list[str] = []
        try:
            tokenizer = KiwiTokenizer()
            retriever = KoreanBM25Retriever(tokenizer)
            retriever.index(documents)
        except Exception as exc:
            errors.append(str(exc))
            return {
                "method": "bm25",
                "available": False,
                "errors": errors,
            }

        per_query = []
        recall_scores: list[float] = []
        top_scores: list[float] = []

        for query in queries:
            results = retriever.search(query["query"], top_k=top_k)
            doc_ids = [res.doc_id for res in results]
            scores = [res.score for res in results]

            recall = recall_at_k(doc_ids, query["relevant_doc_ids"], k=top_k)
            recall_scores.append(recall)
            if scores:
                top_scores.append(scores[0])

            per_query.append(
                {
                    "query_id": query["query_id"],
                    "recall_at_k": recall,
                    "top_doc_ids": doc_ids,
                    "top_scores": scores,
                    "relevant_doc_ids": query["relevant_doc_ids"],
                }
            )

        avg_recall = safe_mean(recall_scores)
        summary = {
            "method": "bm25",
            "doc_count": len(documents),
            "query_count": len(queries),
            "avg_recall_at_k": round(avg_recall, 4),
            "avg_top_score": round(safe_mean(top_scores), 4),
        }

        return {
            "method": "bm25",
            "available": True,
            "score": round(avg_recall, 4),
            "summary": summary,
            "per_query": per_query,
            "errors": errors,
        }
