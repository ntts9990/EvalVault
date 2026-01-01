"""Tests for Async Batch Executor."""

import asyncio

import pytest

from evalvault.domain.services.async_batch_executor import (
    AsyncBatchExecutor,
    BatchExecutorConfig,
    BatchResult,
    ExecutionStats,
    execute_with_progress,
)


class TestBatchExecutorConfig:
    """BatchExecutorConfig 테스트."""

    def test_default_config(self):
        """기본 설정 테스트."""
        config = BatchExecutorConfig()

        assert config.initial_batch_size == 10
        assert config.min_batch_size == 1
        assert config.max_batch_size == 50
        assert config.max_retries == 3
        assert config.return_exceptions is True
        assert config.adaptive_batch_size is True

    def test_custom_config(self):
        """사용자 정의 설정 테스트."""
        config = BatchExecutorConfig(
            initial_batch_size=20,
            max_batch_size=100,
            max_retries=5,
        )

        assert config.initial_batch_size == 20
        assert config.max_batch_size == 100
        assert config.max_retries == 5


class TestAsyncBatchExecutorBasic:
    """AsyncBatchExecutor 기본 기능 테스트."""

    @pytest.mark.asyncio
    async def test_execute_empty_items(self):
        """빈 아이템 리스트 처리."""
        executor = AsyncBatchExecutor()

        async def worker(item):
            return item * 2

        result = await executor.execute([], worker)

        assert result.successful == 0
        assert result.failed == 0
        assert len(result.results) == 0

    @pytest.mark.asyncio
    async def test_execute_single_item(self):
        """단일 아이템 처리."""
        executor = AsyncBatchExecutor()

        async def worker(item):
            return item * 2

        result = await executor.execute([5], worker)

        assert result.successful == 1
        assert result.failed == 0
        assert result.results == [10]

    @pytest.mark.asyncio
    async def test_execute_multiple_items(self):
        """여러 아이템 처리."""
        config = BatchExecutorConfig(initial_batch_size=5)
        executor = AsyncBatchExecutor(config=config)

        async def worker(item):
            return item * 2

        items = list(range(10))
        result = await executor.execute(items, worker)

        assert result.successful == 10
        assert result.failed == 0
        assert result.results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

    @pytest.mark.asyncio
    async def test_execute_with_exceptions(self):
        """예외 발생 시 처리."""
        config = BatchExecutorConfig(return_exceptions=True, max_retries=0)
        executor = AsyncBatchExecutor(config=config)

        async def worker(item):
            if item == 5:
                raise ValueError("Error on item 5")
            return item * 2

        items = list(range(10))
        result = await executor.execute(items, worker)

        assert result.successful == 9
        assert result.failed == 1
        assert isinstance(result.results[5], ValueError)


class TestAsyncBatchExecutorRetry:
    """재시도 로직 테스트."""

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """실패 시 재시도."""
        call_count = {}

        config = BatchExecutorConfig(
            initial_batch_size=5,
            max_retries=2,
            retry_delay_seconds=0.1,
            return_exceptions=True,
        )
        executor = AsyncBatchExecutor(config=config)

        async def worker(item):
            call_count[item] = call_count.get(item, 0) + 1
            if call_count[item] < 2:
                raise ValueError(f"Fail on first attempt: {item}")
            return item * 2

        result = await executor.execute([1, 2, 3], worker)

        assert result.successful == 3
        assert result.failed == 0
        # 각 아이템은 2번씩 호출됨 (첫 실패 + 성공)
        for item in [1, 2, 3]:
            assert call_count[item] == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """최대 재시도 초과."""
        config = BatchExecutorConfig(
            initial_batch_size=5,
            max_retries=2,
            retry_delay_seconds=0.01,
            return_exceptions=True,
        )
        executor = AsyncBatchExecutor(config=config)

        async def worker(item):
            raise ValueError("Always fails")

        result = await executor.execute([1], worker)

        assert result.successful == 0
        assert result.failed == 1
        assert isinstance(result.results[0], ValueError)


class TestAsyncBatchExecutorAdaptive:
    """적응형 배치 크기 테스트."""

    @pytest.mark.asyncio
    async def test_batch_size_increases_on_success(self):
        """성공률 높을 때 배치 크기 증가."""
        config = BatchExecutorConfig(
            initial_batch_size=5,
            max_batch_size=50,
            adaptive_batch_size=True,
        )
        executor = AsyncBatchExecutor(config=config)

        async def worker(item):
            return item * 2

        # 충분한 아이템으로 배치 실행
        items = list(range(100))
        await executor.execute(items, worker)

        # 배치 크기가 증가했어야 함
        assert executor.get_current_batch_size() > 5

    @pytest.mark.asyncio
    async def test_batch_size_decreases_on_failure(self):
        """실패율 높을 때 배치 크기 감소."""
        config = BatchExecutorConfig(
            initial_batch_size=10,
            min_batch_size=1,
            adaptive_batch_size=True,
            max_retries=0,  # 재시도 안 함
        )
        executor = AsyncBatchExecutor(config=config)

        fail_count = 0

        async def worker(item):
            nonlocal fail_count
            # 50% 확률로 실패
            if item % 2 == 0:
                fail_count += 1
                raise ValueError("Fail")
            return item

        items = list(range(20))
        await executor.execute(items, worker)

        # 배치 크기가 감소했어야 함
        assert executor.get_current_batch_size() < 10

    def test_reset_batch_size(self):
        """배치 크기 리셋."""
        config = BatchExecutorConfig(initial_batch_size=10)
        executor = AsyncBatchExecutor(config=config)
        executor._current_batch_size = 50

        executor.reset_batch_size()

        assert executor.get_current_batch_size() == 10


