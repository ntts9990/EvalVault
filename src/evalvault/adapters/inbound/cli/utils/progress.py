"""Progress bar utilities with ETA calculation for CLI."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    Task,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.text import Text

if TYPE_CHECKING:
    from rich.console import Console


@dataclass
class ETACalculator:
    """Calculate ETA based on elapsed time and progress."""

    total: int
    start_time: float = field(default_factory=time.time)
    _completed: int = 0

    def update(self, completed: int) -> None:
        """Update completed count."""
        self._completed = completed

    def advance(self, amount: int = 1) -> None:
        """Advance completed count by amount."""
        self._completed += amount

    @property
    def completed(self) -> int:
        return self._completed

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def eta_seconds(self) -> float | None:
        """Calculate estimated time to completion in seconds."""
        if self._completed == 0:
            return None
        if self._completed >= self.total:
            return 0.0
        rate = self._completed / self.elapsed
        remaining = self.total - self._completed
        return remaining / rate if rate > 0 else None

    @property
    def eta_formatted(self) -> str:
        """Format ETA as human-readable string."""
        eta = self.eta_seconds
        if eta is None:
            return "--:--"
        if eta <= 0:
            return "00:00"
        minutes, seconds = divmod(int(eta), 60)
        if minutes >= 60:
            hours, minutes = divmod(minutes, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def rate(self) -> float:
        """Items processed per second."""
        if self.elapsed <= 0:
            return 0.0
        return self._completed / self.elapsed

    @property
    def rate_formatted(self) -> str:
        """Format rate as human-readable string."""
        rate = self.rate
        if rate >= 1:
            return f"{rate:.1f}/s"
        if rate > 0:
            return f"{rate:.2f}/s"
        return "-/s"


class ETAColumn(ProgressColumn):
    """Renders ETA using custom format."""

    def render(self, task: Task) -> Text:
        elapsed = task.elapsed or 0.0
        if task.total is None or task.completed == 0:
            return Text("ETA --:--", style="progress.remaining")
        if task.completed >= task.total:
            return Text("ETA 00:00", style="progress.remaining")
        rate = task.completed / elapsed if elapsed > 0 else 0
        remaining = task.total - task.completed
        eta = remaining / rate if rate > 0 else 0
        minutes, seconds = divmod(int(eta), 60)
        if minutes >= 60:
            hours, minutes = divmod(minutes, 60)
            return Text(f"ETA {hours:02d}:{minutes:02d}:{seconds:02d}", style="progress.remaining")
        return Text(f"ETA {minutes:02d}:{seconds:02d}", style="progress.remaining")


class RateColumn(ProgressColumn):
    """Renders processing rate."""

    def render(self, task: Task) -> Text:
        elapsed = task.elapsed or 0.0
        if elapsed <= 0 or task.completed == 0:
            return Text("-/s", style="progress.data.speed")
        rate = task.completed / elapsed
        if rate >= 1:
            return Text(f"{rate:.1f}/s", style="progress.data.speed")
        return Text(f"{rate:.2f}/s", style="progress.data.speed")


@contextmanager
def evaluation_progress(
    console: Console,
    total: int,
    description: str = "Evaluating",
) -> Iterator[Callable[[int, str | None], None]]:
    """Show evaluation progress bar with ETA.

    Args:
        console: Rich console instance.
        total: Total number of items to process.
        description: Task description text.

    Yields:
        Update function that accepts number of completed items.

    Example:
        with evaluation_progress(console, len(dataset)) as update:
            for i, item in enumerate(dataset):
                result = process(item)
                update(i + 1)
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        ETAColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task_id = progress.add_task(description, total=total)

        def update(completed: int, message: str | None = None) -> None:
            if message:
                progress.update(task_id, completed=completed, description=message)
                return
            progress.update(task_id, completed=completed)

        yield update


