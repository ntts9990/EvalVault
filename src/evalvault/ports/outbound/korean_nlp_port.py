"""한국어 NLP 포트 인터페이스.

한국어 자연어 처리를 위한 추상 인터페이스를 정의합니다.

Ports:
    KoreanTokenizerPort: 토크나이저
    KoreanTextProcessorPort: 텍스트 처리
    KoreanRetrieverPort: 검색기
    KoreanChunkerPort: 문서 청킹
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol


class KoreanTokenizerPort(Protocol):
    """한국어 토크나이저 포트.

    한국어 텍스트의 토큰화, 형태소 분석, 키워드 추출을 위한 인터페이스입니다.
    """

    @abstractmethod
    def tokenize(self, text: str) -> list[str]:
        """텍스트를 토큰화합니다.

        Args:
            text: 토큰화할 텍스트

        Returns:
            토큰 리스트
        """
        ...

    @abstractmethod
    def extract_nouns(self, text: str) -> list[str]:
        """명사만 추출합니다.

        Args:
            text: 입력 텍스트

        Returns:
            명사 리스트
        """
        ...

    @abstractmethod
    def extract_keywords(
        self,
        text: str,
        pos_tags: set[str] | None = None,
    ) -> list[str]:
        """키워드 품사만 추출합니다.

        Args:
            text: 입력 텍스트
            pos_tags: 추출할 품사 태그 집합

        Returns:
            키워드 리스트
        """
        ...

    @abstractmethod
    def split_sentences(self, text: str) -> list[str]:
        """텍스트를 문장으로 분리합니다.

        Args:
            text: 입력 텍스트

        Returns:
            문장 리스트
        """
        ...

    @abstractmethod
    def get_pos_tags(self, text: str) -> list[tuple[str, str]]:
        """품사 태깅 결과를 반환합니다.

        Args:
            text: 입력 텍스트

        Returns:
            (토큰, 품사) 튜플 리스트
        """
        ...


class KoreanTextProcessorPort(Protocol):
    """한국어 텍스트 처리 포트.

    한국어 텍스트의 전처리, 정규화, 유사도 계산을 위한 인터페이스입니다.
    """

    @abstractmethod
    def normalize(self, text: str) -> str:
        """텍스트를 정규화합니다.

        Args:
            text: 입력 텍스트

        Returns:
            정규화된 텍스트
        """
        ...

    @abstractmethod
    def calculate_token_overlap(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """두 텍스트의 토큰 겹침 비율을 계산합니다.

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            겹침 비율 (0.0 ~ 1.0)
        """
        ...


@dataclass
class SearchResult:
    """검색 결과 데이터 클래스.

    Attributes:
        document: 검색된 문서 텍스트
        score: 검색 점수
        doc_id: 문서 식별자
    """

    document: str
    score: float
    doc_id: int | str


class KoreanRetrieverPort(Protocol):
    """한국어 검색기 포트.

    한국어 문서 검색을 위한 인터페이스입니다.
    BM25, Dense, 하이브리드 검색기 등이 구현할 수 있습니다.
    """

    @abstractmethod
    def index(self, documents: list[str]) -> int:
        """문서를 인덱싱합니다.

        Args:
            documents: 인덱싱할 문서 리스트

        Returns:
            인덱싱된 문서 수
        """
        ...

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """쿼리로 문서를 검색합니다.

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        ...

    @property
    @abstractmethod
    def is_indexed(self) -> bool:
        """인덱스가 구축되었는지 확인."""
        ...

    @property
    @abstractmethod
    def document_count(self) -> int:
        """인덱싱된 문서 수."""
        ...


@dataclass
class ChunkResult:
    """청크 결과 데이터 클래스.

    Attributes:
        text: 청크 텍스트
        token_count: 토큰 수
        start_idx: 시작 인덱스
        end_idx: 끝 인덱스
    """

    text: str
    token_count: int
    start_idx: int
    end_idx: int


class KoreanChunkerPort(Protocol):
    """한국어 문서 청커 포트.

    한국어 문서를 의미 단위로 분할하는 인터페이스입니다.
    """

    @abstractmethod
    def chunk(self, document: str) -> list[ChunkResult]:
        """문서를 청크로 분할합니다.

        Args:
            document: 입력 문서

        Returns:
            청크 결과 리스트
        """
        ...

    @abstractmethod
    def split_sentences(self, text: str) -> list[str]:
        """텍스트를 문장으로 분리합니다.

        Args:
            text: 입력 텍스트

        Returns:
            문장 리스트
        """
        ...

    @property
    @abstractmethod
    def chunk_size(self) -> int:
        """청크 크기 (토큰 수)."""
        ...

    @property
    @abstractmethod
    def overlap_tokens(self) -> int:
        """오버랩 토큰 수."""
        ...
