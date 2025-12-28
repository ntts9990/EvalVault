"""Unit tests for SQLite storage adapter."""

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult


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
def storage_adapter(temp_db):
    """Create SQLiteStorageAdapter with temp database."""
    from evalvault.adapters.outbound.storage.sqlite_adapter import (
        SQLiteStorageAdapter,
    )

    return SQLiteStorageAdapter(db_path=temp_db)


@pytest.fixture
def sample_run():
    """Create a sample EvaluationRun for testing."""
    return EvaluationRun(
        run_id="test-run-001",
        dataset_name="insurance-qa",
        dataset_version="1.0.0",
        model_name="gpt-5-nano",
        started_at=datetime(2025, 1, 1, 10, 0, 0),
        finished_at=datetime(2025, 1, 1, 10, 5, 0),
        metrics_evaluated=["faithfulness", "answer_relevancy"],
        thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7},
        total_tokens=1000,
        total_cost_usd=0.05,
        langfuse_trace_id="trace-123",
        results=[
            TestCaseResult(
                test_case_id="tc-001",
                metrics=[
                    MetricScore(name="faithfulness", score=0.85, threshold=0.7, reason="Good"),
                    MetricScore(
                        name="answer_relevancy",
                        score=0.90,
                        threshold=0.7,
                        reason="Excellent",
                    ),
                ],
                tokens_used=500,
                latency_ms=1200,
                cost_usd=0.025,
                trace_id="trace-tc-001",
                started_at=datetime(2025, 1, 1, 10, 0, 0),
                finished_at=datetime(2025, 1, 1, 10, 0, 1),
                question="What is the coverage amount?",
                answer="The coverage amount is 100 million won.",
                contexts=["The insurance coverage is 100 million won."],
                ground_truth="100 million won",
            ),
            TestCaseResult(
                test_case_id="tc-002",
                metrics=[
                    MetricScore(name="faithfulness", score=0.75, threshold=0.7, reason="OK"),
                    MetricScore(
                        name="answer_relevancy",
                        score=0.80,
                        threshold=0.7,
                        reason="Good",
                    ),
                ],
                tokens_used=500,
                latency_ms=1100,
                cost_usd=0.025,
                trace_id="trace-tc-002",
                started_at=datetime(2025, 1, 1, 10, 1, 0),
                finished_at=datetime(2025, 1, 1, 10, 1, 1),
                question="What is the premium?",
                answer="The monthly premium is 50,000 won.",
                contexts=["The monthly premium is 50,000 won."],
                ground_truth="50,000 won",
            ),
        ],
    )


