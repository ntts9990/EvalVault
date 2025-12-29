"""Tests for Memory Cache Adapter."""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from evalvault.adapters.outbound.cache.memory_cache import MemoryCacheAdapter


class TestMemoryCacheBasic:
    """MemoryCacheAdapter 기본 기능 테스트."""

    @pytest.fixture
    def cache(self):
        """기본 캐시 인스턴스."""
        return MemoryCacheAdapter(max_size=10, default_ttl_seconds=60)

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


class TestMemoryCacheTTL:
    """TTL (Time-To-Live) 관련 테스트."""

    def test_ttl_expiration(self):
        """TTL 만료 테스트."""
        cache = MemoryCacheAdapter(default_ttl_seconds=1)
        cache.set("key1", "value1")

        # 아직 만료되지 않음
        assert cache.get("key1") == "value1"

        # TTL 경과 후
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_custom_ttl(self):
        """사용자 정의 TTL 테스트."""
        cache = MemoryCacheAdapter(default_ttl_seconds=60)
        cache.set("key1", "value1", ttl_seconds=1)

        # 1초 후 만료
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cleanup_expired(self):
        """만료된 항목 정리 테스트."""
        cache = MemoryCacheAdapter(default_ttl_seconds=1)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        time.sleep(1.1)
        removed = cache.cleanup_expired()

        assert removed == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestMemoryCacheLRU:
    """LRU (Least Recently Used) 관련 테스트."""

    def test_lru_eviction(self):
        """LRU 퇴출 테스트."""
        cache = MemoryCacheAdapter(max_size=3, default_ttl_seconds=60)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # 최대 크기 초과 시 가장 오래된 항목 삭제
        cache.set("key4", "value4")

        assert cache.get("key1") is None  # 가장 오래된 항목 삭제됨
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_lru_access_updates_order(self):
        """접근 시 LRU 순서 업데이트 테스트."""
        cache = MemoryCacheAdapter(max_size=3, default_ttl_seconds=60)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # key1을 접근하면 가장 최근으로 이동
        cache.get("key1")

        # 새 항목 추가 시 key2가 삭제됨 (key1은 최근 접근)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # 최근 접근했으므로 유지
        assert cache.get("key2") is None  # 가장 오래된 항목으로 삭제됨
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"


class TestMemoryCacheStats:
    """캐시 통계 테스트."""

    @pytest.fixture
    def cache(self):
        return MemoryCacheAdapter(max_size=10, default_ttl_seconds=60)

    def test_stats_initial(self, cache):
        """초기 통계 테스트."""
        stats = cache.get_stats()

        assert stats["size"] == 0
        assert stats["max_size"] == 10
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

        assert stats["size"] == 1
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(2 / 3)

    def test_stats_reset_on_clear(self, cache):
        """clear 후 통계 초기화 테스트."""
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.clear()

        stats = cache.get_stats()

        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0


class TestMemoryCacheThreadSafety:
    """스레드 안전성 테스트."""

    def test_concurrent_writes(self):
        """동시 쓰기 테스트."""
        cache = MemoryCacheAdapter(max_size=100, default_ttl_seconds=60)

        def write_values(start, count):
            for i in range(start, start + count):
                cache.set(f"key{i}", f"value{i}")

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(write_values, i * 25, 25) for i in range(4)]
            for f in futures:
                f.result()

        # 모든 값이 정상적으로 저장되었는지 확인
        count = 0
        for i in range(100):
            if cache.get(f"key{i}") is not None:
                count += 1

        assert count == 100

    def test_concurrent_reads_writes(self):
        """동시 읽기/쓰기 테스트."""
        cache = MemoryCacheAdapter(max_size=100, default_ttl_seconds=60)

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


class TestMemoryCacheEdgeCases:
    """엣지 케이스 테스트."""

    def test_none_value(self):
        """None 값 저장 테스트."""
        cache = MemoryCacheAdapter()
        cache.set("key1", None)
        result = cache.get("key1")

        assert result is None  # None도 정상적으로 저장됨

    def test_empty_string_key(self):
        """빈 문자열 키 테스트."""
        cache = MemoryCacheAdapter()
        cache.set("", "value")
        result = cache.get("")

        assert result == "value"

    def test_large_value(self):
        """큰 값 저장 테스트."""
        cache = MemoryCacheAdapter()
        large_data = "x" * 1000000  # 1MB 문자열
        cache.set("large", large_data)
        result = cache.get("large")

        assert result == large_data

    def test_max_size_one(self):
        """max_size=1 테스트."""
        cache = MemoryCacheAdapter(max_size=1)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_ttl_zero(self):
        """TTL=0 테스트 (즉시 만료)."""
        cache = MemoryCacheAdapter(default_ttl_seconds=0)
        cache.set("key1", "value1")

        # 즉시 만료
        result = cache.get("key1")
        assert result is None
