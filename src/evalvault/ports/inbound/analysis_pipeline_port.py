"""Phase 14: Analysis Pipeline Port (Inbound).

분석 파이프라인 실행을 위한 인바운드 포트 인터페이스입니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from evalvault.domain.entities.analysis_pipeline import (
        AnalysisContext,
        AnalysisIntent,
        AnalysisPipeline,
        PipelineResult,
    )


class AnalysisPipelinePort(Protocol):
    """분석 파이프라인 포트 인터페이스.

    사용자 쿼리에 따른 분석 파이프라인 구성 및 실행을 담당합니다.
    """

    def build_pipeline(
        self,
        intent: AnalysisIntent,
        context: AnalysisContext,
    ) -> AnalysisPipeline:
        """의도와 컨텍스트에 따라 분석 파이프라인을 구성합니다.

        Args:
            intent: 분석 의도
            context: 분석 컨텍스트

        Returns:
            구성된 분석 파이프라인
        """
        ...

    def execute(
        self,
        pipeline: AnalysisPipeline,
        context: AnalysisContext,
    ) -> PipelineResult:
        """분석 파이프라인을 실행합니다.

        Args:
            pipeline: 실행할 파이프라인
            context: 분석 컨텍스트

        Returns:
            파이프라인 실행 결과
        """
        ...

    async def execute_async(
        self,
        pipeline: AnalysisPipeline,
        context: AnalysisContext,
    ) -> PipelineResult:
        """분석 파이프라인을 비동기로 실행합니다.

        Args:
            pipeline: 실행할 파이프라인
            context: 분석 컨텍스트

        Returns:
            파이프라인 실행 결과
        """
        ...
