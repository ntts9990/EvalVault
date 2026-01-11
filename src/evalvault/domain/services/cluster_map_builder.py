"""Cluster map generation utilities."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from evalvault.domain.entities import EvaluationRun, TestCaseResult
from evalvault.ports.outbound.llm_port import LLMPort

logger = logging.getLogger(__name__)


@dataclass
class ClusterMapBuildResult:
    """Generated cluster map payload."""

    mapping: dict[str, str]
    source: str
    metadata: dict[str, Any]


def _build_text(result: TestCaseResult, max_chars: int) -> str:
    parts: list[str] = []
    if result.question:
        parts.append(result.question)
    if result.answer:
        parts.append(result.answer)
    if result.contexts:
        parts.extend([ctx for ctx in result.contexts if ctx])
    text = " ".join(parts).strip()
    if not text:
        text = result.test_case_id
    if max_chars > 0 and len(text) > max_chars:
        text = text[:max_chars]
    return text


def _resolve_embedding_model_name(llm_adapter: LLMPort | None) -> str | None:
    if llm_adapter is None:
        return None
    name = None
    getter = getattr(llm_adapter, "get_embedding_model_name", None)
    if callable(getter):
        try:
            name = getter()
        except Exception:  # pragma: no cover - best effort only
            name = None
    if not name and hasattr(llm_adapter, "as_ragas_embeddings"):
        try:
            embeddings = llm_adapter.as_ragas_embeddings()
        except Exception:  # pragma: no cover - best effort only
            embeddings = None
        if embeddings is not None:
            name = getattr(embeddings, "model", None) or getattr(embeddings, "model_name", None)
    return name


def _embed_with_model(llm_adapter: LLMPort, texts: list[str]) -> list[list[float]] | None:
    try:
        embeddings = llm_adapter.as_ragas_embeddings()
    except Exception as exc:  # pragma: no cover - depends on external adapters
        logger.warning("Embedding backend unavailable: %s", exc)
        return None
    if embeddings is None:
        return None
    if hasattr(embeddings, "embed_documents"):
        return embeddings.embed_documents(texts)
    if hasattr(embeddings, "embed_texts"):
        return embeddings.embed_texts(texts)
    if hasattr(embeddings, "aembed_documents"):
        logger.warning("Async embedding method detected; falling back to tfidf.")
        return None
    return None


def _embed_with_tfidf(texts: list[str]) -> tuple[Any, dict[str, Any]]:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(max_features=4096)
    matrix = vectorizer.fit_transform(texts)
    meta = {"dimension": matrix.shape[1], "method": "tfidf"}
    return matrix.toarray().astype(np.float32), meta


def _cluster_embeddings(
    embeddings: Any,
    *,
    min_cluster_size: int,
    max_clusters: int,
) -> list[int]:
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - optional dependency
        logger.warning("NumPy not available for clustering: %s", exc)
        return [0] * len(embeddings)

    embeddings = np.asarray(embeddings, dtype=np.float32)
    sample_count = embeddings.shape[0]
    if sample_count < 2:
        return [0] * sample_count
    cluster_count = max(2, min(max_clusters, max(2, sample_count // max(1, min_cluster_size))))
    cluster_count = min(cluster_count, sample_count)
    if cluster_count < 2:
        return [0] * sample_count
    try:
        from sklearn.cluster import KMeans
    except ImportError as exc:  # pragma: no cover - optional dependency
        logger.warning("scikit-learn not available for clustering: %s", exc)
        return [0] * sample_count
    kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    return kmeans.fit_predict(embeddings).tolist()


def build_cluster_map(
    run: EvaluationRun,
    *,
    llm_adapter: LLMPort | None = None,
    embedding_mode: Literal["model", "tfidf"] = "tfidf",
    min_cluster_size: int = 3,
    max_clusters: int = 10,
    text_max_chars: int = 800,
) -> ClusterMapBuildResult | None:
    """Generate a cluster map for a run."""
    if not run.results:
        return None

    texts: list[str] = []
    ids: list[str] = []
    for result in run.results:
        ids.append(result.test_case_id)
        texts.append(_build_text(result, text_max_chars))

    if len(texts) < max(2, min_cluster_size):
        mapping = dict.fromkeys(ids, "0")
        return ClusterMapBuildResult(
            mapping=mapping,
            source="auto:single_cluster",
            metadata={"mode": "single", "count": len(ids)},
        )

    mode_used = embedding_mode
    embeddings: Any | None = None
    embed_meta: dict[str, Any] = {}

    if embedding_mode == "model":
        if llm_adapter is None:
            mode_used = "tfidf"
        else:
            raw_embeddings = _embed_with_model(llm_adapter, texts)
            if raw_embeddings:
                try:
                    import numpy as np
                except ImportError as exc:  # pragma: no cover - optional dependency
                    logger.warning("NumPy not available for model embeddings: %s", exc)
                    raw_embeddings = None
                if raw_embeddings:
                    embeddings = np.asarray(raw_embeddings, dtype=np.float32)
                    embed_meta = {
                        "method": "model",
                        "model": _resolve_embedding_model_name(llm_adapter),
                        "dimension": embeddings.shape[1] if embeddings.ndim == 2 else None,
                    }
            else:
                mode_used = "tfidf"

    if embeddings is None:
        try:
            embeddings, embed_meta = _embed_with_tfidf(texts)
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.warning("TF-IDF embedding failed: %s", exc)
            mapping = dict.fromkeys(ids, "0")
            return ClusterMapBuildResult(
                mapping=mapping,
                source="auto:fallback_single_cluster",
                metadata={"mode": "fallback", "error": str(exc)},
            )

    labels = _cluster_embeddings(
        embeddings,
        min_cluster_size=min_cluster_size,
        max_clusters=max_clusters,
    )
    mapping = {test_case_id: str(labels[idx]) for idx, test_case_id in enumerate(ids)}
    source = f"auto:{mode_used}:kmeans"
    if mode_used == "model":
        model_name = embed_meta.get("model")
        if model_name:
            source = f"auto:{mode_used}:{model_name}:kmeans"
    return ClusterMapBuildResult(
        mapping=mapping,
        source=source,
        metadata={
            "mode": mode_used,
            "min_cluster_size": min_cluster_size,
            "max_clusters": max_clusters,
            **embed_meta,
        },
    )
