"""Integration tests for storage flow with RagasEvaluator."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.domain.entities import Dataset, EvaluationRun, MetricScore, TestCase, TestCaseResult


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing."""
    return Dataset(
        name="insurance-integration-test",
        version="1.0.0",
        test_cases=[
            TestCase(
                id="tc-int-001",
                question="보험금은 얼마인가요?",
                answer="보험금은 1억원입니다.",
                contexts=["이 보험의 사망 보장금은 1억원입니다."],
                ground_truth="1억원",
            ),
            TestCase(
                id="tc-int-002",
                question="보험료는 얼마인가요?",
                answer="월 보험료는 5만원입니다.",
                contexts=["월 납입 보험료는 50,000원입니다."],
                ground_truth="5만원",
            ),
        ],
    )


class TestStorageIntegration:
    """Integration tests for storage adapter with evaluation workflow."""

    def test_save_and_retrieve_full_evaluation_run(self, temp_db, sample_dataset):
        """Test complete workflow: create run, save, and retrieve."""
        storage = SQLiteStorageAdapter(db_path=temp_db)

        # Create evaluation run with results
        run = EvaluationRun(
            run_id="integration-test-001",
            dataset_name=sample_dataset.name,
            dataset_version=sample_dataset.version,
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            metrics_evaluated=["faithfulness", "answer_relevancy"],
            thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7},
        )

        # Add test case results
        for tc in sample_dataset.test_cases:
            result = TestCaseResult(
                test_case_id=tc.id,
                metrics=[
                    MetricScore(name="faithfulness", score=0.85, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.90, threshold=0.7),
                ],
                tokens_used=500,
                latency_ms=1000,
                question=tc.question,
                answer=tc.answer,
                contexts=tc.contexts,
                ground_truth=tc.ground_truth,
            )
            run.results.append(result)

        run.finished_at = datetime.now()
        run.total_tokens = sum(r.tokens_used for r in run.results)

        # Save and retrieve
        run_id = storage.save_run(run)
        retrieved_run = storage.get_run(run_id)

        # Verify
        assert retrieved_run.run_id == run.run_id
        assert retrieved_run.dataset_name == sample_dataset.name
        assert len(retrieved_run.results) == len(sample_dataset.test_cases)
        assert retrieved_run.pass_rate > 0

    def test_multiple_runs_same_dataset(self, temp_db, sample_dataset):
        """Test storing multiple evaluation runs for the same dataset."""
        storage = SQLiteStorageAdapter(db_path=temp_db)

        # Create two runs with different models
        for model in ["gpt-5-nano", "gpt-4"]:
            run = EvaluationRun(
                run_id=f"run-{model}",
                dataset_name=sample_dataset.name,
                dataset_version=sample_dataset.version,
                model_name=model,
                started_at=datetime.now(),
            )
            storage.save_run(run)

        # Retrieve and filter
        all_runs = storage.list_runs()
        assert len(all_runs) == 2

        gpt5_runs = storage.list_runs(model_name="gpt-5-nano")
        assert len(gpt5_runs) == 1
        assert gpt5_runs[0].model_name == "gpt-5-nano"

    def test_history_tracking_over_time(self, temp_db):
        """Test tracking evaluation history over multiple days."""
        storage = SQLiteStorageAdapter(db_path=temp_db)

        # Create runs on different dates
        dates = [
            datetime(2025, 1, 1, 10, 0, 0),
            datetime(2025, 1, 2, 10, 0, 0),
            datetime(2025, 1, 3, 10, 0, 0),
        ]

        for i, date in enumerate(dates):
            run = EvaluationRun(
                run_id=f"run-{i}",
                dataset_name="insurance-qa",
                dataset_version="1.0.0",
                model_name="gpt-5-nano",
                started_at=date,
            )
            storage.save_run(run)

        # Retrieve in reverse chronological order
        runs = storage.list_runs()
        assert len(runs) == 3
        assert runs[0].started_at > runs[1].started_at > runs[2].started_at

    def test_export_and_import_pattern(self, temp_db, sample_dataset):
        """Test pattern for exporting run data for analysis."""
        storage = SQLiteStorageAdapter(db_path=temp_db)

        # Create and save run
        run = EvaluationRun(
            run_id="export-test",
            dataset_name=sample_dataset.name,
            dataset_version=sample_dataset.version,
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            finished_at=datetime.now(),
            metrics_evaluated=["faithfulness"],
            thresholds={"faithfulness": 0.7},
        )

        result = TestCaseResult(
            test_case_id="tc-001",
            metrics=[MetricScore(name="faithfulness", score=0.85, threshold=0.7)],
            tokens_used=100,
        )
        run.results.append(result)

        storage.save_run(run)

        # Retrieve and export to dict
        retrieved = storage.get_run("export-test")
        summary = retrieved.to_summary_dict()

        assert summary["run_id"] == "export-test"
        assert "avg_faithfulness" in summary
        assert summary["total_test_cases"] == 1

    def test_delete_run_cleanup(self, temp_db, sample_dataset):
        """Test that deleting a run properly cleans up all related data."""
        storage = SQLiteStorageAdapter(db_path=temp_db)

        # Create run with results
        run = EvaluationRun(
            run_id="delete-test",
            dataset_name=sample_dataset.name,
            dataset_version=sample_dataset.version,
            model_name="gpt-5-nano",
            started_at=datetime.now(),
        )

        result = TestCaseResult(
            test_case_id="tc-001",
            metrics=[
                MetricScore(name="faithfulness", score=0.85, threshold=0.7),
                MetricScore(name="answer_relevancy", score=0.90, threshold=0.7),
            ],
        )
        run.results.append(result)

        storage.save_run(run)

        # Verify it exists
        assert storage.get_run("delete-test") is not None

        # Delete and verify
        deleted = storage.delete_run("delete-test")
        assert deleted is True

        # Should raise KeyError
        with pytest.raises(KeyError):
            storage.get_run("delete-test")

    def test_storage_persists_across_instances(self, temp_db, sample_dataset):
        """Test that data persists when creating new adapter instances."""
        # First instance - save data
        storage1 = SQLiteStorageAdapter(db_path=temp_db)
        run = EvaluationRun(
            run_id="persist-test",
            dataset_name=sample_dataset.name,
            dataset_version=sample_dataset.version,
            model_name="gpt-5-nano",
            started_at=datetime.now(),
        )
        storage1.save_run(run)

        # Second instance - should be able to read the data
        storage2 = SQLiteStorageAdapter(db_path=temp_db)
        retrieved = storage2.get_run("persist-test")

        assert retrieved.run_id == "persist-test"
        assert retrieved.dataset_name == sample_dataset.name

    def test_concurrent_writes_different_runs(self, temp_db):
        """Test that multiple runs can be written without conflicts."""
        storage = SQLiteStorageAdapter(db_path=temp_db)

        # Create multiple runs
        runs = []
        for i in range(10):
            run = EvaluationRun(
                run_id=f"concurrent-{i}",
                dataset_name="test-dataset",
                dataset_version="1.0.0",
                model_name="gpt-5-nano",
                started_at=datetime.now(),
            )
            storage.save_run(run)
            runs.append(run)

        # Verify all were saved
        retrieved_runs = storage.list_runs(limit=20)
        assert len(retrieved_runs) == 10

        # Verify each can be retrieved individually
        for run in runs:
            retrieved = storage.get_run(run.run_id)
            assert retrieved.run_id == run.run_id
