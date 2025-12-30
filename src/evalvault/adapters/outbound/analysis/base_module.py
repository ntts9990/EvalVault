"""Phase 14.4: Base Analysis Module.

분석 모듈의 기본 클래스입니다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from evalvault.domain.entities.analysis_pipeline import ModuleMetadata


class BaseAnalysisModule(ABC):
    """분석 모듈 기본 클래스.

    모든 분석 모듈은 이 클래스를 상속받아 구현합니다.

    Attributes:
        module_id: 모듈 고유 ID
        name: 모듈 표시 이름
        description: 모듈 설명
        input_types: 입력 타입 목록
        output_types: 출력 타입 목록
        requires: 필수 의존 모듈 ID 목록
        optional_requires: 선택적 의존 모듈 ID 목록
        tags: 태그 목록
    """

    module_id: str
    name: str
    description: str
    input_types: list[str]
    output_types: list[str]
    requires: list[str] = []
    optional_requires: list[str] = []
    tags: list[str] = []

    @property
    def metadata(self) -> ModuleMetadata:
        """모듈 메타데이터.

        Returns:
            ModuleMetadata 객체
        """
        return ModuleMetadata(
            module_id=self.module_id,
            name=self.name,
            description=self.description,
            input_types=self.input_types,
            output_types=self.output_types,
            requires=getattr(self, "requires", []),
            optional_requires=getattr(self, "optional_requires", []),
            tags=getattr(self, "tags", []),
        )

    def validate_inputs(self, inputs: dict[str, Any]) -> bool:
        """입력 유효성 검증.

        Args:
            inputs: 입력 데이터

        Returns:
            유효하면 True
        """
        return True

    @abstractmethod
    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """모듈 실행.

        Args:
            inputs: 입력 데이터
            params: 실행 파라미터

        Returns:
            실행 결과
        """
        ...

    async def execute_async(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """모듈 비동기 실행.

        기본 구현은 동기 실행을 호출합니다.

        Args:
            inputs: 입력 데이터
            params: 실행 파라미터

        Returns:
            실행 결과
        """
        return self.execute(inputs, params)
