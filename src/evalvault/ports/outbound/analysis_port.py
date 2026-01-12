"""분석 서비스 인터페이스."""

from typing import TYPE_CHECKING, Literal, Protocol

from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.analysis import (
    ComparisonResult,
    StatisticalAnalysis,
)

if TYPE_CHECKING:
    pass


class AnalysisPort(Protocol):
    """평가 결과 분석을 위한 포트 인터페이스.

    통계 분석, NLP 분석, 인과 분석 등 다양한 분석 기능을 제공합니다.
    """

    def analyze_statistics(
        self,
        run: EvaluationRun,
        *,
        include_correlations: bool = True,
        include_low_performers: bool = True,
        low_performer_threshold: float = 0.5,
    ) -> StatisticalAnalysis:
        """통계 분석을 수행합니다.

        Args:
            run: 분석할 평가 실행 결과
            include_correlations: 상관관계 분석 포함 여부
            include_low_performers: 낮은 성능 케이스 분석 포함 여부
            low_performer_threshold: 낮은 성능 기준 점수

        Returns:
            StatisticalAnalysis 객체
        """
        ...

    def compare_runs(
        self,
        run_a: EvaluationRun,
        run_b: EvaluationRun,
        metrics: list[str] | None = None,
        test_type: Literal["t-test", "mann-whitney"] = "t-test",
    ) -> list[ComparisonResult]:
        """두 실행을 통계적으로 비교합니다.

        Args:
            run_a: 첫 번째 평가 실행
            run_b: 두 번째 평가 실행
            metrics: 비교할 메트릭 목록 (None이면 공통 메트릭 모두)
            test_type: 통계 검정 유형 ('t-test', 'mann-whitney')

        Returns:
            메트릭별 ComparisonResult 리스트
        """
        ...

    def calculate_effect_size(
        self,
        values_a: list[float],
        values_b: list[float],
    ) -> float:
        """Cohen's d 효과 크기를 계산합니다.

        Args:
            values_a: 첫 번째 그룹의 값들
            values_b: 두 번째 그룹의 값들

        Returns:
            Cohen's d 값
        """
        ...