@contextmanager
def batch_progress(
    console: Console,
    total_batches: int,
    total_items: int,
    description: str = "Processing batches",
) -> Iterator[Callable[[int, int], None]]:
    """Show progress for batch processing with dual tracking.

    Args:
        console: Rich console instance.
        total_batches: Total number of batches.
        total_items: Total number of items across all batches.
        description: Task description text.

    Yields:
        Update function that accepts (batch_num, items_completed).

    Example:
        with batch_progress(console, 10, 100) as update:
            for batch_idx, batch in enumerate(batches):
                results = process_batch(batch)
                update(batch_idx + 1, (batch_idx + 1) * batch_size)
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TextColumn("[cyan]{task.fields[batch_info]}[/cyan]"),
        TaskProgressColumn(),
        ETAColumn(),
        console=console,
        transient=False,
    ) as progress:
        task_id = progress.add_task(
            description,
            total=total_items,
            batch_info=f"Batch 0/{total_batches}",
        )

        def update(batch_num: int, items_completed: int) -> None:
            progress.update(
                task_id,
                completed=items_completed,
                batch_info=f"Batch {batch_num}/{total_batches}",
            )

        yield update


@contextmanager
def streaming_progress(
    console: Console,
    description: str = "Streaming",
) -> Iterator[Callable[[int, int | None, str | None], None]]:
    """Show progress for streaming evaluation where total may change.

    Args:
        console: Rich console instance.
        description: Task description text.

    Yields:
        Update function that accepts (completed, new_total).

    Example:
        with streaming_progress(console) as update:
            for chunk_idx, chunk in enumerate(stream_chunks()):
                results = process_chunk(chunk)
                update(chunk_idx + 1, estimated_total)
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        MofNCompleteColumn(),
        RateColumn(),
        ETAColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task_id = progress.add_task(description, total=None)

        def update(
            completed: int,
            total: int | None = None,
            message: str | None = None,
        ) -> None:
            if total is not None:
                progress.update(task_id, completed=completed, total=total)
            elif completed is not None:
                progress.update(task_id, completed=completed)
            if message:
                progress.update(task_id, description=message)

        yield update


def progress_iterate[T](
    console: Console,
    items: Sequence[T],
    description: str = "Processing",
) -> Iterator[T]:
    """Iterate with progress bar.

    Args:
        console: Rich console instance.
        items: Sequence of items to iterate over.
        description: Task description text.

    Yields:
        Items from the sequence.

    Example:
        for item in progress_iterate(console, dataset.test_cases, "Evaluating"):
            result = evaluate(item)
    """
    total = len(items)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        ETAColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task_id = progress.add_task(description, total=total)
        for item in items:
            yield item
            progress.advance(task_id)


@contextmanager
def multi_stage_progress(
    console: Console,
    stages: Sequence[tuple[str, int]],
) -> Iterator[Callable[[int, int], None]]:
    """Show progress for multi-stage processing.

    Args:
        console: Rich console instance.
        stages: List of (stage_name, item_count) tuples.

    Yields:
        Update function that accepts (stage_index, items_completed_in_stage).

    Example:
        stages = [("Loading", 1), ("Evaluating", 100), ("Saving", 1)]
        with multi_stage_progress(console, stages) as update:
            load_data()
            update(0, 1)
            for i, item in enumerate(items):
                evaluate(item)
                update(1, i + 1)
            save_results()
            update(2, 1)
    """
    total_items = sum(count for _, count in stages)
    stage_offsets = []
    offset = 0
    for _, count in stages:
        stage_offsets.append(offset)
        offset += count

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        ETAColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task_id = progress.add_task(stages[0][0] if stages else "Processing", total=total_items)
        current_stage = 0

        def update(stage_index: int, items_completed: int) -> None:
            nonlocal current_stage
            if stage_index != current_stage and stage_index < len(stages):
                current_stage = stage_index
                progress.update(task_id, description=stages[stage_index][0])
            absolute_completed = stage_offsets[stage_index] + items_completed
            progress.update(task_id, completed=absolute_completed)

        yield update


__all__ = [
    "ETACalculator",
    "ETAColumn",
    "RateColumn",
    "evaluation_progress",
    "batch_progress",
    "streaming_progress",
    "progress_iterate",
    "multi_stage_progress",
]
