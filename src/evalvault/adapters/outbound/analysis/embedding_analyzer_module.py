"""Embedding analyzer module."""

from __future__ import annotations

from typing import Any

import numpy as np

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output
from evalvault.adapters.outbound.nlp.korean.dense_retriever import KoreanDenseRetriever
from evalvault.config.settings import Settings
from evalvault.domain.entities import EvaluationRun


class EmbeddingAnalyzerModule(BaseAnalysisModule):
    """Compute embedding distribution statistics."""

    module_id = "embedding_analyzer"
    name = "Embedding Analyzer"
    description = "Compute embedding distribution stats from run texts."
    input_types = ["metrics"]
    output_types = ["embedding_summary", "statistics"]
    requires = ["data_loader"]
    tags = ["verification", "embedding"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")
        params = params or {}

        texts = self._collect_texts(run, params)
        if not texts:
            return {
                "summary": {},
                "statistics": {},
                "insights": ["No texts available for embedding analysis."],
            }

        embeddings, meta, errors = self._compute_embeddings(texts, params)
        if embeddings is None:
            return {
                "summary": {
                    "backend": meta.get("backend", "unavailable"),
                    "errors": errors,
                },
                "statistics": {},
                "insights": ["Embedding backend is not available."],
            }

        norms = np.linalg.norm(embeddings, axis=1)
        mean_vector = embeddings.mean(axis=0)
        mean_norm = float(np.linalg.norm(mean_vector))
        if mean_norm == 0:
            cosine_to_mean = np.zeros(len(embeddings))
        else:
            cosine_to_mean = (embeddings @ mean_vector) / (norms * mean_norm)

        norm_mean = float(np.mean(norms)) if norms.size else 0.0
        norm_std = float(np.std(norms)) if norms.size else 0.0
        norm_min = float(np.min(norms)) if norms.size else 0.0
        norm_max = float(np.max(norms)) if norms.size else 0.0
        cosine_mean = float(np.mean(cosine_to_mean)) if cosine_to_mean.size else 0.0

        summary = {
            "backend": meta.get("backend"),
            "model": meta.get("model"),
            "dimension": meta.get("dimension"),
            "sample_count": len(texts),
            "avg_norm": round(norm_mean, 4),
            "norm_std": round(norm_std, 4),
            "norm_min": round(norm_min, 4),
            "norm_max": round(norm_max, 4),
            "mean_cosine_to_centroid": round(cosine_mean, 4),
        }
        if errors:
            summary["errors"] = errors

        insights = []
        if norm_std < 0.01:
            insights.append("Embedding norms have very low variance.")
        if cosine_mean > 0.98:
            insights.append("Embeddings appear highly clustered toward a single direction.")

        return {
            "summary": summary,
            "statistics": {
                "norms": norms[:200].tolist(),
                "cosine_to_centroid": cosine_to_mean[:200].tolist(),
            },
            "insights": insights,
        }

    def _collect_texts(
        self,
        run: EvaluationRun | None,
        params: dict[str, Any],
    ) -> list[str]:
        if not isinstance(run, EvaluationRun):
            return []

        max_questions = int(params.get("max_questions", 100))
        max_contexts = int(params.get("max_contexts", 200))

        questions = [result.question for result in run.results if result.question][:max_questions]
        contexts: list[str] = []
        for result in run.results:
            for context in result.contexts or []:
                if context:
                    contexts.append(context)
                if len(contexts) >= max_contexts:
                    break
            if len(contexts) >= max_contexts:
                break

        return questions + contexts

    def _compute_embeddings(
        self,
        texts: list[str],
        params: dict[str, Any],
    ) -> tuple[np.ndarray | None, dict[str, Any], list[str]]:
        errors: list[str] = []
        backend_hint = params.get("backend")
        embedding_profile = params.get("embedding_profile")
        model_name = params.get("model_name")
        matryoshka_dim = params.get("matryoshka_dim")
        batch_size = params.get("batch_size")

        if backend_hint == "tfidf":
            return self._compute_tfidf_embeddings(texts, errors)

        retriever = None
        settings = Settings()

        if backend_hint == "ollama" or embedding_profile in {"dev", "prod"}:
            try:
                from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter

                adapter = OllamaAdapter(settings)
                retriever = KoreanDenseRetriever(
                    model_name=model_name or settings.ollama_embedding_model,
                    ollama_adapter=adapter,
                    matryoshka_dim=matryoshka_dim,
                    profile=embedding_profile,
                )
            except Exception as exc:
                errors.append(str(exc))
                retriever = None

        if retriever is None and (backend_hint == "vllm" or embedding_profile == "vllm"):
            try:
                from evalvault.adapters.outbound.llm.vllm_adapter import VLLMAdapter

                adapter = VLLMAdapter(settings)
                retriever = KoreanDenseRetriever(
                    model_name=model_name or settings.vllm_embedding_model,
                    ollama_adapter=adapter,
                    profile=embedding_profile,
                )
            except Exception as exc:
                errors.append(str(exc))
                retriever = None

        if retriever is None and backend_hint != "ollama":
            try:
                retriever = KoreanDenseRetriever(model_name=model_name)
            except Exception as exc:
                errors.append(str(exc))
                retriever = None

        if retriever is not None:
            try:
                embeddings = retriever.encode(
                    texts,
                    batch_size=batch_size if isinstance(batch_size, int) else None,
                )
                meta = {
                    "backend": "vllm"
                    if backend_hint == "vllm" or embedding_profile == "vllm"
                    else "ollama"
                    if retriever.model_name.startswith("qwen3")
                    else "sentence-transformers",
                    "model": retriever.model_name,
                    "dimension": retriever.dimension,
                }
                return embeddings, meta, errors
            except Exception as exc:
                errors.append(str(exc))

        return self._compute_tfidf_embeddings(texts, errors)

    def _compute_tfidf_embeddings(
        self,
        texts: list[str],
        errors: list[str],
    ) -> tuple[np.ndarray | None, dict[str, Any], list[str]]:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
        except Exception as exc:  # pragma: no cover - optional dependency
            errors.append(str(exc))
            return None, {"backend": "tfidf"}, errors

        vectorizer = TfidfVectorizer(max_features=2048)
        matrix = vectorizer.fit_transform(texts)
        embeddings = matrix.toarray().astype(np.float32)
        meta = {
            "backend": "tfidf",
            "model": "tfidf",
            "dimension": embeddings.shape[1],
            "vocab_size": len(vectorizer.vocabulary_),
        }
        return embeddings, meta, errors
