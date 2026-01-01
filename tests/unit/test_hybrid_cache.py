"""Tests for Hybrid Cache Adapter."""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from evalvault.adapters.outbound.cache.hybrid_cache import (
    CacheEntry,
    HybridCache,
    make_cache_key,
)


class TestHybridCacheBasic:
    """HybridCache 기본 기능 테스트."""

    @pytest.fixture
    def cache(self):
        """기본 캐시 인스턴스."""
        return HybridCache(max_size=100, ttl_seconds=60, hot_ratio=0.3)

    def test_set_and_get(self, cache):
        """기본 set/get 테스트."""
        cache.set("key1", "value1")
        result = cache.get("key1")

        assert result == "value1"

    def test_get_nonexistent_key(self, cache):
        """존재하지 않는 키 조회 테스트."""
        result = cache.get("nonexistent")

        assert result is None

    def test_set_overwrites_existing(self, cache):
        """기존 값 덮어쓰기 테스트."""
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        result = cache.get("key1")

        assert result == "value2"

    def test_delete_key(self, cache):
        """키 삭제 테스트."""
        cache.set("key1", "value1")
        deleted = cache.delete("key1")
        result = cache.get("key1")

        assert deleted is True
        assert result is None

    def test_delete_nonexistent_key(self, cache):
        """존재하지 않는 키 삭제 테스트."""
        deleted = cache.delete("nonexistent")

        assert deleted is False

    def test_clear_cache(self, cache):
        """캐시 전체 삭제 테스트."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_store_complex_objects(self, cache):
        """복잡한 객체 저장 테스트."""
        data = {
            "list": [1, 2, 3],
            "nested": {"a": 1, "b": 2},
            "string": "hello",
        }
        cache.set("complex", data)
        result = cache.get("complex")

        assert result == data
        assert result["list"] == [1, 2, 3]


class TestHybridCacheTTL:
    """TTL (Time-To-Live) 관련 테스트."""

    def test_ttl_expiration(self):
        """TTL 만료 테스트."""
        cache = HybridCache(ttl_seconds=1)
        cache.set("key1", "value1")

        # 아직 만료되지 않음
        assert cache.get("key1") == "value1"

        # TTL 경과 후
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_custom_ttl(self):
        """사용자 정의 TTL 테스트."""
        cache = HybridCache(ttl_seconds=60)
        cache.set("key1", "value1", ttl_seconds=1)

        # 1초 후 만료
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cleanup_expired(self):
        """만료된 항목 정리 테스트."""
        cache = HybridCache(ttl_seconds=1)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        time.sleep(1.1)
        removed = cache.cleanup_expired()

        assert removed == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestHybridCacheHotCold:
    """Hot/Cold 영역 테스트."""

    def test_initial_storage_in_cold(self):
        """새 항목은 Cold 영역에 저장."""
        cache = HybridCache(max_size=10, hot_ratio=0.3)
        cache.set("key1", "value1")

        stats = cache.get_stats()
        assert stats["cold_size"] == 1
        assert stats["hot_size"] == 0

    def test_promotion_to_hot(self):
        """접근 횟수에 따른 Hot 승격 테스트."""
        cache = HybridCache(max_size=10, hot_ratio=0.3)
        cache.set("key1", "value1")

        # HOT_PROMOTION_THRESHOLD(3)번 이상 접근 시 승격
        for _ in range(4):
            cache.get("key1")

        stats = cache.get_stats()
        assert stats["hot_size"] == 1
        assert stats["cold_size"] == 0
        assert stats["promotions"] >= 1

    def test_hot_hits_tracked(self):
        """Hot 영역 히트 추적 테스트."""
        cache = HybridCache(max_size=10, hot_ratio=0.5)
        cache.set("key1", "value1")

        # 먼저 승격시키기
        for _ in range(5):
            cache.get("key1")

        # 추가 접근
        cache.get("key1")

        stats = cache.get_stats()
        assert stats["hot_hits"] >= 1


class TestHybridCacheLRU:
    """LRU 퇴출 관련 테스트."""

    def test_cold_lru_eviction(self):
        """Cold 영역 LRU 퇴출 테스트."""
        cache = HybridCache(max_size=10, hot_ratio=0.3)
        # cold_max = 7

        # 8개 항목 추가 (cold 용량 초과)
        for i in range(8):
            cache.set(f"key{i}", f"value{i}")

        # 첫 번째 항목은 퇴출되어야 함
        assert cache.get("key0") is None
        assert cache.get("key7") == "value7"

    def test_access_updates_lru_order(self):
        """접근 시 LRU 순서 업데이트 테스트."""
        cache = HybridCache(max_size=5, hot_ratio=0.2)
        # cold_max = 4

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")

        # key1 접근하여 최근으로 이동
        cache.get("key1")

        # 새 항목 추가 시 key2가 퇴출됨
        cache.set("key5", "value5")

        assert cache.get("key1") == "value1"  # 최근 접근했으므로 유지
        assert cache.get("key2") is None  # 가장 오래된 항목으로 삭제


class TestHybridCacheStats:
    """캐시 통계 테스트."""

    @pytest.fixture
    def cache(self):
        return HybridCache(max_size=100, ttl_seconds=60, hot_ratio=0.3)

    def test_stats_initial(self, cache):
        """초기 통계 테스트."""
        stats = cache.get_stats()

        assert stats["total_size"] == 0
        assert stats["hot_size"] == 0
        assert stats["cold_size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

    def test_stats_after_operations(self, cache):
        """연산 후 통계 테스트."""
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("key2")  # miss

        stats = cache.get_stats()

        assert stats["total_size"] == 1
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(2 / 3)

    def test_stats_reset_on_clear(self, cache):
        """clear 후 통계 초기화 테스트."""
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.clear()

        stats = cache.get_stats()

        assert stats["total_size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0


class TestHybridCacheGetOrSet:
    """get_or_set 기능 테스트."""

    def test_get_or_set_cache_miss(self):
        """캐시 미스 시 팩토리 호출 테스트."""
        cache = HybridCache()
        factory_called = []

        def factory():
            factory_called.append(True)
            return "new_value"

        result = cache.get_or_set("key1", factory)

        assert result == "new_value"
        assert len(factory_called) == 1

    def test_get_or_set_cache_hit(self):
        """캐시 히트 시 팩토리 호출 안 함 테스트."""
        cache = HybridCache()
        cache.set("key1", "cached_value")
        factory_called = []

        def factory():
            factory_called.append(True)
            return "new_value"

        result = cache.get_or_set("key1", factory)

        assert result == "cached_value"
        assert len(factory_called) == 0


class TestHybridCacheBatchOperations:
    """배치 연산 테스트."""

    @pytest.fixture
    def cache(self):
        return HybridCache(max_size=100, ttl_seconds=60)

    def test_set_many(self, cache):
        """여러 항목 저장 테스트."""
        items = {"key1": "value1", "key2": "value2", "key3": "value3"}
        cache.set_many(items)

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_get_many(self, cache):
        """여러 항목 조회 테스트."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        result = cache.get_many(["key1", "key2", "key3"])

        assert result == {"key1": "value1", "key2": "value2"}
        assert "key3" not in result


