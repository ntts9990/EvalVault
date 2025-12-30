"""한국어 NLP 포트 인터페이스.

한국어 자연어 처리를 위한 추상 인터페이스를 정의합니다.
"""

from __future__ import annotations

from abc import abstractmethod
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
