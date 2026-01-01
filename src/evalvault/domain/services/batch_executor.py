"""Async batching helpers for evaluator performance."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence


def chunked[T](items: Sequence[T], size: int) -> list[Sequence[T]]:
    """Split a sequence into evenly sized chunks."""

    if size <= 0:
        raise ValueError("size must be positive")
    return [items[i : i + size] for i in range(0, len(items), size)]


async def run_in_batches[T, R](
    items: Sequence[T],
    *,
    worker: Callable[[T], Awaitable[R]],
    batch_size: int = 10,
    return_exceptions: bool = True,
) -> list[R | Exception]:
    """Execute awaitable tasks in batches.

    This helper mirrors the plan in `docs/IMPROVEMENT_PLAN.md` by chunking the
    workload and dispatching each chunk via ``asyncio.gather`` so that large
    evaluation sets (1,000+ 테스트 케이스 등) can run with predictable memory usage.
    """

    results: list[R | Exception] = []
    for batch in chunked(items, batch_size):
        tasks = [worker(item) for item in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=return_exceptions)
        results.extend(batch_results)
    return results


__all__ = ["chunked", "run_in_batches"]