class TestHybridCachePrefetch:
    """프리페치 콜백 테스트."""

    def test_prefetch_on_miss(self):
        """캐시 미스 시 프리페치 콜백 호출 테스트."""
        prefetch_calls = []

        def prefetch(key):
            prefetch_calls.append(key)
            return f"prefetched_{key}"

        cache = HybridCache(prefetch_callback=prefetch)
        result = cache.get("missing_key")

        assert result == "prefetched_missing_key"
        assert "missing_key" in prefetch_calls
        # 캐시에 저장되어야 함
        assert cache.get("missing_key") == "prefetched_missing_key"

    def test_prefetch_not_called_on_hit(self):
        """캐시 히트 시 프리페치 콜백 호출 안 함 테스트."""
        prefetch_calls = []

        def prefetch(key):
            prefetch_calls.append(key)
            return f"prefetched_{key}"

        cache = HybridCache(prefetch_callback=prefetch)
        cache.set("key1", "cached_value")
        result = cache.get("key1")

        assert result == "cached_value"
        assert len(prefetch_calls) == 0


class TestHybridCacheThreadSafety:
    """스레드 안전성 테스트."""

    def test_concurrent_writes(self):
        """동시 쓰기 테스트."""
        cache = HybridCache(max_size=500, ttl_seconds=60)

        def write_values(start, count):
            for i in range(start, start + count):
                cache.set(f"key{i}", f"value{i}")

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(write_values, i * 100, 100) for i in range(4)]
            for f in futures:
                f.result()

        # 최소한 일부는 저장되어야 함 (LRU 퇴출 고려)
        stats = cache.get_stats()
        assert stats["total_size"] > 0

    def test_concurrent_reads_writes(self):
        """동시 읽기/쓰기 테스트."""
        cache = HybridCache(max_size=200, ttl_seconds=60)

        # 초기 데이터 설정
        for i in range(50):
            cache.set(f"key{i}", f"value{i}")

        def read_values():
            results = []
            for i in range(50):
                result = cache.get(f"key{i}")
                results.append(result)
            return results

        def write_values():
            for i in range(50, 100):
                cache.set(f"key{i}", f"value{i}")

        with ThreadPoolExecutor(max_workers=4) as executor:
            read_futures = [executor.submit(read_values) for _ in range(2)]
            write_futures = [executor.submit(write_values) for _ in range(2)]

            # 모든 작업이 예외 없이 완료되어야 함
            for f in read_futures + write_futures:
                f.result()


class TestMakeCacheKey:
    """캐시 키 생성 유틸리티 테스트."""

    def test_same_args_same_key(self):
        """동일 인자는 동일 키 생성."""
        key1 = make_cache_key("a", "b", x=1, y=2)
        key2 = make_cache_key("a", "b", x=1, y=2)

        assert key1 == key2

    def test_different_args_different_key(self):
        """다른 인자는 다른 키 생성."""
        key1 = make_cache_key("a", "b")
        key2 = make_cache_key("a", "c")

        assert key1 != key2

    def test_kwarg_order_independent(self):
        """키워드 인자 순서 독립."""
        key1 = make_cache_key(x=1, y=2)
        key2 = make_cache_key(y=2, x=1)

        assert key1 == key2

    def test_complex_args(self):
        """복잡한 인자 처리."""
        key = make_cache_key(
            "query",
            123,
            ["a", "b"],
            nested={"key": "value"},
        )

        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hex digest


class TestCacheEntry:
    """CacheEntry 데이터클래스 테스트."""

    def test_cache_entry_creation(self):
        """CacheEntry 생성 테스트."""
        now = time.time()
        entry = CacheEntry(
            value="test",
            expires_at=now + 3600,
            access_count=0,
        )

        assert entry.value == "test"
        assert entry.expires_at > now
        assert entry.access_count == 0
