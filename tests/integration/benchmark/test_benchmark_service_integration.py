"""Integration tests for BenchmarkService with storage and mocked benchmark adapter."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from evalvault.adapters.outbound.storage.benchmark_storage_adapter import (
    SQLiteBenchmarkStorageAdapter,
)
from evalvault.domain.entities.benchmark_run import (
    BenchmarkStatus,
    BenchmarkType,
)
from evalvault.domain.services.benchmark_service import BenchmarkService
from evalvault.ports.outbound.benchmark_port import (
    BenchmarkBackend,
    BenchmarkPort,
    BenchmarkRequest,
    BenchmarkResponse,
    BenchmarkTaskResult,
)


@pytest.fixture
def temp_db() -> Path:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        return Path(f.name)


@pytest.fixture
def storage_adapter(temp_db: Path) -> SQLiteBenchmarkStorageAdapter:
    return SQLiteBenchmarkStorageAdapter(db_path=temp_db)


@pytest.fixture
def mock_benchmark_adapter() -> MagicMock:
    adapter = MagicMock(spec=BenchmarkPort)

    def mock_run_benchmark(request: BenchmarkRequest) -> BenchmarkResponse:
        response = BenchmarkResponse(
            model_name="gemma3:1b",
            backend=request.backend,
            total_time_seconds=10.5,
        )
        for task in request.tasks:
            response.results[task] = BenchmarkTaskResult(
                task_name=task,
                metrics={"acc,none": 0.75, "acc_stderr,none": 0.04},
                num_samples=100,
                version="1",
            )
        return response

    adapter.run_benchmark.side_effect = mock_run_benchmark
    return adapter


@pytest.fixture
def benchmark_service(
    mock_benchmark_adapter: MagicMock,
    storage_adapter: SQLiteBenchmarkStorageAdapter,
) -> BenchmarkService:
    return BenchmarkService(
        benchmark_adapter=mock_benchmark_adapter,
        storage_adapter=storage_adapter,
    )


class TestBenchmarkServiceIntegration:
    def test_run_kmmlu_with_ollama_backend_saves_to_storage(
        self,
        benchmark_service: BenchmarkService,
        storage_adapter: SQLiteBenchmarkStorageAdapter,
    ) -> None:
        # When
        run = benchmark_service.run_kmmlu(
            subjects=["Insurance", "Finance"],
            model_name="gemma3:1b",
            backend=BenchmarkBackend.OLLAMA,
            num_fewshot=5,
            limit=10,
        )

        # Then - verify run completed
        assert run.status == BenchmarkStatus.COMPLETED
        assert run.model_name == "gemma3:1b"
        assert run.backend == "ollama"
        assert len(run.task_scores) == 2
        assert run.overall_accuracy is not None
        assert run.overall_accuracy > 0

        # Then - verify saved to storage
        retrieved = storage_adapter.get_benchmark_run(run.run_id)
        assert retrieved.run_id == run.run_id
        assert retrieved.status == BenchmarkStatus.COMPLETED
        assert len(retrieved.task_scores) == 2

    def test_run_kmmlu_stores_metadata(
        self,
        benchmark_service: BenchmarkService,
        storage_adapter: SQLiteBenchmarkStorageAdapter,
    ) -> None:
        # When
        run = benchmark_service.run_kmmlu(
            subjects=["Insurance"],
            model_name="gemma3:1b",
            backend=BenchmarkBackend.OLLAMA,
            num_fewshot=5,
            limit=10,
        )

        # Then
        retrieved = storage_adapter.get_benchmark_run(run.run_id)
        assert retrieved.metadata["subjects"] == ["Insurance"]
        assert retrieved.metadata["limit"] == 10

    def test_failed_benchmark_is_saved(
        self,
        storage_adapter: SQLiteBenchmarkStorageAdapter,
    ) -> None:
        # Given - adapter that fails
        failing_adapter = MagicMock(spec=BenchmarkPort)
        failing_adapter.run_benchmark.return_value = BenchmarkResponse(
            error="Connection refused",
            backend=BenchmarkBackend.OLLAMA,
        )

        service = BenchmarkService(
            benchmark_adapter=failing_adapter,
            storage_adapter=storage_adapter,
        )

        # When
        run = service.run_kmmlu(
            subjects=["Insurance"],
            model_name="gemma3:1b",
            backend=BenchmarkBackend.OLLAMA,
        )

        # Then
        assert run.status == BenchmarkStatus.FAILED
        assert run.error_message == "Connection refused"

        retrieved = storage_adapter.get_benchmark_run(run.run_id)
        assert retrieved.status == BenchmarkStatus.FAILED
        assert retrieved.error_message == "Connection refused"

    def test_list_runs_returns_saved_runs(
        self,
        benchmark_service: BenchmarkService,
        storage_adapter: SQLiteBenchmarkStorageAdapter,
    ) -> None:
        # Given
        benchmark_service.run_kmmlu(
            subjects=["Insurance"],
            model_name="gemma3:1b",
            backend=BenchmarkBackend.OLLAMA,
        )
        benchmark_service.run_kmmlu(
            subjects=["Finance"],
            model_name="llama3:8b",
            backend=BenchmarkBackend.OLLAMA,
        )

        # When
        runs = benchmark_service.list_runs()

        # Then
        assert len(runs) == 2

    def test_list_runs_filter_by_model(
        self,
        benchmark_service: BenchmarkService,
        storage_adapter: SQLiteBenchmarkStorageAdapter,
    ) -> None:
        # Given
        benchmark_service.run_kmmlu(
            subjects=["Insurance"],
            model_name="gemma3:1b",
            backend=BenchmarkBackend.OLLAMA,
        )
        benchmark_service.run_kmmlu(
            subjects=["Finance"],
            model_name="llama3:8b",
            backend=BenchmarkBackend.OLLAMA,
        )

        # When
        runs = benchmark_service.list_runs(model_name="gemma3:1b")

        # Then
        assert len(runs) == 1
        assert runs[0].model_name == "gemma3:1b"

    def test_get_run_returns_saved_run(
        self,
        benchmark_service: BenchmarkService,
    ) -> None:
        # Given
        run = benchmark_service.run_kmmlu(
            subjects=["Insurance"],
            model_name="gemma3:1b",
            backend=BenchmarkBackend.OLLAMA,
        )

        # When
        retrieved = benchmark_service.get_run(run.run_id)

        # Then
        assert retrieved is not None
        assert retrieved.run_id == run.run_id

    def test_get_nonexistent_run_returns_none(
        self,
        benchmark_service: BenchmarkService,
    ) -> None:
        # When
        result = benchmark_service.get_run("nonexistent_id")

        # Then
        assert result is None

    def test_run_custom_benchmark(
        self,
        benchmark_service: BenchmarkService,
    ) -> None:
        # When
        run = benchmark_service.run_custom(
            tasks=["custom_task_1", "custom_task_2"],
            model_name="gemma3:1b",
            backend=BenchmarkBackend.OLLAMA,
            num_fewshot=0,
        )

        # Then
        assert run.status == BenchmarkStatus.COMPLETED
        assert run.benchmark_type == BenchmarkType.CUSTOM
        assert len(run.task_scores) == 2

    def test_task_scores_have_correct_metrics(
        self,
        benchmark_service: BenchmarkService,
    ) -> None:
        # When
        run = benchmark_service.run_kmmlu(
            subjects=["Insurance"],
            model_name="gemma3:1b",
            backend=BenchmarkBackend.OLLAMA,
        )

        # Then
        assert len(run.task_scores) == 1
        score = run.task_scores[0]
        assert score.task_name == "kmmlu_direct_insurance"
        assert score.accuracy == 0.75
        assert score.num_samples == 100
        assert score.metrics["acc,none"] == 0.75
