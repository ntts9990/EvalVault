"""Korean NLP toolkit adapter implementing outbound ports."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from evalvault.adapters.outbound.nlp.korean import (
    FusionMethod,
    KiwiTokenizer,
    KoreanBM25Retriever,
    KoreanDenseRetriever,
    KoreanFaithfulnessChecker,
    KoreanHybridRetriever,
)
from evalvault.ports.outbound.korean_nlp_port import (
    KoreanNLPToolkitPort,
    RetrieverPort,
    RetrieverResultProtocol,
)

logger = logging.getLogger(__name__)


class _RetrieverWrapper(RetrieverPort):
    """Adapter wrapper that exposes a unified retriever interface."""

    def __init__(self, retriever: Any):
        self._retriever = retriever

    def search(self, query: str, top_k: int = 5) -> Sequence[RetrieverResultProtocol]:
        return self._retriever.search(query, top_k=top_k)


class KoreanNLPToolkit(KoreanNLPToolkitPort):
    """Concrete implementation of KoreanNLPToolkitPort."""

    def __init__(self) -> None:
        self._tokenizer: KiwiTokenizer | None = None
        self._faithfulness_checker: KoreanFaithfulnessChecker | None = None

    def _ensure_tokenizer(self) -> KiwiTokenizer:
        if self._tokenizer is None:
            self._tokenizer = KiwiTokenizer()
        return self._tokenizer

    def _ensure_faithfulness_checker(self) -> KoreanFaithfulnessChecker:
        if self._faithfulness_checker is None:
            self._faithfulness_checker = KoreanFaithfulnessChecker(
                tokenizer=self._ensure_tokenizer()
            )
        return self._faithfulness_checker

    def extract_keywords(self, text: str) -> Sequence[str]:
        tokenizer = self._ensure_tokenizer()
        return tokenizer.extract_keywords(text)

    def check_faithfulness(
        self,
        answer: str,
        contexts: Sequence[str],
    ):
        checker = self._ensure_faithfulness_checker()
        return checker.check_faithfulness(answer=answer, contexts=list(contexts))

    def _build_hybrid_retriever(
        self,
        documents: Sequence[str],
        *,
        ollama_adapter: Any | None,
        embedding_profile: str | None,
        verbose: bool,
    ) -> RetrieverPort | None:
        tokenizer = self._ensure_tokenizer()

        embedding_func = None
        try:
            if embedding_profile == "vllm":
                from evalvault.adapters.outbound.llm.vllm_adapter import VLLMAdapter
                from evalvault.config.settings import Settings

                settings = Settings()
                adapter = ollama_adapter or VLLMAdapter(settings)
                dense_retriever = KoreanDenseRetriever(
                    model_name=settings.vllm_embedding_model,
                    ollama_adapter=adapter,
                )
            else:
                dense_retriever = KoreanDenseRetriever(
                    profile=embedding_profile,
                    ollama_adapter=ollama_adapter,
                )
            embedding_func = dense_retriever.get_embedding_func()
            if verbose:
                logger.info(
                    "Initialized KoreanDenseRetriever model=%s dim=%s",
                    dense_retriever.model_name,
                    dense_retriever.dimension,
                )
        except Exception as exc:  # pragma: no cover - runtime dependency
            logger.warning("Failed to initialize dense retriever: %s", exc)
            embedding_func = None

        retriever = KoreanHybridRetriever(
            tokenizer=tokenizer,
            embedding_func=embedding_func,
            bm25_weight=0.4,
            dense_weight=0.6,
            fusion_method=FusionMethod.RRF,
        )
        retriever.index(list(documents), compute_embeddings=embedding_func is not None)
        return _RetrieverWrapper(retriever)

    def _build_bm25_retriever(self, documents: Sequence[str]) -> RetrieverPort | None:
        tokenizer = self._ensure_tokenizer()
        retriever = KoreanBM25Retriever(tokenizer=tokenizer)
        retriever.index(list(documents))
        return _RetrieverWrapper(retriever)

    def build_retriever(
        self,
        documents: Sequence[str],
        *,
        use_hybrid: bool,
        ollama_adapter: Any | None = None,
        embedding_profile: str | None = None,
        verbose: bool = False,
    ) -> RetrieverPort | None:
        if not documents:
            return None
        if use_hybrid:
            return self._build_hybrid_retriever(
                documents,
                ollama_adapter=ollama_adapter,
                embedding_profile=embedding_profile,
                verbose=verbose,
            )
        return self._build_bm25_retriever(documents)


__all__ = ["KoreanNLPToolkit"]
