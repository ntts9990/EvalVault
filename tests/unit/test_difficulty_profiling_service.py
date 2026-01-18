from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.services.difficulty_profile_reporter import DifficultyProfileReporter
from evalvault.domain.services.difficulty_profiling_service import (
    DifficultyProfileRequest,
    DifficultyProfilingService,
)
from evalvault.ports.outbound.difficulty_profile_port import DifficultyProfileWriterPort
from evalvault.ports.outbound.storage_port import StoragePort


@pytest.fixture
def sample_run() -> EvaluationRun:
    return EvaluationRun(
        run_id="run-001",
        dataset_name="demo",
        model_name="gpt-5-nano",
        started_at=datetime.now(),
        metrics_evaluated=["faithfulness", "answer_relevancy"],
        results=[
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[
                    MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.8, threshold=0.7),
                ],
            ),
            TestCaseResult(
                test_case_id="tc-2",
                metrics=[
                    MetricScore(name="faithfulness", score=0.4, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.5, threshold=0.7),
                ],
            ),
            TestCaseResult(
                test_case_id="tc-3",
                metrics=[
                    MetricScore(name="faithfulness", score=0.6, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.55, threshold=0.7),
                ],
            ),
        ],
    )


@pytest.fixture
def storage_adapter(sample_run: EvaluationRun) -> StoragePort:
    adapter = MagicMock(spec=StoragePort)
    adapter.get_run.return_value = sample_run
    adapter.list_runs.return_value = [sample_run]
    return adapter


@pytest.fixture
def writer_adapter() -> DifficultyProfileWriterPort:
    return MagicMock(spec=DifficultyProfileWriterPort)


def _build_request(tmp_path: Path, **overrides) -> DifficultyProfileRequest:
    payload = {
        "dataset_name": "demo",
        "run_id": None,
        "limit_runs": None,
        "metrics": None,
        "bucket_count": 3,
        "min_samples": 1,
        "output_path": tmp_path / "difficulty.json",
        "artifacts_dir": tmp_path / "artifacts",
        "parallel": False,
        "concurrency": None,
    }
    payload.update(overrides)
    return DifficultyProfileRequest(**payload)


def test_profile_builds_envelope(storage_adapter, writer_adapter, tmp_path: Path) -> None:
    reporter = DifficultyProfileReporter(writer_adapter)
    service = DifficultyProfilingService(storage=storage_adapter, reporter=reporter)
    request = _build_request(tmp_path)
    writer_adapter.write_profile.return_value = {"dir": "dir", "index": "index"}

    envelope = service.profile(request)

    assert envelope["command"] == "profile-difficulty"
    assert envelope["status"] == "ok"
    assert envelope["data"]["bucket_count"] == 3
    assert envelope["data"]["total_cases"] == 3
    assert envelope["artifacts"] == {"dir": "dir", "index": "index"}
    storage_adapter.list_runs.assert_called_once()
    writer_adapter.write_profile.assert_called_once()


def test_profile_with_run_id(storage_adapter, writer_adapter, tmp_path: Path) -> None:
    reporter = DifficultyProfileReporter(writer_adapter)
    service = DifficultyProfilingService(storage=storage_adapter, reporter=reporter)
    request = _build_request(tmp_path, run_id="run-001", dataset_name=None)
    writer_adapter.write_profile.return_value = {"dir": "dir", "index": "index"}

    envelope = service.profile(request)

    assert envelope["data"]["run_id"] == "run-001"
    storage_adapter.get_run.assert_called_once_with("run-001")


def test_profile_requires_min_samples(storage_adapter, writer_adapter, tmp_path: Path) -> None:
    reporter = DifficultyProfileReporter(writer_adapter)
    service = DifficultyProfilingService(storage=storage_adapter, reporter=reporter)
    request = _build_request(tmp_path, min_samples=10)

    with pytest.raises(ValueError):
        service.profile(request)

    writer_adapter.write_profile.assert_not_called()
