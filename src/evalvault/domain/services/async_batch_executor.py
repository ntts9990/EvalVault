"""향상된 비동기 배치 실행기.

목표: 평가 속도 30분 -> 20분 (1000 테스트케이스 기준)

기능:
- 적응형 배치 크기 조절
- 레이트 리밋 자동 처리
- 진행 상황 콜백
- 재시도 메커니즘
- 리소스 사용량 모니터링
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass


@dataclass
class BatchResult[R]:
    """배치 실행 결과."""

    results: list[R | Exception]
    successful: int = 0
    failed: int = 0
    total_time_ms: int = 0
    avg_time_per_item_ms: float = 0.0
    retried: int = 0


@dataclass
class BatchExecutorConfig:
    """배치 실행기 설정."""

    # 기본 배치 크기
    initial_batch_size: int = 10
    # 최소 배치 크기
    min_batch_size: int = 1
    # 최대 배치 크기
    max_batch_size: int = 50
    # 배치 간 지연 시간 (초)
    batch_delay_seconds: float = 0.1
    # 최대 재시도 횟수
    max_retries: int = 3
    # 재시도 간 지연 (초, 지수 백오프 적용)
    retry_delay_seconds: float = 1.0
    # 예외 반환 여부 (False면 예외 발생 시 전체 실패)
    return_exceptions: bool = True
    # 동시성 제한 (세마포어)
    max_concurrency: int | None = None
    # 적응형 배치 크기 사용
    adaptive_batch_size: bool = True
    # 타임아웃 (초)
    timeout_seconds: float | None = None


@dataclass
class ExecutionStats:
    """실행 통계."""

    items_processed: int = 0
    items_succeeded: int = 0
    items_failed: int = 0
    items_retried: int = 0
    total_time_ms: int = 0
    current_batch_size: int = 0
    batches_completed: int = 0
    rate_limited_count: int = 0


class AsyncBatchExecutor[T, R]:
    """향상된 비동기 배치 실행기.

    특징:
    - 적응형 배치 크기: 성공률에 따라 배치 크기 자동 조절
    - 레이트 리밋 대응: 429 오류 시 자동 감속
    - 진행 콜백: 실시간 진행 상황 보고
    - 스마트 재시도: 지수 백오프로 재시도
    """

    def __init__(
        self,
        config: BatchExecutorConfig | None = None,
        progress_callback: Callable[[ExecutionStats], None] | None = None,
    ):
        """초기화.

        Args:
            config: 실행기 설정
            progress_callback: 진행 상황 콜백 함수
        """
        self.config = config or BatchExecutorConfig()
        self.progress_callback = progress_callback
        self._current_batch_size = self.config.initial_batch_size
        self._stats = ExecutionStats()
        self._semaphore: asyncio.Semaphore | None = None

    async def execute(
        self,
        items: Sequence[T],
        worker: Callable[[T], Awaitable[R]],
    ) -> BatchResult[R]:
        """아이템들을 배치로 나누어 비동기 실행.

        Args:
            items: 처리할 아이템 시퀀스
            worker: 각 아이템을 처리하는 비동기 함수

        Returns:
            배치 실행 결과
        """
        if not items:
            return BatchResult(results=[], successful=0, failed=0)

        start_time = time.time()
        self._stats = ExecutionStats(current_batch_size=self._current_batch_size)

        # 동시성 제한 세마포어 초기화
        if self.config.max_concurrency:
            self._semaphore = asyncio.Semaphore(self.config.max_concurrency)

        results: list[R | Exception] = []
        items_list = list(items)
        idx = 0

        while idx < len(items_list):
            # 현재 배치 크기만큼 아이템 선택
            batch_end = min(idx + self._current_batch_size, len(items_list))
            batch_items = items_list[idx:batch_end]

            # 배치 실행
            batch_results = await self._execute_batch(batch_items, worker)
            results.extend(batch_results)

            # 통계 업데이트
            batch_success = sum(1 for r in batch_results if not isinstance(r, Exception))
            batch_failed = len(batch_results) - batch_success

            self._stats.items_processed += len(batch_results)
            self._stats.items_succeeded += batch_success
            self._stats.items_failed += batch_failed
            self._stats.batches_completed += 1
            self._stats.current_batch_size = self._current_batch_size

            # 적응형 배치 크기 조절
            if self.config.adaptive_batch_size:
                self._adjust_batch_size(batch_success, len(batch_results))

            # 진행 콜백 호출
            if self.progress_callback:
                self._stats.total_time_ms = int((time.time() - start_time) * 1000)
                self.progress_callback(self._stats)

            idx = batch_end

            # 배치 간 지연
            if idx < len(items_list) and self.config.batch_delay_seconds > 0:
                await asyncio.sleep(self.config.batch_delay_seconds)

        total_time_ms = int((time.time() - start_time) * 1000)
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful

        return BatchResult(
            results=results,
            successful=successful,
            failed=failed,
            total_time_ms=total_time_ms,
            avg_time_per_item_ms=total_time_ms / len(results) if results else 0.0,
            retried=self._stats.items_retried,
        )

    async def _execute_batch(
        self,
        batch: list[T],
        worker: Callable[[T], Awaitable[R]],
    ) -> list[R | Exception]:
        """단일 배치 실행.

        Args:
            batch: 배치 아이템 목록
            worker: 워커 함수

        Returns:
            배치 결과 목록
        """
        tasks = [self._execute_with_retry(item, worker) for item in batch]

        if self.config.timeout_seconds:
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=self.config.return_exceptions),
                    timeout=self.config.timeout_seconds,
                )
            except TimeoutError:
                results = [TimeoutError("Batch execution timed out")] * len(batch)
        else:
            results = await asyncio.gather(*tasks, return_exceptions=self.config.return_exceptions)

        return list(results)

    async def _execute_with_retry(
        self,
        item: T,
        worker: Callable[[T], Awaitable[R]],
    ) -> R | Exception:
        """재시도 로직이 포함된 단일 아이템 실행.

        Args:
            item: 처리할 아이템
            worker: 워커 함수

        Returns:
            결과 또는 예외
        """
        last_exception: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                if self._semaphore:
                    async with self._semaphore:
                        return await worker(item)
                else:
                    return await worker(item)

            except Exception as e:
                last_exception = e

                # 레이트 리밋 감지 (429 또는 rate limit 관련 메시지)
                if self._is_rate_limit_error(e):
                    self._stats.rate_limited_count += 1
                    # 배치 크기 즉시 감소
                    self._current_batch_size = max(
                        self.config.min_batch_size,
                        self._current_batch_size // 2,
                    )

                # 재시도 가능 여부 확인
                if attempt < self.config.max_retries:
                    self._stats.items_retried += 1
                    # 지수 백오프
                    delay = self.config.retry_delay_seconds * (2**attempt)
                    await asyncio.sleep(delay)
                else:
                    break

        if self.config.return_exceptions:
            return last_exception or Exception("Unknown error")
        raise last_exception or Exception("Unknown error")

    def _adjust_batch_size(self, success_count: int, total_count: int) -> None:
        """성공률에 따라 배치 크기 조절.

        Args:
            success_count: 성공 개수
            total_count: 전체 개수
        """
        if total_count == 0:
            return

        success_rate = success_count / total_count

        if success_rate >= 0.95:
            # 성공률 95% 이상: 배치 크기 증가
            new_size = min(
                self.config.max_batch_size,
                int(self._current_batch_size * 1.2),
            )
            self._current_batch_size = max(new_size, self._current_batch_size + 1)
        elif success_rate < 0.8:
            # 성공률 80% 미만: 배치 크기 감소
            self._current_batch_size = max(
                self.config.min_batch_size,
                self._current_batch_size // 2,
            )
        # 80-95% 사이는 유지

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """레이트 리밋 오류 여부 확인.

        Args:
            error: 확인할 예외

        Returns:
            레이트 리밋 오류 여부
        """
        error_str = str(error).lower()
        return any(
            keyword in error_str
            for keyword in ["429", "rate limit", "too many requests", "quota exceeded"]
        )

    def get_current_batch_size(self) -> int:
        """현재 배치 크기 반환."""
        return self._current_batch_size

    def reset_batch_size(self) -> None:
        """배치 크기를 초기값으로 리셋."""
        self._current_batch_size = self.config.initial_batch_size


async def execute_with_progress[T, R](
    items: Sequence[T],
    worker: Callable[[T], Awaitable[R]],
    batch_size: int = 10,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[R | Exception]:
    """진행 상황 콜백과 함께 배치 실행하는 간편 함수.

    Args:
        items: 처리할 아이템들
        worker: 각 아이템을 처리하는 비동기 함수
        batch_size: 배치 크기
        on_progress: 진행 콜백 (completed, total)

    Returns:
        결과 목록

    Example:
        results = await execute_with_progress(
            items=test_cases,
            worker=evaluate_single,
            batch_size=10,
            on_progress=lambda c, t: print(f"{c}/{t} completed"),
        )
    """

    def progress_callback(stats: ExecutionStats) -> None:
        if on_progress:
            on_progress(stats.items_processed, len(items))

    config = BatchExecutorConfig(
        initial_batch_size=batch_size,
        adaptive_batch_size=False,  # 명시적 배치 크기 사용
    )
    executor: AsyncBatchExecutor[T, R] = AsyncBatchExecutor(
        config=config, progress_callback=progress_callback
    )
    result = await executor.execute(items, worker)
    return result.results


__all__ = [
    "AsyncBatchExecutor",
    "BatchExecutorConfig",
    "BatchResult",
    "ExecutionStats",
    "execute_with_progress",
]
