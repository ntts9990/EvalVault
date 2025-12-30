"""Phase 14: Analysis Module Port (Outbound).

분석 모듈 플러그인을 위한 아웃바운드 포트 인터페이스입니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from evalvault.domain.entities.analysis_pipeline import ModuleMetadata


class AnalysisModulePort(Protocol):
    """분석 모듈 포트 인터페이스.

    개별 분석 모듈이 구현해야 하는 인터페이스입니다.
    형태소 분석기, BM25 검색기, 하이브리드 검색 비교기 등이
    이 인터페이스를 구현합니다.
    """

    @property
    def module_id(self) -> str:
        """모듈 고유 ID.

        Returns:
            모듈 ID 문자열
        """
        ...

    @property
    def metadata(self) -> ModuleMetadata:
        """모듈 메타데이터.

        Returns:
            모듈 메타데이터 객체
        """
        ...

    def validate_inputs(self, inputs: dict[str, Any]) -> bool:
        """입력 유효성 검증.

        Args:
            inputs: 입력 데이터 딕셔너리

        Returns:
            유효하면 True
        """
        ...

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """모듈 실행.

        Args:
            inputs: 입력 데이터 (이전 노드 출력 등)
            params: 실행 파라미터

        Returns:
            실행 결과 데이터
        """
        ...

    async def execute_async(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """모듈 비동기 실행.

        Args:
            inputs: 입력 데이터
            params: 실행 파라미터

        Returns:
            실행 결과 데이터
        """
        ...
