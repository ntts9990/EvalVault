"""Unit tests for SQLiteBenchmarkStorageAdapter.

Tests cover CRUD operations for BenchmarkRun entities.
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from evalvault.adapters.outbound.storage.benchmark_storage_adapter import (
    SQLiteBenchmarkStorageAdapter,
)
from evalvault.domain.entities.benchmark_run import (
    BenchmarkRun,
    BenchmarkStatus,
    BenchmarkTaskScore,
    BenchmarkType,
)


@pytest.fixture
def temp_db() -> Path:
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        return Path(f.name)


@pytest.fixture
def adapter(temp_db: Path) -> SQLiteBenchmarkStorageAdapter:
    """Create adapter with temporary database."""
    return SQLiteBenchmarkStorageAdapter(db_path=temp_db)


@pytest.fixture
def sample_run() -> BenchmarkRun:
    """Create a sample benchmark run for testing."""
    return BenchmarkRun.create(
        benchmark_type=BenchmarkType.KMMLU,
        model_name="gemma3:1b",
        backend="ollama",
        tasks=["kmmlu_insurance", "kmmlu_finance"],
        num_fewshot=5,
        metadata={"subjects": ["Insurance", "Finance"], "limit": 10},
    )


@pytest.fixture
def completed_run() -> BenchmarkRun:
    """Create a completed benchmark run with task scores."""
    run = BenchmarkRun.create(
        benchmark_type=BenchmarkType.KMMLU,
        model_name="gemma3:1b",
        backend="ollama",
        tasks=["kmmlu_insurance", "kmmlu_finance"],
        num_fewshot=5,
    )
    run.start()
    run.complete(
        [
            BenchmarkTaskScore(
                task_name="kmmlu_insurance",
                accuracy=0.75,
                num_samples=100,
                metrics={"acc,none": 0.75, "acc_stderr,none": 0.04},
                version="1",
            ),
            BenchmarkTaskScore(
                task_name="kmmlu_finance",
                accuracy=0.80,
                num_samples=100,
                metrics={"acc,none": 0.80, "acc_stderr,none": 0.03},
                version="1",
            ),
        ]
    )
    return run


class TestSQLiteBenchmarkStorageAdapter:
    """Test suite for SQLiteBenchmarkStorageAdapter."""

    def test_save_and_get_pending_run(
        self, adapter: SQLiteBenchmarkStorageAdapter, sample_run: BenchmarkRun
    ) -> None:
        """Test saving and retrieving a pending benchmark run."""
        # When
        saved_id = adapter.save_benchmark_run(sample_run)

        # Then
        assert saved_id == sample_run.run_id

        retrieved = adapter.get_benchmark_run(sample_run.run_id)
        assert retrieved.run_id == sample_run.run_id
        assert retrieved.benchmark_type == BenchmarkType.KMMLU
        assert retrieved.model_name == "gemma3:1b"
        assert retrieved.backend == "ollama"
        assert retrieved.tasks == ["kmmlu_insurance", "kmmlu_finance"]
        assert retrieved.status == BenchmarkStatus.PENDING
        assert retrieved.num_fewshot == 5
        assert retrieved.metadata == {"subjects": ["Insurance", "Finance"], "limit": 10}

    def test_save_and_get_completed_run(
        self, adapter: SQLiteBenchmarkStorageAdapter, completed_run: BenchmarkRun
    ) -> None:
        """Test saving and retrieving a completed benchmark run with task scores."""
        # When
        adapter.save_benchmark_run(completed_run)

        # Then
        retrieved = adapter.get_benchmark_run(completed_run.run_id)
        assert retrieved.status == BenchmarkStatus.COMPLETED
        assert len(retrieved.task_scores) == 2
        assert retrieved.overall_accuracy is not None
        assert retrieved.overall_accuracy == pytest.approx(0.775, rel=0.01)
        assert retrieved.duration_seconds >= 0

        # Verify task scores
        insurance_score = next(
            ts for ts in retrieved.task_scores if ts.task_name == "kmmlu_insurance"
        )
        assert insurance_score.accuracy == 0.75
        assert insurance_score.num_samples == 100
        assert insurance_score.metrics["acc,none"] == 0.75

    def test_save_failed_run(self, adapter: SQLiteBenchmarkStorageAdapter) -> None:
        """Test saving a failed benchmark run."""
        # Given
        run = BenchmarkRun.create(
            benchmark_type=BenchmarkType.KMMLU,
            model_name="gemma3:1b",
            backend="ollama",
            tasks=["kmmlu_invalid"],
        )
        run.start()
        run.fail("Task not found: kmmlu_invalid")

        # When
        adapter.save_benchmark_run(run)

        # Then
        retrieved = adapter.get_benchmark_run(run.run_id)
        assert retrieved.status == BenchmarkStatus.FAILED
        assert retrieved.error_message == "Task not found: kmmlu_invalid"

    def test_get_nonexistent_run_raises_keyerror(
        self, adapter: SQLiteBenchmarkStorageAdapter
    ) -> None:
        """Test that getting a nonexistent run raises KeyError."""
        with pytest.raises(KeyError, match="Benchmark run not found"):
            adapter.get_benchmark_run("nonexistent_run_id")

    def test_list_runs_empty(self, adapter: SQLiteBenchmarkStorageAdapter) -> None:
        """Test listing runs when database is empty."""
        runs = adapter.list_benchmark_runs()
        assert runs == []

    def test_list_runs_with_data(
        self, adapter: SQLiteBenchmarkStorageAdapter, completed_run: BenchmarkRun
    ) -> None:
        """Test listing runs after saving data."""
        # Given
        adapter.save_benchmark_run(completed_run)

        # When
        runs = adapter.list_benchmark_runs()

        # Then
        assert len(runs) == 1
        assert runs[0].run_id == completed_run.run_id

    def test_list_runs_filter_by_benchmark_type(
        self, adapter: SQLiteBenchmarkStorageAdapter
    ) -> None:
        """Test filtering runs by benchmark type."""
        # Given
        kmmlu_run = BenchmarkRun.create(
            benchmark_type=BenchmarkType.KMMLU,
            model_name="gemma3:1b",
            backend="ollama",
            tasks=["kmmlu_insurance"],
        )
        custom_run = BenchmarkRun.create(
            benchmark_type=BenchmarkType.CUSTOM,
            model_name="gemma3:1b",
            backend="ollama",
            tasks=["custom_task"],
        )
        adapter.save_benchmark_run(kmmlu_run)
        adapter.save_benchmark_run(custom_run)

        # When
        kmmlu_runs = adapter.list_benchmark_runs(benchmark_type="kmmlu")
        custom_runs = adapter.list_benchmark_runs(benchmark_type="custom")

        # Then
        assert len(kmmlu_runs) == 1
        assert kmmlu_runs[0].benchmark_type == BenchmarkType.KMMLU

        assert len(custom_runs) == 1
        assert custom_runs[0].benchmark_type == BenchmarkType.CUSTOM

    def test_list_runs_filter_by_model_name(self, adapter: SQLiteBenchmarkStorageAdapter) -> None:
        """Test filtering runs by model name."""
        # Given
        run1 = BenchmarkRun.create(
            benchmark_type=BenchmarkType.KMMLU,
            model_name="gemma3:1b",
            backend="ollama",
            tasks=["kmmlu_insurance"],
        )
        run2 = BenchmarkRun.create(
            benchmark_type=BenchmarkType.KMMLU,
            model_name="llama3:8b",
            backend="ollama",
            tasks=["kmmlu_insurance"],
        )
        adapter.save_benchmark_run(run1)
        adapter.save_benchmark_run(run2)

        # When
        gemma_runs = adapter.list_benchmark_runs(model_name="gemma3:1b")

        # Then
        assert len(gemma_runs) == 1
        assert gemma_runs[0].model_name == "gemma3:1b"

    def test_list_runs_limit(self, adapter: SQLiteBenchmarkStorageAdapter) -> None:
        """Test limiting the number of returned runs."""
        # Given
        for i in range(5):
            run = BenchmarkRun.create(
                benchmark_type=BenchmarkType.KMMLU,
                model_name=f"model_{i}",
                backend="ollama",
                tasks=["kmmlu_insurance"],
            )
            adapter.save_benchmark_run(run)

        # When
        runs = adapter.list_benchmark_runs(limit=3)

        # Then
        assert len(runs) == 3

    def test_update_run(
        self, adapter: SQLiteBenchmarkStorageAdapter, sample_run: BenchmarkRun
    ) -> None:
        """Test updating an existing run."""
        # Given
        adapter.save_benchmark_run(sample_run)

        # When - update the run
        sample_run.start()
        sample_run.complete(
            [
                BenchmarkTaskScore(
                    task_name="kmmlu_insurance",
                    accuracy=0.85,
                    num_samples=50,
                    metrics={"acc,none": 0.85},
                )
            ]
        )
        adapter.save_benchmark_run(sample_run)

        # Then
        retrieved = adapter.get_benchmark_run(sample_run.run_id)
        assert retrieved.status == BenchmarkStatus.COMPLETED
        assert retrieved.overall_accuracy == 0.85

    def test_delete_run(
        self, adapter: SQLiteBenchmarkStorageAdapter, sample_run: BenchmarkRun
    ) -> None:
        """Test deleting a benchmark run."""
        # Given
        adapter.save_benchmark_run(sample_run)

        # When
        deleted = adapter.delete_benchmark_run(sample_run.run_id)

        # Then
        assert deleted is True
        with pytest.raises(KeyError):
            adapter.get_benchmark_run(sample_run.run_id)

    def test_delete_nonexistent_run(self, adapter: SQLiteBenchmarkStorageAdapter) -> None:
        """Test deleting a nonexistent run returns False."""
        deleted = adapter.delete_benchmark_run("nonexistent_run_id")
        assert deleted is False

    def test_save_run_with_phoenix_trace_id(self, adapter: SQLiteBenchmarkStorageAdapter) -> None:
        """Test saving a run with Phoenix trace ID."""
        # Given
        run = BenchmarkRun.create(
            benchmark_type=BenchmarkType.KMMLU,
            model_name="gemma3:1b",
            backend="ollama",
            tasks=["kmmlu_insurance"],
        )
        run.set_phoenix_trace_id("phoenix_trace_123")

        # When
        adapter.save_benchmark_run(run)

        # Then
        retrieved = adapter.get_benchmark_run(run.run_id)
        assert retrieved.phoenix_trace_id == "phoenix_trace_123"

    def test_run_serialization_roundtrip(self, adapter: SQLiteBenchmarkStorageAdapter) -> None:
        """Test that all fields survive serialization roundtrip."""
        # Given
        run = BenchmarkRun(
            run_id="bench_test123",
            benchmark_type=BenchmarkType.MMLU,
            model_name="gpt-4",
            backend="openai",
            tasks=["mmlu_math", "mmlu_physics"],
            status=BenchmarkStatus.COMPLETED,
            task_scores=[
                BenchmarkTaskScore(
                    task_name="mmlu_math",
                    accuracy=0.90,
                    num_samples=200,
                    metrics={"acc,none": 0.90, "custom_metric": 0.85},
                    version="2",
                ),
            ],
            overall_accuracy=0.90,
            num_fewshot=3,
            started_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
            finished_at=datetime(2024, 1, 1, 10, 30, 0, tzinfo=UTC),
            duration_seconds=1800.0,
            error_message=None,
            phoenix_trace_id="trace_abc",
            metadata={"experiment": "test", "version": 2},
        )

        # When
        adapter.save_benchmark_run(run)
        retrieved = adapter.get_benchmark_run(run.run_id)

        # Then
        assert retrieved.run_id == run.run_id
        assert retrieved.benchmark_type == run.benchmark_type
        assert retrieved.model_name == run.model_name
        assert retrieved.backend == run.backend
        assert retrieved.tasks == run.tasks
        assert retrieved.status == run.status
        assert retrieved.overall_accuracy == run.overall_accuracy
        assert retrieved.num_fewshot == run.num_fewshot
        assert retrieved.duration_seconds == run.duration_seconds
        assert retrieved.phoenix_trace_id == run.phoenix_trace_id
        assert retrieved.metadata == run.metadata

        # Verify task scores
        assert len(retrieved.task_scores) == 1
        ts = retrieved.task_scores[0]
        assert ts.task_name == "mmlu_math"
        assert ts.accuracy == 0.90
        assert ts.num_samples == 200
        assert ts.metrics == {"acc,none": 0.90, "custom_metric": 0.85}
        assert ts.version == "2"
