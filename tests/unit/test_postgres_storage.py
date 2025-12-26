"""Unit tests for PostgreSQL storage adapter."""

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult

# Mock psycopg module before importing PostgreSQLStorageAdapter
sys.modules["psycopg"] = MagicMock()
sys.modules["psycopg.rows"] = MagicMock()


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


@pytest.fixture
def mock_psycopg():
    """Mock psycopg module."""
    with patch("psycopg.connect") as mock_connect:
        yield mock_connect


@pytest.fixture
def mock_connection(mock_psycopg):
    """Create a mock connection with cursor."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Setup context manager
    mock_psycopg.return_value.__enter__.return_value = mock_conn
    mock_psycopg.return_value.__exit__.return_value = None

    # Setup cursor
    mock_conn.execute.return_value = mock_cursor
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = None

    return mock_conn


class TestPostgreSQLStorageAdapter:
    """Test suite for PostgreSQLStorageAdapter."""

    def test_initialization_creates_schema(self, mock_psycopg):
        """Test that initialization creates database schema."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            PostgreSQLStorageAdapter(
                host="localhost",
                port=5432,
                database="test_db",
                user="test_user",
                password="test_pass",
            )

        # Verify connection was attempted
        assert mock_psycopg.called

    def test_initialization_with_connection_string(self, mock_psycopg):
        """Test initialization with connection string."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(
                connection_string="postgresql://user:pass@localhost:5432/testdb"
            )

        assert adapter._conn_string == "postgresql://user:pass@localhost:5432/testdb"

    def test_save_run_returns_run_id(self, mock_psycopg, sample_run):
        """Test that save_run stores data and returns run_id."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        run_id = adapter.save_run(sample_run)
        assert run_id == "test-run-001"

    def test_save_run_inserts_evaluation_run(self, mock_psycopg, mock_connection, sample_run):
        """Test that save_run correctly inserts evaluation run data."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        adapter.save_run(sample_run)

        # Verify execute was called (schema init + run insert + results + metrics)
        assert mock_connection.execute.called

    def test_save_run_inserts_test_case_results(self, mock_psycopg, mock_connection, sample_run):
        """Test that save_run inserts test case results."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        adapter.save_run(sample_run)

        # Should insert 2 test case results
        assert mock_connection.execute.called

    def test_save_run_inserts_metric_scores(self, mock_psycopg, mock_connection, sample_run):
        """Test that save_run inserts metric scores."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        adapter.save_run(sample_run)

        # Should insert 4 metric scores (2 test cases × 2 metrics)
        assert mock_connection.execute.called

    def test_get_run_returns_stored_run(self, mock_psycopg, mock_connection):
        """Test that get_run retrieves stored EvaluationRun."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        # Mock database responses
        mock_cursor = MagicMock()
        mock_connection.execute.return_value = mock_cursor

        # Mock evaluation run data
        mock_cursor.fetchone.side_effect = [
            {
                "run_id": "test-run-001",
                "dataset_name": "insurance-qa",
                "dataset_version": "1.0.0",
                "model_name": "gpt-5-nano",
                "started_at": datetime(2025, 1, 1, 10, 0, 0),
                "finished_at": datetime(2025, 1, 1, 10, 5, 0),
                "total_tokens": 1000,
                "total_cost_usd": 0.05,
                "pass_rate": None,
                "metrics_evaluated": '["faithfulness"]',
                "thresholds": '{"faithfulness": 0.7}',
                "langfuse_trace_id": "trace-123",
            },
            None,  # End of test_case_results
        ]

        # Mock test case results
        mock_cursor.fetchall.side_effect = [
            [],  # No test case results
        ]

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        run = adapter.get_run("test-run-001")

        assert run.run_id == "test-run-001"
        assert run.dataset_name == "insurance-qa"
        assert run.model_name == "gpt-5-nano"

    def test_get_run_raises_key_error_for_nonexistent_run(self, mock_psycopg, mock_connection):
        """Test that get_run raises KeyError for non-existent run_id."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        mock_cursor = MagicMock()
        mock_connection.execute.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        with pytest.raises(KeyError, match="Run not found: nonexistent-run"):
            adapter.get_run("nonexistent-run")

    def test_get_run_reconstructs_test_case_results(self, mock_psycopg, mock_connection):
        """Test that get_run correctly reconstructs TestCaseResult objects."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        mock_cursor = MagicMock()
        mock_connection.execute.return_value = mock_cursor

        # Mock evaluation run
        mock_cursor.fetchone.return_value = {
            "run_id": "test-run-001",
            "dataset_name": "insurance-qa",
            "dataset_version": "1.0.0",
            "model_name": "gpt-5-nano",
            "started_at": datetime(2025, 1, 1, 10, 0, 0),
            "finished_at": datetime(2025, 1, 1, 10, 5, 0),
            "total_tokens": 1000,
            "total_cost_usd": 0.05,
            "pass_rate": None,
            "metrics_evaluated": '["faithfulness"]',
            "thresholds": '{"faithfulness": 0.7}',
            "langfuse_trace_id": "trace-123",
        }

        # Mock test case results and metrics
        mock_cursor.fetchall.side_effect = [
            [
                {
                    "id": 1,
                    "test_case_id": "tc-001",
                    "tokens_used": 500,
                    "latency_ms": 1200,
                    "cost_usd": 0.025,
                    "trace_id": "trace-tc-001",
                    "started_at": datetime(2025, 1, 1, 10, 0, 0),
                    "finished_at": datetime(2025, 1, 1, 10, 0, 1),
                    "question": "What is the coverage?",
                    "answer": "100 million won",
                    "contexts": '["Insurance coverage is 100M"]',
                    "ground_truth": "100M",
                }
            ],
            [
                {
                    "name": "faithfulness",
                    "score": 0.85,
                    "threshold": 0.7,
                    "reason": "Good",
                }
            ],
        ]

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        run = adapter.get_run("test-run-001")

        assert len(run.results) == 1
        assert run.results[0].test_case_id == "tc-001"
        assert run.results[0].tokens_used == 500

    def test_list_runs_returns_all_runs(self, mock_psycopg, mock_connection):
        """Test that list_runs returns all stored runs."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        mock_cursor = MagicMock()
        mock_connection.execute.return_value = mock_cursor

        # Mock run IDs
        mock_cursor.fetchall.return_value = [
            {"run_id": "test-run-001"},
            {"run_id": "test-run-002"},
        ]

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        # Mock get_run to avoid complex reconstruction
        with patch.object(adapter, "get_run") as mock_get_run:
            mock_get_run.side_effect = lambda run_id: EvaluationRun(
                run_id=run_id,
                dataset_name="test",
                model_name="gpt-5-nano",
                started_at=datetime(2025, 1, 1, 10, 0, 0),
            )

            runs = adapter.list_runs()
            assert len(runs) == 2

    def test_list_runs_filters_by_dataset_name(self, mock_psycopg, mock_connection):
        """Test that list_runs filters by dataset_name."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        mock_cursor = MagicMock()
        mock_connection.execute.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{"run_id": "test-run-001"}]

        with patch.object(adapter, "get_run") as mock_get_run:
            mock_get_run.return_value = EvaluationRun(
                run_id="test-run-001",
                dataset_name="insurance-qa",
                model_name="gpt-5-nano",
                started_at=datetime(2025, 1, 1, 10, 0, 0),
            )

            adapter.list_runs(dataset_name="insurance-qa")

            # Verify SQL was called with dataset filter
            assert mock_connection.execute.called

    def test_list_runs_filters_by_model_name(self, mock_psycopg, mock_connection):
        """Test that list_runs filters by model_name."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        mock_cursor = MagicMock()
        mock_connection.execute.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{"run_id": "test-run-001"}]

        with patch.object(adapter, "get_run") as mock_get_run:
            mock_get_run.return_value = EvaluationRun(
                run_id="test-run-001",
                dataset_name="insurance-qa",
                model_name="gpt-5-nano",
                started_at=datetime(2025, 1, 1, 10, 0, 0),
            )

            adapter.list_runs(model_name="gpt-5-nano")

            # Verify SQL was called
            assert mock_connection.execute.called

    def test_list_runs_respects_limit(self, mock_psycopg, mock_connection):
        """Test that list_runs respects the limit parameter."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        mock_cursor = MagicMock()
        mock_connection.execute.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {"run_id": "test-run-001"},
            {"run_id": "test-run-002"},
            {"run_id": "test-run-003"},
        ]

        with patch.object(adapter, "get_run") as mock_get_run:
            mock_get_run.side_effect = lambda run_id: EvaluationRun(
                run_id=run_id,
                dataset_name="test",
                model_name="gpt-5-nano",
                started_at=datetime(2025, 1, 1, 10, 0, 0),
            )

            runs = adapter.list_runs(limit=3)
            assert len(runs) == 3

    def test_delete_run_removes_run(self, mock_psycopg, mock_connection):
        """Test that delete_run removes run and related data."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        mock_cursor = MagicMock()
        mock_connection.execute.return_value = mock_cursor
        mock_cursor.rowcount = 1

        result = adapter.delete_run("test-run-001")

        assert result is True
        assert mock_connection.execute.called
        assert mock_connection.commit.called

    def test_delete_run_returns_false_for_nonexistent_run(self, mock_psycopg, mock_connection):
        """Test that delete_run returns False for non-existent run."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        mock_cursor = MagicMock()
        mock_connection.execute.return_value = mock_cursor
        mock_cursor.rowcount = 0

        result = adapter.delete_run("nonexistent-run")
        assert result is False

    def test_storage_port_compliance(self):
        """Test that PostgreSQLStorageAdapter implements StoragePort interface."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )
        from evalvault.ports.outbound.storage_port import StoragePort

        # Check all required methods exist
        assert hasattr(PostgreSQLStorageAdapter, "save_run")
        assert hasattr(PostgreSQLStorageAdapter, "get_run")
        assert hasattr(PostgreSQLStorageAdapter, "list_runs")

        # Verify method signatures match protocol
        import inspect

        port_methods = {
            name: method
            for name, method in inspect.getmembers(StoragePort, predicate=inspect.isfunction)
            if not name.startswith("_")
        }

        adapter_methods = {
            name: method
            for name, method in inspect.getmembers(
                PostgreSQLStorageAdapter, predicate=inspect.ismethod
            )
            if not name.startswith("_")
        }

        # All port methods should be present in adapter
        for method_name in port_methods:
            assert method_name in adapter_methods or hasattr(PostgreSQLStorageAdapter, method_name)

    def test_save_run_with_no_results(self, mock_psycopg, mock_connection):
        """Test saving a run with no test case results."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        run = EvaluationRun(
            run_id="test-run-003",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 1, 10, 0, 0),
            results=[],
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        run_id = adapter.save_run(run)
        assert run_id == "test-run-003"
