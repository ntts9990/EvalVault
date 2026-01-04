"""Cache metrics helpers tests."""

from __future__ import annotations

from evalvault.domain.services.cache_metrics import (
    CacheMetricsWindow,
    CacheStatsSnapshot,
    CacheStatsTracker,
)


def test_snapshot_from_stats_and_rates() -> None:
    snapshot = CacheStatsSnapshot.from_stats(
        {
            "hits": "3",
            "misses": 1,
            "evictions": "2",
            "expired": None,
            "size": "5",
        },
        captured_at=10.0,
    )

    assert snapshot.hits == 3
    assert snapshot.misses == 1
    assert snapshot.evictions == 2
    assert snapshot.expired == 0
    assert snapshot.size == 5
    assert snapshot.total_requests == 4
    assert snapshot.hit_rate == 0.75
    assert snapshot.miss_rate == 0.25
    assert snapshot.captured_at == 10.0


def test_metrics_window_delta_and_duration() -> None:
    start = CacheStatsSnapshot(
        hits=5,
        misses=2,
        evictions=3,
        expired=1,
        size=10,
        captured_at=5.0,
    )
    end = CacheStatsSnapshot(
        hits=8,
        misses=1,
        evictions=2,
        expired=4,
        size=12,
        captured_at=9.5,
    )

    window = CacheMetricsWindow(start=start, end=end)

    assert window.hits == 3
    assert window.misses == 0
    assert window.evictions == 0
    assert window.expired == 3
    assert window.total_requests == 3
    assert window.hit_rate == 1.0
    assert window.miss_rate == 0.0
    assert window.duration_seconds == 4.5


def test_tracker_resets_and_updates_baseline() -> None:
    stats_sequence = iter(
        [
            {"hits": 1, "misses": 1, "evictions": 0, "expired": 0, "size": 5},
            {"hits": 4, "misses": 2, "evictions": 1, "expired": 1, "size": 6},
            {"hits": 6, "misses": 3, "evictions": 1, "expired": 2, "size": 7},
        ]
    )

    tracker = CacheStatsTracker(lambda: next(stats_sequence))
    baseline = tracker.reset()
    assert baseline.hits == 1

    window = tracker.window()
    assert window.hits == 3
    assert window.misses == 1
    assert window.evictions == 1
    assert window.expired == 1

    window_no_update = tracker.window(update_baseline=False)
    assert window_no_update.hits == 2
