"""Korean Hybrid Retriever combining BM25 and Dense search.

BM25(희소 검색)와 Dense(밀집 임베딩) 검색을 결합한 하이브리드 검색을 제공합니다.

Example:
    >>> from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer
    >>> from evalvault.adapters.outbound.nlp.korean.hybrid_retriever import KoreanHybridRetriever
    >>> tokenizer = KiwiTokenizer()
    >>> retriever = KoreanHybridRetriever(tokenizer, embedding_func=get_embeddings)
    >>> retriever.index(documents)
    >>> results = retriever.search("보험료 납입", top_k=5)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

from evalvault.adapters.outbound.nlp.korean.bm25_retriever import (
    KoreanBM25Retriever,
    RetrievalResult,
)
from evalvault.config.phoenix_support import instrumentation_span, set_span_attributes

if TYPE_CHECKING:
    from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer

logger = logging.getLogger(__name__)


class FusionMethod(Enum):
    """검색 결과 융합 방법."""

    RRF = "rrf"  # Reciprocal Rank Fusion
    WEIGHTED_SUM = "weighted_sum"  # 가중 합
    NORMALIZED_SUM = "normalized_sum"  # 정규화 후 합


@dataclass
class HybridResult:
    """하이브리드 검색 결과.

    Attributes:
        document: 검색된 문서 텍스트
        score: 최종 융합 점수
        doc_id: 문서 인덱스
        bm25_score: BM25 점수
        dense_score: Dense 유사도 점수
        bm25_rank: BM25 순위 (1-based)
        dense_rank: Dense 순위 (1-based)
    """

    document: str
    score: float
    doc_id: int
    bm25_score: float = 0.0
    dense_score: float = 0.0
    bm25_rank: int = 0
    dense_rank: int = 0
    metadata: dict = field(default_factory=dict)


# Type alias for embedding function
EmbeddingFunc = Callable[[list[str]], list[list[float]]]


class KoreanHybridRetriever:
    """한국어 하이브리드 검색기.

    BM25(희소)와 Dense(밀집) 검색을 결합하여 정확한 용어 매칭과
    의미적 유사도를 모두 활용합니다.

    Attributes:
        tokenizer: KiwiTokenizer 인스턴스
        embedding_func: 임베딩 생성 함수
        bm25_weight: BM25 점수 가중치 (기본: 0.5)
        dense_weight: Dense 점수 가중치 (기본: 0.5)
        fusion_method: 결과 융합 방법

    Example:
        >>> retriever = KoreanHybridRetriever(
        ...     tokenizer=tokenizer,
        ...     embedding_func=lambda texts: model.encode(texts),
        ...     bm25_weight=0.4,
        ...     dense_weight=0.6,
        ... )
        >>> retriever.index(documents)
        >>> results = retriever.search("보험 가입 조건", top_k=10)
    """

    def __init__(
        self,
        tokenizer: KiwiTokenizer,
        embedding_func: EmbeddingFunc | None = None,
        bm25_weight: float = 0.5,
        dense_weight: float = 0.5,
        fusion_method: FusionMethod = FusionMethod.RRF,
        rrf_k: int = 60,
    ) -> None:
        """KoreanHybridRetriever 초기화.

        Args:
            tokenizer: 한국어 토크나이저
            embedding_func: 텍스트를 임베딩 벡터로 변환하는 함수
            bm25_weight: BM25 점수 가중치 (fusion_method=WEIGHTED_SUM 시 사용)
            dense_weight: Dense 점수 가중치
            fusion_method: 결과 융합 방법
            rrf_k: RRF 파라미터 (기본: 60)
        """
        self._tokenizer = tokenizer
        self._embedding_func = embedding_func
        self._bm25_weight = bm25_weight
        self._dense_weight = dense_weight
        self._fusion_method = fusion_method
        self._rrf_k = rrf_k

        # BM25 검색기
        self._bm25_retriever = KoreanBM25Retriever(tokenizer)

        # Dense 검색용 저장소
        self._documents: list[str] = []
        self._embeddings: np.ndarray | None = None

    @property
    def is_indexed(self) -> bool:
        """인덱스가 구축되었는지 확인."""
        return self._bm25_retriever.is_indexed

    @property
    def has_embeddings(self) -> bool:
        """임베딩이 계산되었는지 확인."""
        return self._embeddings is not None

    @property
    def document_count(self) -> int:
        """인덱싱된 문서 수."""
        return len(self._documents)

    def index(
        self,
        documents: list[str],
        compute_embeddings: bool = True,
    ) -> int:
        """문서를 인덱싱합니다.

        BM25 인덱스를 구축하고, 임베딩 함수가 있으면 Dense 임베딩도 계산합니다.

        Args:
            documents: 인덱싱할 문서 리스트
            compute_embeddings: 임베딩 계산 여부

        Returns:
            인덱싱된 문서 수
        """
        if not documents:
            logger.warning("빈 문서 리스트로 인덱싱 시도")
            return 0

        span_attrs = {
            "retriever.type": "hybrid",
            "retriever.documents": len(documents),
            "retriever.fusion": self._fusion_method.value,
        }
        with instrumentation_span("retriever.hybrid.index", span_attrs) as span:
            self._documents = documents

            # BM25 인덱스 구축
            self._bm25_retriever.index(documents)

            # Dense 임베딩 계산
            if compute_embeddings and self._embedding_func is not None:
                try:
                    embeddings = self._embedding_func(documents)
                    self._embeddings = np.array(embeddings)
                    logger.info(f"Dense 임베딩 계산 완료: {len(documents)}개 문서")
                except Exception as e:
                    logger.warning(f"임베딩 계산 실패: {e}")
                    self._embeddings = None

            if span and self._embeddings is not None:
                set_span_attributes(
                    span,
                    {"retriever.embedding_dim": int(self._embeddings.shape[1])},
                )

            return len(documents)

    def search(
        self,
        query: str,
        top_k: int = 5,
        use_bm25: bool = True,
        use_dense: bool = True,
    ) -> list[HybridResult]:
        """하이브리드 검색을 수행합니다.

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            use_bm25: BM25 검색 사용 여부
            use_dense: Dense 검색 사용 여부

        Returns:
            하이브리드 검색 결과 리스트

        Raises:
            ValueError: 인덱스가 구축되지 않은 경우
        """
        if not self.is_indexed:
            raise ValueError("인덱스가 구축되지 않았습니다. index()를 먼저 호출하세요.")

        span_attrs = {
            "retriever.type": "hybrid",
            "retriever.top_k": top_k,
            "retriever.use_bm25": use_bm25,
            "retriever.use_dense": use_dense,
        }
        with instrumentation_span("retriever.hybrid.search", span_attrs) as span:
            # 검색 실행
            bm25_results: list[RetrievalResult] = []
            dense_results: list[tuple[int, float]] = []

            if use_bm25:
                bm25_results = self._bm25_retriever.search(query, top_k=len(self._documents))

            if use_dense and self.has_embeddings and self._embedding_func is not None:
                dense_results = self._search_dense(query)

            # 결과 융합
            if use_bm25 and use_dense and bm25_results and dense_results:
                fused = self._fuse_results(bm25_results, dense_results, top_k)
            elif use_bm25 and bm25_results:
                fused = self._convert_bm25_results(bm25_results[:top_k])
            elif use_dense and dense_results:
                fused = self._convert_dense_results(dense_results[:top_k])
            else:
                fused = []

            if span:
                set_span_attributes(span, {"retriever.result_count": len(fused)})

            return fused

    def _search_dense(self, query: str) -> list[tuple[int, float]]:
        """Dense 검색을 수행합니다.

        Args:
            query: 검색 쿼리

        Returns:
            (doc_id, similarity) 리스트 (유사도 내림차순)
        """
        if self._embedding_func is None or self._embeddings is None:
            return []

        try:
            # 쿼리 임베딩
            query_embedding = self._embedding_func([query])[0]
            query_vec = np.array(query_embedding)

            # 코사인 유사도 계산
            similarities = self._cosine_similarity(query_vec, self._embeddings)

            # 정렬
            sorted_indices = np.argsort(similarities)[::-1]

            return [(int(idx), float(similarities[idx])) for idx in sorted_indices]

        except Exception as e:
            logger.warning(f"Dense 검색 실패: {e}")
            return []

    def _cosine_similarity(
        self,
        query_vec: np.ndarray,
        doc_vecs: np.ndarray,
    ) -> np.ndarray:
        """코사인 유사도를 계산합니다."""
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return np.zeros(len(doc_vecs))

        doc_norms = np.linalg.norm(doc_vecs, axis=1)
        doc_norms[doc_norms == 0] = 1  # 0으로 나누기 방지

        similarities = np.dot(doc_vecs, query_vec) / (doc_norms * query_norm)
        return similarities

    def _fuse_results(
        self,
        bm25_results: list[RetrievalResult],
        dense_results: list[tuple[int, float]],
        top_k: int,
    ) -> list[HybridResult]:
        """BM25와 Dense 결과를 융합합니다."""
        if self._fusion_method == FusionMethod.RRF:
            return self._fuse_rrf(bm25_results, dense_results, top_k)
        elif self._fusion_method == FusionMethod.WEIGHTED_SUM:
            return self._fuse_weighted(bm25_results, dense_results, top_k)
        else:  # NORMALIZED_SUM
            return self._fuse_normalized(bm25_results, dense_results, top_k)

    def _fuse_rrf(
        self,
        bm25_results: list[RetrievalResult],
        dense_results: list[tuple[int, float]],
        top_k: int,
    ) -> list[HybridResult]:
        """Reciprocal Rank Fusion으로 결과 융합.

        RRF Score = sum(1 / (k + rank))
        """
        scores: dict[int, dict] = {}

        # BM25 랭크 점수
        for rank, result in enumerate(bm25_results, 1):
            doc_id = result.doc_id
            if doc_id not in scores:
                scores[doc_id] = {
                    "bm25_score": 0,
                    "dense_score": 0,
                    "bm25_rank": 0,
                    "dense_rank": 0,
                    "rrf_score": 0,
                }
            scores[doc_id]["bm25_score"] = result.score
            scores[doc_id]["bm25_rank"] = rank
            scores[doc_id]["rrf_score"] += self._bm25_weight / (self._rrf_k + rank)

        # Dense 랭크 점수
        for rank, (doc_id, similarity) in enumerate(dense_results, 1):
            if doc_id not in scores:
                scores[doc_id] = {
                    "bm25_score": 0,
                    "dense_score": 0,
                    "bm25_rank": 0,
                    "dense_rank": 0,
                    "rrf_score": 0,
                }
            scores[doc_id]["dense_score"] = similarity
            scores[doc_id]["dense_rank"] = rank
            scores[doc_id]["rrf_score"] += self._dense_weight / (self._rrf_k + rank)

        # 정렬 및 결과 생성
        sorted_docs = sorted(scores.items(), key=lambda x: x[1]["rrf_score"], reverse=True)

        results = []
        for doc_id, score_info in sorted_docs[:top_k]:
            results.append(
                HybridResult(
                    document=self._documents[doc_id],
                    score=score_info["rrf_score"],
                    doc_id=doc_id,
                    bm25_score=score_info["bm25_score"],
                    dense_score=score_info["dense_score"],
                    bm25_rank=score_info["bm25_rank"],
                    dense_rank=score_info["dense_rank"],
                )
            )

        return results

    def _fuse_weighted(
        self,
        bm25_results: list[RetrievalResult],
        dense_results: list[tuple[int, float]],
        top_k: int,
    ) -> list[HybridResult]:
        """가중 합으로 결과 융합."""
        scores: dict[int, dict] = {}

        # BM25 점수 수집
        for rank, result in enumerate(bm25_results, 1):
            doc_id = result.doc_id
            if doc_id not in scores:
                scores[doc_id] = {
                    "bm25_score": 0,
                    "dense_score": 0,
                    "bm25_rank": rank,
                    "dense_rank": 0,
                }
            scores[doc_id]["bm25_score"] = result.score
            scores[doc_id]["bm25_rank"] = rank

        # Dense 점수 수집
        for rank, (doc_id, similarity) in enumerate(dense_results, 1):
            if doc_id not in scores:
                scores[doc_id] = {
                    "bm25_score": 0,
                    "dense_score": 0,
                    "bm25_rank": 0,
                    "dense_rank": rank,
                }
            scores[doc_id]["dense_score"] = similarity
            scores[doc_id]["dense_rank"] = rank

        # 가중 합 계산
        for doc_id in scores:
            weighted = (
                self._bm25_weight * scores[doc_id]["bm25_score"]
                + self._dense_weight * scores[doc_id]["dense_score"]
            )
            scores[doc_id]["weighted_score"] = weighted

        # 정렬 및 결과 생성
        sorted_docs = sorted(scores.items(), key=lambda x: x[1]["weighted_score"], reverse=True)

        results = []
        for doc_id, score_info in sorted_docs[:top_k]:
            results.append(
                HybridResult(
                    document=self._documents[doc_id],
                    score=score_info["weighted_score"],
                    doc_id=doc_id,
                    bm25_score=score_info["bm25_score"],
                    dense_score=score_info["dense_score"],
                    bm25_rank=score_info["bm25_rank"],
                    dense_rank=score_info["dense_rank"],
                )
            )

        return results

    def _fuse_normalized(
        self,
        bm25_results: list[RetrievalResult],
        dense_results: list[tuple[int, float]],
        top_k: int,
    ) -> list[HybridResult]:
        """정규화 후 합으로 결과 융합."""
        # BM25 점수 정규화
        bm25_scores = [r.score for r in bm25_results]
        bm25_min, bm25_max = (
            min(bm25_scores) if bm25_scores else 0,
            max(bm25_scores) if bm25_scores else 1,
        )
        bm25_range = bm25_max - bm25_min if bm25_max != bm25_min else 1

        # Dense 점수 정규화 (이미 0-1 범위일 수 있음)
        dense_scores = [s for _, s in dense_results]
        dense_min, dense_max = (
            min(dense_scores) if dense_scores else 0,
            max(dense_scores) if dense_scores else 1,
        )
        dense_range = dense_max - dense_min if dense_max != dense_min else 1

        scores: dict[int, dict] = {}

        # 정규화된 BM25 점수
        for rank, result in enumerate(bm25_results, 1):
            doc_id = result.doc_id
            normalized = (result.score - bm25_min) / bm25_range
            if doc_id not in scores:
                scores[doc_id] = {
                    "bm25_score": 0,
                    "dense_score": 0,
                    "bm25_norm": 0,
                    "dense_norm": 0,
                    "bm25_rank": 0,
                    "dense_rank": 0,
                }
            scores[doc_id]["bm25_score"] = result.score
            scores[doc_id]["bm25_norm"] = normalized
            scores[doc_id]["bm25_rank"] = rank

        # 정규화된 Dense 점수
        for rank, (doc_id, similarity) in enumerate(dense_results, 1):
            normalized = (similarity - dense_min) / dense_range
            if doc_id not in scores:
                scores[doc_id] = {
                    "bm25_score": 0,
                    "dense_score": 0,
                    "bm25_norm": 0,
                    "dense_norm": 0,
                    "bm25_rank": 0,
                    "dense_rank": 0,
                }
            scores[doc_id]["dense_score"] = similarity
            scores[doc_id]["dense_norm"] = normalized
            scores[doc_id]["dense_rank"] = rank

        # 정규화된 점수의 가중 합
        for doc_id in scores:
            normalized_sum = (
                self._bm25_weight * scores[doc_id]["bm25_norm"]
                + self._dense_weight * scores[doc_id]["dense_norm"]
            )
            scores[doc_id]["final_score"] = normalized_sum

        # 정렬 및 결과 생성
        sorted_docs = sorted(scores.items(), key=lambda x: x[1]["final_score"], reverse=True)

        results = []
        for doc_id, score_info in sorted_docs[:top_k]:
            results.append(
                HybridResult(
                    document=self._documents[doc_id],
                    score=score_info["final_score"],
                    doc_id=doc_id,
                    bm25_score=score_info["bm25_score"],
                    dense_score=score_info["dense_score"],
                    bm25_rank=score_info["bm25_rank"],
                    dense_rank=score_info["dense_rank"],
                )
            )

        return results

    def _convert_bm25_results(self, results: list[RetrievalResult]) -> list[HybridResult]:
        """BM25 결과를 HybridResult로 변환."""
        return [
            HybridResult(
                document=r.document,
                score=r.score,
                doc_id=r.doc_id,
                bm25_score=r.score,
                bm25_rank=i + 1,
            )
            for i, r in enumerate(results)
        ]

    def _convert_dense_results(self, results: list[tuple[int, float]]) -> list[HybridResult]:
        """Dense 결과를 HybridResult로 변환."""
        return [
            HybridResult(
                document=self._documents[doc_id],
                score=similarity,
                doc_id=doc_id,
                dense_score=similarity,
                dense_rank=i + 1,
            )
            for i, (doc_id, similarity) in enumerate(results)
        ]

    def search_bm25_only(self, query: str, top_k: int = 5) -> list[HybridResult]:
        """BM25만 사용한 검색.

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        return self.search(query, top_k=top_k, use_bm25=True, use_dense=False)

    def search_dense_only(self, query: str, top_k: int = 5) -> list[HybridResult]:
        """Dense만 사용한 검색.

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        return self.search(query, top_k=top_k, use_bm25=False, use_dense=True)

    def clear(self) -> None:
        """인덱스를 초기화합니다."""
        self._bm25_retriever.clear()
        self._documents = []
        self._embeddings = None
        logger.info("하이브리드 인덱스 초기화")
