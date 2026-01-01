"""인메모리 캐시 어댑터.

TTL과 LRU 기반의 인메모리 캐시를 제공합니다.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any


class MemoryCacheAdapter:
    """인메모리 LRU 캐시 어댑터.

    AnalysisCachePort 인터페이스를 구현합니다.
    """

    def __init__(
        self,
        max_size: int = 100,
        default_ttl_seconds: int = 3600,
    ):
        """초기화.

        Args:
            max_size: 최대 캐시 항목 수
            default_ttl_seconds: 기본 TTL (초)
        """
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl_seconds
        self._lock = threading.RLock()

        # 통계
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """캐시에서 값을 조회합니다."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, expires_at = self._cache[key]

            # TTL 체크
            if expires_at <= time.time():
                del self._cache[key]
                self._misses += 1
                return None

            # LRU: 최근 사용으로 이동
            self._cache.move_to_end(key)
            self._hits += 1

            return value

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> bool:
        """캐시에 값을 저장합니다."""
        with self._lock:
            ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
            expires_at = time.time() + ttl

            # 기존 키가 있으면 삭제
            if key in self._cache:
                del self._cache[key]

            # LRU: 가장 오래된 항목 삭제
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)

            self._cache[key] = (value, expires_at)
            return True

    def delete(self, key: str) -> bool:
        """캐시에서 값을 삭제합니다."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """모든 캐시를 삭제합니다."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> dict[str, Any]:
        """캐시 통계를 조회합니다."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "default_ttl_seconds": self._default_ttl,
            }

    def cleanup_expired(self) -> int:
        """만료된 캐시 항목을 정리합니다.

        Returns:
            삭제된 항목 수
        """
        with self._lock:
            now = time.time()
            expired_keys = [
                key for key, (_, expires_at) in self._cache.items() if expires_at <= now
            ]

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)
