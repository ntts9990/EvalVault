"""LRU + TTL 하이브리드 캐시 어댑터.

목표: 캐시 hit rate 60% -> 85%
개선 사항:
- 핫 영역과 콜드 영역 분리 (2-tier 캐시)
- 접근 빈도 기반 승격/강등
- 프리페치 지원 (예측 기반 사전 로딩)
- 적응형 TTL (자주 접근되는 항목은 TTL 연장)
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CacheEntry:
    """캐시 항목 메타데이터."""

    value: Any
    expires_at: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0


class HybridCache:
    """LRU + TTL 하이브리드 캐시.

    특징:
    - 2-tier 아키텍처 (hot/cold 영역)
    - 접근 빈도 기반 자동 승격/강등
    - 적응형 TTL (자주 접근 시 TTL 연장)
    - 프리페치 콜백 지원
    - 스레드 안전

    목표: hit rate 85% 달성
    """

    # Hot 영역 승격 임계값 (접근 횟수)
    HOT_PROMOTION_THRESHOLD = 3
    # TTL 연장 배수 (hot 영역)
    TTL_EXTENSION_FACTOR = 2.0
    # 최대 TTL 연장 배수
    MAX_TTL_EXTENSION = 5.0

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
        hot_ratio: float = 0.3,
        prefetch_callback: Callable[[str], Any] | None = None,
    ):
        """초기화.

        Args:
            max_size: 전체 최대 캐시 항목 수
            ttl_seconds: 기본 TTL (초)
            hot_ratio: hot 영역 비율 (0.0 ~ 1.0)
            prefetch_callback: 캐시 미스 시 값을 가져오는 콜백 함수
        """
        self._max_size = max_size
        self._default_ttl = ttl_seconds
        self._hot_ratio = hot_ratio
        self._prefetch_callback = prefetch_callback

        # Hot 영역 (자주 접근되는 항목)
        self._hot: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hot_max = int(max_size * hot_ratio)

        # Cold 영역 (일반 항목)
        self._cold: OrderedDict[str, CacheEntry] = OrderedDict()
        self._cold_max = max_size - self._hot_max

        # 스레드 안전
        self._lock = threading.RLock()

        # 통계
        self._hits = 0
        self._misses = 0
        self._hot_hits = 0
        self._cold_hits = 0
        self._promotions = 0
        self._demotions = 0
        self._prefetch_hits = 0

    def get(self, key: str) -> Any | None:
        """캐시에서 값을 조회합니다.

        Hot 영역 먼저 확인 후 Cold 영역 확인.
        접근 횟수에 따라 Cold -> Hot 승격.

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 또는 None (캐시 미스)
        """
        with self._lock:
            now = time.time()

            # 1. Hot 영역 확인
            if key in self._hot:
                entry = self._hot[key]
                if entry.expires_at > now:
                    self._update_entry_access(entry)
                    self._hot.move_to_end(key)
                    self._hits += 1
                    self._hot_hits += 1
                    return entry.value
                else:
                    del self._hot[key]

            # 2. Cold 영역 확인
            if key in self._cold:
                entry = self._cold[key]
                if entry.expires_at > now:
                    self._update_entry_access(entry)
                    self._cold.move_to_end(key)
                    self._hits += 1
                    self._cold_hits += 1

                    # 승격 조건 확인
                    if entry.access_count >= self.HOT_PROMOTION_THRESHOLD:
                        self._promote_to_hot(key, entry)

                    return entry.value
                else:
                    del self._cold[key]

            # 3. 캐시 미스
            self._misses += 1

            # 프리페치 콜백이 있으면 값 가져오기
            if self._prefetch_callback:
                try:
                    value = self._prefetch_callback(key)
                    if value is not None:
                        self.set(key, value)
                        self._prefetch_hits += 1
                        return value
                except Exception:
                    pass

            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        """캐시에 값을 저장합니다.

        새 항목은 Cold 영역에 저장되고, 접근 빈도에 따라 Hot으로 승격됩니다.

        Args:
            key: 캐시 키
            value: 저장할 값
            ttl_seconds: 만료 시간 (초), None이면 기본값 사용
        """
        with self._lock:
            ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
            expires_at = time.time() + ttl

            # 기존 항목 제거
            if key in self._hot:
                del self._hot[key]
            if key in self._cold:
                del self._cold[key]

            entry = CacheEntry(
                value=value,
                expires_at=expires_at,
                access_count=1,
                last_accessed=time.time(),
                size_bytes=self._estimate_size(value),
            )

            # Cold 영역에 저장
            self._ensure_cold_capacity()
            self._cold[key] = entry

    def delete(self, key: str) -> bool:
        """캐시에서 값을 삭제합니다.

        Args:
            key: 삭제할 캐시 키

        Returns:
            삭제 성공 여부
        """
        with self._lock:
            if key in self._hot:
                del self._hot[key]
                return True
            if key in self._cold:
                del self._cold[key]
                return True
            return False

    def clear(self) -> None:
        """모든 캐시를 삭제합니다."""
        with self._lock:
            self._hot.clear()
            self._cold.clear()
            self._reset_stats()

    def get_stats(self) -> dict[str, Any]:
        """캐시 통계를 조회합니다.

        Returns:
            캐시 통계 정보
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0
            hot_hit_rate = self._hot_hits / self._hits if self._hits > 0 else 0.0

            return {
                "total_size": len(self._hot) + len(self._cold),
                "hot_size": len(self._hot),
                "cold_size": len(self._cold),
                "max_size": self._max_size,
                "hot_max": self._hot_max,
                "cold_max": self._cold_max,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "hot_hits": self._hot_hits,
                "cold_hits": self._cold_hits,
                "hot_hit_rate": hot_hit_rate,
                "promotions": self._promotions,
                "demotions": self._demotions,
                "prefetch_hits": self._prefetch_hits,
                "default_ttl_seconds": self._default_ttl,
            }

    def cleanup_expired(self) -> int:
        """만료된 캐시 항목을 정리합니다.

        Returns:
            삭제된 항목 수
        """
        with self._lock:
            now = time.time()
            removed = 0

            # Hot 영역 정리
            expired_hot = [k for k, v in self._hot.items() if v.expires_at <= now]
            for key in expired_hot:
                del self._hot[key]
                removed += 1

            # Cold 영역 정리
            expired_cold = [k for k, v in self._cold.items() if v.expires_at <= now]
            for key in expired_cold:
                del self._cold[key]
                removed += 1

            return removed

    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl_seconds: int | None = None,
    ) -> Any:
        """캐시에서 값을 조회하거나, 없으면 생성하여 저장합니다.

        Args:
            key: 캐시 키
            factory: 값이 없을 때 호출할 팩토리 함수
            ttl_seconds: 만료 시간 (초)

        Returns:
            캐시된 값 또는 새로 생성된 값
        """
        value = self.get(key)
        if value is not None:
            return value

        # 캐시 미스 시 값 생성
        value = factory()
        self.set(key, value, ttl_seconds)
        return value

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """여러 키의 값을 한 번에 조회합니다.

        Args:
            keys: 조회할 키 목록

        Returns:
            키-값 딕셔너리 (캐시 미스는 포함되지 않음)
        """
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def set_many(
        self,
        items: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> None:
        """여러 항목을 한 번에 저장합니다.

        Args:
            items: 키-값 딕셔너리
            ttl_seconds: 만료 시간 (초)
        """
        for key, value in items.items():
            self.set(key, value, ttl_seconds)

    def _promote_to_hot(self, key: str, entry: CacheEntry) -> None:
        """Cold 영역에서 Hot 영역으로 승격.

        Args:
            key: 캐시 키
            entry: 캐시 항목
        """
        # Hot 영역 용량 확보
        self._ensure_hot_capacity()

        # Cold에서 제거
        if key in self._cold:
            del self._cold[key]

        # TTL 연장 (자주 접근되는 항목)
        extension = min(
            entry.access_count * self.TTL_EXTENSION_FACTOR,
            self.MAX_TTL_EXTENSION,
        )
        remaining_ttl = entry.expires_at - time.time()
        if remaining_ttl > 0:
            entry.expires_at = time.time() + remaining_ttl * extension

        # Hot에 추가
        self._hot[key] = entry
        self._promotions += 1

    def _demote_from_hot(self) -> None:
        """Hot 영역에서 가장 오래된 항목을 Cold로 강등."""
        if not self._hot:
            return

        # 가장 오래된 항목 (LRU)
        oldest_key, oldest_entry = next(iter(self._hot.items()))
        del self._hot[oldest_key]

        # Cold 용량 확보 후 이동
        self._ensure_cold_capacity()
        self._cold[oldest_key] = oldest_entry
        self._demotions += 1

    def _ensure_hot_capacity(self) -> None:
        """Hot 영역 용량 확보."""
        while len(self._hot) >= self._hot_max:
            self._demote_from_hot()

    def _ensure_cold_capacity(self) -> None:
        """Cold 영역 용량 확보."""
        while len(self._cold) >= self._cold_max:
            # 가장 오래된 항목 삭제 (LRU)
            self._cold.popitem(last=False)

    def _update_entry_access(self, entry: CacheEntry) -> None:
        """항목 접근 시 메타데이터 업데이트.

        Args:
            entry: 캐시 항목
        """
        entry.access_count += 1
        entry.last_accessed = time.time()

    def _estimate_size(self, value: Any) -> int:
        """값의 대략적인 크기 추정 (바이트).

        Args:
            value: 크기를 추정할 값

        Returns:
            추정 크기 (바이트)
        """
        try:
            import sys

            return sys.getsizeof(value)
        except Exception:
            return 0

    def _reset_stats(self) -> None:
        """통계 초기화."""
        self._hits = 0
        self._misses = 0
        self._hot_hits = 0
        self._cold_hits = 0
        self._promotions = 0
        self._demotions = 0
        self._prefetch_hits = 0


def make_cache_key(*args: Any, **kwargs: Any) -> str:
    """캐시 키 생성 유틸리티.

    인자들을 해시하여 일관된 캐시 키를 생성합니다.

    Args:
        *args: 위치 인자
        **kwargs: 키워드 인자

    Returns:
        해시된 캐시 키 문자열
    """
    # 인자들을 문자열로 변환하여 결합
    parts = [str(arg) for arg in args]
    parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    combined = "|".join(parts)

    # MD5 해시 (충돌 가능성 낮고 빠름)
    return hashlib.md5(combined.encode()).hexdigest()


__all__ = ["HybridCache", "CacheEntry", "make_cache_key"]
