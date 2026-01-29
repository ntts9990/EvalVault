"""Embedding searcher module."""

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
from evalvault.adapters.outbound.nlp.korean.dense_retriever import KoreanDenseRetriever
from evalvault.config.settings import Settings
from evalvault.domain.entities import EvaluationRun


class EmbeddingSearcherModule(BaseAnalysisModule):
    """Dense embedding retrieval evaluation module."""

    module_id = "embedding_searcher"
    name = "Embedding Searcher"
    description = "Evaluate dense retrieval over evaluation contexts."
    input_types = ["metrics"]
    output_types = ["search_score"]
    requires = ["data_loader"]
    tags = ["search", "embedding"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")
        if not isinstance(run, EvaluationRun):
            return {
                "method": "embedding",
                "available": False,
                "errors": ["No run data available"],
            }

        params = params or {}
        max_documents = int(params.get("max_documents", 1000))
        max_queries = int(params.get("max_queries", 200))
        top_k = int(params.get("top_k", 5))
        embedding_profile = params.get("embedding_profile")
        model_name = params.get("model_name")

        documents, index_map = build_retrieval_corpus(run, max_documents=max_documents)
        queries = build_query_set(run, index_map=index_map, max_queries=max_queries)

        if not documents or not queries:
            return {
                "method": "embedding",
                "available": False,
                "errors": ["No documents or queries for retrieval"],
            }

        errors: list[str] = []
        retriever = None
        settings = Settings()

        if embedding_profile in {"dev", "prod"}:
            try:
                from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter

                adapter = OllamaAdapter(settings)
                retriever = KoreanDenseRetriever(
                    model_name=settings.ollama_embedding_model,
                    ollama_adapter=adapter,
                    profile=embedding_profile,
                )
            except Exception as exc:
                errors.append(str(exc))
                retriever = None

        if retriever is None and embedding_profile == "vllm":
            try:
                from evalvault.adapters.outbound.llm.vllm_adapter import VLLMAdapter

                adapter = VLLMAdapter(settings)
                retriever = KoreanDenseRetriever(
                    model_name=settings.vllm_embedding_model,
                    ollama_adapter=adapter,
                    profile=embedding_profile,
                )
            except Exception as exc:
                errors.append(str(exc))
                retriever = None

        if retriever is None:
            try:
                retriever = KoreanDenseRetriever(model_name=model_name)
            except Exception as exc:
                errors.append(str(exc))
                retriever = None

        if retriever is None:
            return {
                "method": "embedding",
                "available": False,
                "errors": errors or ["Embedding backend unavailable"],
            }

        try:
            retriever.index(documents)
        except Exception as exc:
            errors.append(str(exc))
            return {
                "method": "embedding",
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
            "method": "embedding",
            "doc_count": len(documents),
            "query_count": len(queries),
            "avg_recall_at_k": round(avg_recall, 4),
            "avg_top_score": round(safe_mean(top_scores), 4),
            "model": retriever.model_name,
            "dimension": retriever.dimension,
        }

        return {
            "method": "embedding",
            "available": True,
            "score": round(avg_recall, 4),
            "summary": summary,
            "per_query": per_query,
            "errors": errors,
        }
