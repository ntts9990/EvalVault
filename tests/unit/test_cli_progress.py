"""Unit tests for CLI progress utilities."""

from __future__ import annotations

import time

from rich.console import Console

from evalvault.adapters.inbound.cli.utils.progress import (
    ETACalculator,
    batch_progress,
    evaluation_progress,
    multi_stage_progress,
    progress_iterate,
    streaming_progress,
)


class TestETACalculator:
    """Tests for ETACalculator class."""

    def test_initial_state(self) -> None:
        calc = ETACalculator(total=100)
        assert calc.total == 100
        assert calc.completed == 0
        assert calc.eta_seconds is None
        assert calc.eta_formatted == "--:--"

    def test_update_completed(self) -> None:
        calc = ETACalculator(total=100)
        calc.update(50)
        assert calc.completed == 50

    def test_advance(self) -> None:
        calc = ETACalculator(total=100)
        calc.advance(10)
        assert calc.completed == 10
        calc.advance(5)
        assert calc.completed == 15

    def test_elapsed_time(self) -> None:
        calc = ETACalculator(total=100)
        time.sleep(0.1)
        assert calc.elapsed >= 0.1

    def test_eta_seconds_calculation(self) -> None:
        # Create calculator with a known start time
        calc = ETACalculator(total=100, start_time=time.time() - 10)
        calc.update(50)
        # 50 items in 10 seconds = 5 items/sec, 50 remaining = 10 seconds ETA
        eta = calc.eta_seconds
        assert eta is not None
        assert 9 <= eta <= 11  # Allow some tolerance

    def test_eta_formatted_minutes(self) -> None:
        calc = ETACalculator(total=100, start_time=time.time() - 10)
        calc.update(50)
        formatted = calc.eta_formatted
        # Should be around "00:10"
        assert ":" in formatted

    def test_eta_formatted_hours(self) -> None:
        # Simulate a very slow rate
        calc = ETACalculator(total=10000, start_time=time.time() - 1)
        calc.update(1)
        # 1 item in 1 second, 9999 remaining = 9999 seconds ETA (about 2.7 hours)
        formatted = calc.eta_formatted
        assert formatted.count(":") >= 1  # Has at least MM:SS format

    def test_eta_complete(self) -> None:
        calc = ETACalculator(total=100)
        calc.update(100)
        assert calc.eta_seconds == 0.0
        assert calc.eta_formatted == "00:00"

    def test_rate_calculation(self) -> None:
        calc = ETACalculator(total=100, start_time=time.time() - 10)
        calc.update(50)
        assert 4.5 <= calc.rate <= 5.5  # Allow tolerance

    def test_rate_formatted(self) -> None:
        calc = ETACalculator(total=100, start_time=time.time() - 10)
        calc.update(50)
        formatted = calc.rate_formatted
        assert "/s" in formatted


class TestEvaluationProgress:
    """Tests for evaluation_progress context manager."""

    def test_evaluation_progress_context(self) -> None:
        console = Console(record=True, force_terminal=True)
        with evaluation_progress(console, 10, "Testing") as update:
            for i in range(10):
                update(i + 1)
        # Should complete without error
        output = console.export_text()
        assert "10/10" in output or "100%" in output

    def test_evaluation_progress_partial(self) -> None:
        console = Console(record=True, force_terminal=True)
        with evaluation_progress(console, 100, "Evaluating") as update:
            update(50)
        # Should not error even if not completed


class TestBatchProgress:
    """Tests for batch_progress context manager."""

    def test_batch_progress_context(self) -> None:
        console = Console(record=True, force_terminal=True)
        with batch_progress(console, 5, 50, "Processing batches") as update:
            for batch_idx in range(5):
                update(batch_idx + 1, (batch_idx + 1) * 10)
        # Should complete without error


class TestStreamingProgress:
    """Tests for streaming_progress context manager."""

    def test_streaming_progress_context(self) -> None:
        console = Console(record=True, force_terminal=True)
        with streaming_progress(console, "Streaming") as update:
            update(10)
            update(20, 100)  # Update with total
        # Should complete without error


class TestProgressIterate:
    """Tests for progress_iterate generator."""

    def test_progress_iterate_list(self) -> None:
        console = Console(record=True, force_terminal=True)
        items = [1, 2, 3, 4, 5]
        result = list(progress_iterate(console, items, "Processing"))
        assert result == items

    def test_progress_iterate_empty(self) -> None:
        console = Console(record=True, force_terminal=True)
        result = list(progress_iterate(console, [], "Processing"))
        assert result == []


class TestMultiStageProgress:
    """Tests for multi_stage_progress context manager."""

    def test_multi_stage_progress_context(self) -> None:
        console = Console(record=True, force_terminal=True)
        stages = [
            ("Loading", 2),
            ("Processing", 5),
            ("Saving", 1),
        ]
        with multi_stage_progress(console, stages) as update:
            update(0, 1)
            update(0, 2)
            for i in range(5):
                update(1, i + 1)
            update(2, 1)
        # Should complete without error

    def test_multi_stage_progress_stage_transition(self) -> None:
        console = Console(record=True, force_terminal=True)
        stages = [
            ("Stage1", 1),
            ("Stage2", 1),
        ]
        with multi_stage_progress(console, stages) as update:
            update(0, 1)
            update(1, 1)
        # Should handle stage transitions


class TestProgressModuleExports:
    """Tests to verify module exports."""

    def test_all_exports_available(self) -> None:
        from evalvault.adapters.inbound.cli.utils import progress

        assert hasattr(progress, "ETACalculator")
        assert hasattr(progress, "evaluation_progress")
        assert hasattr(progress, "batch_progress")
        assert hasattr(progress, "streaming_progress")
        assert hasattr(progress, "progress_iterate")
        assert hasattr(progress, "multi_stage_progress")

    def test_exports_from_init(self) -> None:
        from evalvault.adapters.inbound.cli.utils import (
            ETACalculator,
            batch_progress,
            evaluation_progress,
            multi_stage_progress,
            progress_iterate,
            streaming_progress,
        )

        assert ETACalculator is not None
        assert evaluation_progress is not None
        assert batch_progress is not None
        assert streaming_progress is not None
        assert progress_iterate is not None
        assert multi_stage_progress is not None
