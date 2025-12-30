"""Phase 14: Intent Classifier Port (Outbound).

사용자 쿼리에서 분석 의도를 추출하는 포트 인터페이스입니다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from evalvault.domain.entities.analysis_pipeline import AnalysisIntent


@dataclass
class IntentClassificationResult:
    """의도 분류 결과.

    Attributes:
        intent: 분류된 의도
        confidence: 신뢰도 (0.0 ~ 1.0)
        keywords: 추출된 키워드 목록
        alternative_intents: 대안 의도 목록 (신뢰도 순)
    """

    intent: AnalysisIntent
    confidence: float
    keywords: list[str] = field(default_factory=list)
    alternative_intents: list[tuple[AnalysisIntent, float]] = field(default_factory=list)

    @property
    def is_confident(self) -> bool:
        """충분한 신뢰도 여부 (0.7 이상)."""
        return self.confidence >= 0.7

    @property
    def has_alternatives(self) -> bool:
        """대안 의도 존재 여부."""
        return len(self.alternative_intents) > 0


class IntentClassifierPort(Protocol):
    """의도 분류기 포트 인터페이스.

    사용자 쿼리를 분석하여 분석 의도를 추출합니다.
    키워드 기반 규칙 분류기 또는 LLM 기반 분류기가
    이 인터페이스를 구현합니다.
    """

    def classify(self, query: str) -> AnalysisIntent:
        """쿼리에서 의도를 분류합니다.

        Args:
            query: 사용자 분석 요청 쿼리

        Returns:
            분류된 분석 의도
        """
        ...

    def classify_with_confidence(self, query: str) -> IntentClassificationResult:
        """쿼리에서 의도를 분류하고 신뢰도를 반환합니다.

        Args:
            query: 사용자 분석 요청 쿼리

        Returns:
            분류 결과 (의도, 신뢰도, 키워드, 대안)
        """
        ...

    def extract_keywords(self, query: str) -> list[str]:
        """쿼리에서 핵심 키워드를 추출합니다.

        Args:
            query: 사용자 분석 요청 쿼리

        Returns:
            추출된 키워드 목록
        """
        ...
