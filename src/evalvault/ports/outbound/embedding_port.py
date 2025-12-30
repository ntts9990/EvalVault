"""Embedding port interface.

임베딩 생성을 위한 추상 인터페이스를 정의합니다.
Dense retrieval, semantic similarity 등에 활용됩니다.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol


@dataclass
class EmbeddingResult:
    """임베딩 결과.

    Attributes:
        embeddings: Dense 임베딩 벡터 (texts 순서와 동일)
        dimension: 임베딩 차원
        model_name: 사용된 모델 이름
    """

    embeddings: list[list[float]]
    dimension: int
    model_name: str


class EmbeddingPort(Protocol):
    """임베딩 생성 포트.

    Dense embedding을 생성하는 인터페이스입니다.
    BGE-M3, sentence-transformers 등이 구현할 수 있습니다.
    """

    @abstractmethod
    def encode(
        self,
        texts: list[str],
        *,
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> EmbeddingResult:
        """텍스트를 임베딩 벡터로 변환합니다.

        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기
            show_progress: 진행 상황 표시 여부

        Returns:
            EmbeddingResult 객체
        """
        ...

    @abstractmethod
    def encode_query(self, query: str) -> list[float]:
        """단일 쿼리를 임베딩합니다.

        일부 모델(예: BGE)은 쿼리와 문서에 다른 프롬프트를 사용합니다.
        이 메서드는 쿼리용 임베딩을 생성합니다.

        Args:
            query: 쿼리 텍스트

        Returns:
            임베딩 벡터
        """
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """임베딩 차원."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """모델 이름."""
        ...

    @property
    @abstractmethod
    def max_length(self) -> int:
        """최대 입력 토큰 수."""
        ...