class TestAsyncBatchExecutorProgress:
    """진행 콜백 테스트."""

    @pytest.mark.asyncio
    async def test_progress_callback_called(self):
        """진행 콜백 호출 확인."""
        progress_updates = []

        def on_progress(stats: ExecutionStats):
            progress_updates.append(stats.items_processed)

        config = BatchExecutorConfig(initial_batch_size=5)
        executor = AsyncBatchExecutor(config=config, progress_callback=on_progress)

        async def worker(item):
            return item * 2

        items = list(range(15))
        await executor.execute(items, worker)

        # 배치 완료마다 콜백 호출
        assert len(progress_updates) >= 3  # 15 items / 5 batch_size = 3 batches
        assert progress_updates[-1] == 15  # 마지막은 전체 완료


class TestAsyncBatchExecutorConcurrency:
    """동시성 제한 테스트."""

    @pytest.mark.asyncio
    async def test_max_concurrency_respected(self):
        """최대 동시성 제한 확인."""
        concurrent_count = []
        current_concurrent = 0
        lock = asyncio.Lock()

        config = BatchExecutorConfig(
            initial_batch_size=20,
            max_concurrency=3,
        )
        executor = AsyncBatchExecutor(config=config)

        async def worker(item):
            nonlocal current_concurrent
            async with lock:
                current_concurrent += 1
                concurrent_count.append(current_concurrent)
            await asyncio.sleep(0.05)
            async with lock:
                current_concurrent -= 1
            return item

        items = list(range(10))
        await executor.execute(items, worker)

        # 동시 실행 수가 3을 초과하지 않아야 함
        assert max(concurrent_count) <= 3


class TestAsyncBatchExecutorTimeout:
    """타임아웃 테스트."""

    @pytest.mark.asyncio
    async def test_timeout_on_slow_batch(self):
        """느린 배치 타임아웃."""
        config = BatchExecutorConfig(
            initial_batch_size=5,
            timeout_seconds=0.1,
            return_exceptions=True,
        )
        executor = AsyncBatchExecutor(config=config)

        async def worker(item):
            await asyncio.sleep(1)  # 1초 대기
            return item

        result = await executor.execute([1, 2, 3], worker)

        # 타임아웃으로 실패
        assert result.failed >= 1


class TestExecuteWithProgress:
    """execute_with_progress 간편 함수 테스트."""

    @pytest.mark.asyncio
    async def test_execute_with_progress(self):
        """진행 콜백과 함께 실행."""
        progress_calls = []

        def on_progress(completed, total):
            progress_calls.append((completed, total))

        async def worker(item):
            return item * 2

        results = await execute_with_progress(
            items=list(range(10)),
            worker=worker,
            batch_size=5,
            on_progress=on_progress,
        )

        assert len(results) == 10
        assert results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
        # 진행 콜백이 호출됨
        assert len(progress_calls) >= 2


class TestBatchResult:
    """BatchResult 데이터클래스 테스트."""

    def test_batch_result_creation(self):
        """BatchResult 생성 테스트."""
        result = BatchResult(
            results=[1, 2, 3],
            successful=3,
            failed=0,
            total_time_ms=100,
            avg_time_per_item_ms=33.3,
            retried=0,
        )

        assert len(result.results) == 3
        assert result.successful == 3
        assert result.failed == 0
        assert result.total_time_ms == 100


class TestExecutionStats:
    """ExecutionStats 데이터클래스 테스트."""

    def test_execution_stats_defaults(self):
        """기본값 테스트."""
        stats = ExecutionStats()

        assert stats.items_processed == 0
        assert stats.items_succeeded == 0
        assert stats.items_failed == 0
        assert stats.items_retried == 0


class TestRateLimitHandling:
    """레이트 리밋 처리 테스트."""

    @pytest.mark.asyncio
    async def test_rate_limit_detection(self):
        """레이트 리밋 감지."""
        config = BatchExecutorConfig(
            initial_batch_size=10,
            min_batch_size=1,
            adaptive_batch_size=True,
            max_retries=0,
        )
        executor = AsyncBatchExecutor(config=config)

        async def worker(item):
            if item < 5:
                raise Exception("429 Too Many Requests")
            return item

        await executor.execute(list(range(10)), worker)

        # 레이트 리밋 감지로 배치 크기 감소
        assert executor.get_current_batch_size() < 10