class TestSQLiteStorageAdapter:
    """Test suite for SQLiteStorageAdapter."""

    def test_initialization_creates_tables(self, temp_db):
        """Test that initialization creates database and tables."""
        from evalvault.adapters.outbound.storage.sqlite_adapter import (
            SQLiteStorageAdapter,
        )

        SQLiteStorageAdapter(db_path=temp_db)

        # Verify tables exist
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "evaluation_runs" in tables
        assert "test_case_results" in tables
        assert "metric_scores" in tables

    def test_save_run_returns_run_id(self, storage_adapter, sample_run):
        """Test that save_run stores data and returns run_id."""
        run_id = storage_adapter.save_run(sample_run)
        assert run_id == "test-run-001"

    def test_save_run_stores_evaluation_run(self, storage_adapter, sample_run, temp_db):
        """Test that save_run correctly stores evaluation run data."""
        storage_adapter.save_run(sample_run)

        # Verify data in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evaluation_runs WHERE run_id = ?", ("test-run-001",))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "test-run-001"  # run_id
        assert row[1] == "insurance-qa"  # dataset_name
        assert row[2] == "1.0.0"  # dataset_version
        assert row[3] == "gpt-5-nano"  # model_name
        assert row[6] == 1000  # total_tokens
        assert row[7] == 0.05  # total_cost_usd

    def test_save_run_stores_test_case_results(self, storage_adapter, sample_run, temp_db):
        """Test that save_run stores test case results."""
        storage_adapter.save_run(sample_run)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM test_case_results WHERE run_id = ?",
            ("test-run-001",),
        )
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2

    def test_save_run_stores_metric_scores(self, storage_adapter, sample_run, temp_db):
        """Test that save_run stores metric scores."""
        storage_adapter.save_run(sample_run)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM metric_scores ms
            JOIN test_case_results tcr ON ms.result_id = tcr.id
            WHERE tcr.run_id = ?
            """,
            ("test-run-001",),
        )
        count = cursor.fetchone()[0]
        conn.close()

        # 2 test cases × 2 metrics = 4 scores
        assert count == 4

    def test_get_run_returns_stored_run(self, storage_adapter, sample_run):
        """Test that get_run retrieves stored EvaluationRun."""
        storage_adapter.save_run(sample_run)
        retrieved_run = storage_adapter.get_run("test-run-001")

        assert retrieved_run.run_id == sample_run.run_id
        assert retrieved_run.dataset_name == sample_run.dataset_name
        assert retrieved_run.model_name == sample_run.model_name
        assert retrieved_run.total_tokens == sample_run.total_tokens
        assert len(retrieved_run.results) == 2

    def test_get_run_raises_key_error_for_nonexistent_run(self, storage_adapter):
        """Test that get_run raises KeyError for non-existent run_id."""
        with pytest.raises(KeyError, match="Run not found: nonexistent-run"):
            storage_adapter.get_run("nonexistent-run")

    def test_get_run_reconstructs_test_case_results(self, storage_adapter, sample_run):
        """Test that get_run correctly reconstructs TestCaseResult objects."""
        storage_adapter.save_run(sample_run)
        retrieved_run = storage_adapter.get_run("test-run-001")

        result = retrieved_run.results[0]
        assert result.test_case_id == "tc-001"
        assert result.tokens_used == 500
        assert result.latency_ms == 1200
        assert result.cost_usd == 0.025
        assert result.question == "What is the coverage amount?"
        assert len(result.contexts) == 1

    def test_get_run_reconstructs_metric_scores(self, storage_adapter, sample_run):
        """Test that get_run correctly reconstructs MetricScore objects."""
        storage_adapter.save_run(sample_run)
        retrieved_run = storage_adapter.get_run("test-run-001")

        result = retrieved_run.results[0]
        assert len(result.metrics) == 2

        faithfulness = result.get_metric("faithfulness")
        assert faithfulness is not None
        assert faithfulness.score == 0.85
        assert faithfulness.threshold == 0.7
        assert faithfulness.reason == "Good"

    def test_list_runs_returns_all_runs(self, storage_adapter, sample_run):
        """Test that list_runs returns all stored runs."""
        # Create multiple runs
        run1 = sample_run
        run2 = EvaluationRun(
            run_id="test-run-002",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 2, 10, 0, 0),
        )

        storage_adapter.save_run(run1)
        storage_adapter.save_run(run2)

        runs = storage_adapter.list_runs()
        assert len(runs) == 2

    def test_list_runs_filters_by_dataset_name(self, storage_adapter, sample_run):
        """Test that list_runs filters by dataset_name."""
        run1 = sample_run
        run2 = EvaluationRun(
            run_id="test-run-002",
            dataset_name="medical-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 2, 10, 0, 0),
        )

        storage_adapter.save_run(run1)
        storage_adapter.save_run(run2)

        runs = storage_adapter.list_runs(dataset_name="insurance-qa")
        assert len(runs) == 1
        assert runs[0].dataset_name == "insurance-qa"

    def test_list_runs_filters_by_model_name(self, storage_adapter, sample_run):
        """Test that list_runs filters by model_name."""
        run1 = sample_run
        run2 = EvaluationRun(
            run_id="test-run-002",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-4",
            started_at=datetime(2025, 1, 2, 10, 0, 0),
        )

        storage_adapter.save_run(run1)
        storage_adapter.save_run(run2)

        runs = storage_adapter.list_runs(model_name="gpt-5-nano")
        assert len(runs) == 1
        assert runs[0].model_name == "gpt-5-nano"

    def test_list_runs_respects_limit(self, storage_adapter):
        """Test that list_runs respects the limit parameter."""
        for i in range(5):
            run = EvaluationRun(
                run_id=f"test-run-{i:03d}",
                dataset_name="insurance-qa",
                dataset_version="1.0.0",
                model_name="gpt-5-nano",
                started_at=datetime(2025, 1, i + 1, 10, 0, 0),
            )
            storage_adapter.save_run(run)

        runs = storage_adapter.list_runs(limit=3)
        assert len(runs) == 3

    def test_list_runs_returns_latest_first(self, storage_adapter):
        """Test that list_runs returns runs in descending order by started_at."""
        run1 = EvaluationRun(
            run_id="test-run-001",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 1, 10, 0, 0),
        )
        run2 = EvaluationRun(
            run_id="test-run-002",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 2, 10, 0, 0),
        )

        storage_adapter.save_run(run1)
        storage_adapter.save_run(run2)

        runs = storage_adapter.list_runs()
        assert runs[0].run_id == "test-run-002"  # Latest first
        assert runs[1].run_id == "test-run-001"

    def test_delete_run_removes_run(self, storage_adapter, sample_run, temp_db):
        """Test that delete_run removes run and related data."""
        storage_adapter.save_run(sample_run)
        result = storage_adapter.delete_run("test-run-001")

        assert result is True

        # Verify run is deleted
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM evaluation_runs WHERE run_id = ?", ("test-run-001",))
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 0

    def test_delete_run_cascades_to_results(self, storage_adapter, sample_run, temp_db):
        """Test that delete_run cascades to test_case_results."""
        storage_adapter.save_run(sample_run)
        storage_adapter.delete_run("test-run-001")

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM test_case_results WHERE run_id = ?",
            ("test-run-001",),
        )
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 0

    def test_delete_run_returns_false_for_nonexistent_run(self, storage_adapter):
        """Test that delete_run returns False for non-existent run."""
        result = storage_adapter.delete_run("nonexistent-run")
        assert result is False

    def test_save_run_with_no_results(self, storage_adapter):
        """Test saving a run with no test case results."""
        run = EvaluationRun(
            run_id="test-run-003",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 1, 10, 0, 0),
            results=[],
        )

        run_id = storage_adapter.save_run(run)
        assert run_id == "test-run-003"

        retrieved_run = storage_adapter.get_run("test-run-003")
        assert len(retrieved_run.results) == 0
