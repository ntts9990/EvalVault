"""Cache metrics helpers."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any


def _coerce_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


@dataclass(frozen=True)
class CacheStatsSnapshot:
    """Snapshot of cache stats for hit-rate measurement."""

    hits: int
    misses: int
    evictions: int
    expired: int
    size: int
    captured_at: float

    @property
    def total_requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        total = self.total_requests
        return self.hits / total if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        total = self.total_requests
        return self.misses / total if total > 0 else 0.0

    @classmethod
    def from_stats(
        cls,
        stats: Mapping[str, Any],
        *,
        captured_at: float | None = None,
    ) -> CacheStatsSnapshot:
        size = stats.get("total_size", stats.get("size", 0))
        return cls(
            hits=_coerce_int(stats.get("hits", 0)),
            misses=_coerce_int(stats.get("misses", 0)),
            evictions=_coerce_int(stats.get("evictions", 0)),
            expired=_coerce_int(stats.get("expired", 0)),
            size=_coerce_int(size),
            captured_at=captured_at if captured_at is not None else time.time(),
        )


@dataclass(frozen=True)
class CacheMetricsWindow:
    """Delta metrics between two cache snapshots."""

    start: CacheStatsSnapshot
    end: CacheStatsSnapshot

    @property
    def hits(self) -> int:
        return max(0, self.end.hits - self.start.hits)

    @property
    def misses(self) -> int:
        return max(0, self.end.misses - self.start.misses)

    @property
    def evictions(self) -> int:
        return max(0, self.end.evictions - self.start.evictions)

    @property
    def expired(self) -> int:
        return max(0, self.end.expired - self.start.expired)

    @property
    def total_requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        total = self.total_requests
        return self.hits / total if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        total = self.total_requests
        return self.misses / total if total > 0 else 0.0

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.end.captured_at - self.start.captured_at)


class CacheStatsTracker:
    """Track cache stats deltas between capture points."""

    def __init__(self, stats_provider: Callable[[], Mapping[str, Any]]):
        self._stats_provider = stats_provider
        self._baseline: CacheStatsSnapshot | None = None

    def capture(self) -> CacheStatsSnapshot:
        return CacheStatsSnapshot.from_stats(self._stats_provider())

    def reset(self) -> CacheStatsSnapshot:
        self._baseline = self.capture()
        return self._baseline

    def window(self, *, update_baseline: bool = True) -> CacheMetricsWindow:
        if self._baseline is None:
            self.reset()
        end = self.capture()
        window = CacheMetricsWindow(self._baseline or end, end)
        if update_baseline:
            self._baseline = end
        return window


__all__ = ["CacheMetricsWindow", "CacheStatsSnapshot", "CacheStatsTracker"]
