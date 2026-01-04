"""Korean BM25 Retriever with morphological analysis.

한국어 형태소 분석을 활용한 BM25 검색을 제공합니다.

Example:
    >>> from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer
    >>> from evalvault.adapters.outbound.nlp.korean.bm25_retriever import KoreanBM25Retriever
    >>> tokenizer = KiwiTokenizer()
    >>> retriever = KoreanBM25Retriever(tokenizer)
    >>> retriever.index(["보험료 납입 기간은 20년입니다.", "보장금액은 1억원입니다."])
    >>> results = retriever.search("보험료 기간", top_k=1)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from evalvault.config.phoenix_support import instrumentation_span, set_span_attributes

if TYPE_CHECKING:
    from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer

logger = logging.getLogger(__name__)
_FALLBACK_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


@dataclass
class RetrievalResult:
    """검색 결과.

    Attributes:
        document: 검색된 문서 텍스트
        score: BM25 점수
        doc_id: 문서 인덱스
        tokens: 문서의 토큰 리스트 (디버깅용)
    """

    document: str
    score: float
    doc_id: int
    tokens: list[str] | None = None


class KoreanBM25Retriever:
    """한국어 형태소 분석 기반 BM25 검색기.

    Kiwi 형태소 분석기를 사용하여 조사/어미를 제거한 후
    BM25 알고리즘으로 검색합니다.

    Attributes:
        tokenizer: KiwiTokenizer 인스턴스
        k1: BM25 k1 파라미터 (기본: 1.5)
        b: BM25 b 파라미터 (기본: 0.75)

    Example:
        >>> retriever = KoreanBM25Retriever(tokenizer)
        >>> retriever.index(documents)
        >>> results = retriever.search("보험료 납입", top_k=5)
    """

    def __init__(
        self,
        tokenizer: KiwiTokenizer,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        """KoreanBM25Retriever 초기화.

        Args:
            tokenizer: 한국어 토크나이저
            k1: BM25 k1 파라미터 (term frequency 포화)
            b: BM25 b 파라미터 (문서 길이 정규화)
        """
        self._tokenizer = tokenizer
        self._k1 = k1
        self._b = b
        self._bm25 = None
        self._documents: list[str] = []
        self._tokenized_docs: list[list[str]] = []

    @property
    def is_indexed(self) -> bool:
        """인덱스가 구축되었는지 확인."""
        return self._bm25 is not None

    @property
    def document_count(self) -> int:
        """인덱싱된 문서 수."""
        return len(self._documents)

    def index(self, documents: list[str]) -> int:
        """문서를 인덱싱합니다.

        형태소 분석을 수행하여 BM25 인덱스를 구축합니다.

        Args:
            documents: 인덱싱할 문서 리스트

        Returns:
            인덱싱된 문서 수

        Raises:
            ImportError: rank-bm25가 설치되지 않은 경우
        """
        span_attrs = {"retriever.documents": len(documents), "retriever.type": "bm25"}
        with instrumentation_span("retriever.bm25.index", span_attrs) as span:
            try:
                from rank_bm25 import BM25Okapi
            except ImportError as e:
                raise ImportError(
                    "rank-bm25가 설치되지 않았습니다. "
                    "'uv add rank-bm25' 또는 'pip install rank-bm25'로 설치하세요."
                ) from e

            if not documents:
                logger.warning("빈 문서 리스트로 인덱싱 시도")
                return 0

            self._documents = documents
            tokenized_docs: list[list[str]] = []
            for doc in documents:
                tokens = self._tokenizer.tokenize(doc)
                if not tokens:
                    tokens = self._fallback_tokenize(doc)
                tokenized_docs.append(tokens)
            self._tokenized_docs = tokenized_docs

            # 빈 토큰 리스트 처리
            self._tokenized_docs = [tokens if tokens else [""] for tokens in self._tokenized_docs]

            self._bm25 = BM25Okapi(
                self._tokenized_docs,
                k1=self._k1,
                b=self._b,
            )

            if span:
                set_span_attributes(
                    span,
                    {"retriever.tokenizer": self._tokenizer.__class__.__name__},
                )

            logger.info(f"BM25 인덱스 구축 완료: {len(documents)}개 문서")
            return len(documents)

    def search(
        self,
        query: str,
        top_k: int = 5,
        include_tokens: bool = False,
    ) -> list[RetrievalResult]:
        """쿼리로 문서를 검색합니다.

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            include_tokens: 결과에 토큰 포함 여부

        Returns:
            검색 결과 리스트 (점수 내림차순)

        Raises:
            ValueError: 인덱스가 구축되지 않은 경우
        """
        span_attrs = {
            "retriever.type": "bm25",
            "retriever.query.length": len(query or ""),
            "retriever.top_k": top_k,
        }
        if not self.is_indexed:
            raise ValueError("인덱스가 구축되지 않았습니다. index()를 먼저 호출하세요.")

        with instrumentation_span("retriever.bm25.search", span_attrs) as span:
            # 쿼리 토큰화
            query_tokens = self._tokenizer.tokenize(query)
            if not query_tokens:
                query_tokens = self._fallback_tokenize(query)
            if not query_tokens:
                logger.warning(f"쿼리에서 토큰을 추출할 수 없음: {query}")
                return []

            # BM25 점수 계산
            scores = self._bm25.get_scores(query_tokens)

            # 상위 k개 인덱스
            top_indices = scores.argsort()[::-1][:top_k]

            results = []
            for idx in top_indices:
                idx = int(idx)
                score = float(scores[idx])

                result = RetrievalResult(
                    document=self._documents[idx],
                    score=score,
                    doc_id=idx,
                    tokens=self._tokenized_docs[idx] if include_tokens else None,
                )
                results.append(result)

            if span:
                set_span_attributes(span, {"retriever.result_count": len(results)})

            return results

    def _fallback_tokenize(self, text: str) -> list[str]:
        if not text:
            return []
        return [token.lower() for token in _FALLBACK_TOKEN_PATTERN.findall(text)]

    def search_with_scores(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """쿼리로 검색하고 (문서, 점수) 튜플 반환.

        간단한 사용을 위한 편의 메서드.

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수

        Returns:
            (문서, 점수) 튜플 리스트
        """
        results = self.search(query, top_k=top_k)
        return [(r.document, r.score) for r in results]

    def get_document_tokens(self, doc_id: int) -> list[str]:
        """특정 문서의 토큰을 반환합니다.

        Args:
            doc_id: 문서 인덱스

        Returns:
            토큰 리스트
        """
        if not 0 <= doc_id < len(self._tokenized_docs):
            raise IndexError(f"유효하지 않은 doc_id: {doc_id}")
        return self._tokenized_docs[doc_id]

    def add_documents(self, documents: list[str]) -> int:
        """문서를 추가하고 인덱스를 재구축합니다.

        Args:
            documents: 추가할 문서 리스트

        Returns:
            전체 인덱싱된 문서 수
        """
        all_docs = self._documents + documents
        return self.index(all_docs)

    def clear(self) -> None:
        """인덱스를 초기화합니다."""
        self._bm25 = None
        self._documents = []
        self._tokenized_docs = []
        logger.info("BM25 인덱스 초기화")
