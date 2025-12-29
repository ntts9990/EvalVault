"""분석 결과 캐싱 인터페이스."""

from typing import Any, Protocol


class AnalysisCachePort(Protocol):
    """분석 결과 캐싱을 위한 포트 인터페이스.

    분석 결과를 캐싱하여 반복 요청 시 성능을 향상시킵니다.
    """

    def get(self, key: str) -> Any | None:
        """캐시에서 값을 조회합니다.

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 또는 None (캐시 미스)
        """
        ...

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> bool:
        """캐시에 값을 저장합니다.

        Args:
            key: 캐시 키
            value: 저장할 값
            ttl_seconds: 만료 시간 (초), None이면 기본값 사용

        Returns:
            저장 성공 여부
        """
        ...

    def delete(self, key: str) -> bool:
        """캐시에서 값을 삭제합니다.

        Args:
            key: 삭제할 캐시 키

        Returns:
            삭제 성공 여부
        """
        ...

    def clear(self) -> None:
        """모든 캐시를 삭제합니다."""
        ...

    def get_stats(self) -> dict[str, Any]:
        """캐시 통계를 조회합니다.

        Returns:
            캐시 통계 정보 (hits, misses, size 등)
        """
        ...
