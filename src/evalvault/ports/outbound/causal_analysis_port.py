"""Causal analysis port interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from evalvault.domain.entities import EvaluationRun
    from evalvault.domain.entities.analysis import CausalAnalysis


class CausalAnalysisPort(Protocol):
    """인과 분석 포트 인터페이스.

    평가 결과에서 인과 관계를 분석하여 근본 원인을 파악하고
    개선 제안을 생성합니다.
    """

    def analyze_causality(
        self,
        run: EvaluationRun,
        *,
        min_samples: int = 10,
        significance_level: float = 0.05,
    ) -> CausalAnalysis:
        """인과 분석 수행.

        Args:
            run: 분석할 평가 실행
            min_samples: 분석에 필요한 최소 샘플 수
            significance_level: 유의 수준 (기본: 0.05)

        Returns:
            CausalAnalysis 결과
        """
        ...
