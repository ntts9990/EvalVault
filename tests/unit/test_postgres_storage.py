"""Unit tests for PostgreSQL storage adapter."""

import importlib
import json
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.entities.experiment import Experiment

POSTGRES_ADAPTER_MODULE = "evalvault.adapters.outbound.storage.postgres_adapter"


@pytest.fixture(autouse=True)
def mock_psycopg_modules():
    """Ensure psycopg is mocked before importing the adapter module."""
    original_psycopg = sys.modules.get("psycopg")
    original_psycopg_rows = sys.modules.get("psycopg.rows")
    sys.modules["psycopg"] = MagicMock()
    sys.modules["psycopg.rows"] = MagicMock()

    if POSTGRES_ADAPTER_MODULE in sys.modules:
        del sys.modules[POSTGRES_ADAPTER_MODULE]
    importlib.import_module(POSTGRES_ADAPTER_MODULE)

    yield

    if original_psycopg is None:
        sys.modules.pop("psycopg", None)
    else:
        sys.modules["psycopg"] = original_psycopg

    if original_psycopg_rows is None:
        sys.modules.pop("psycopg.rows", None)
    else:
        sys.modules["psycopg.rows"] = original_psycopg_rows


@pytest.fixture(autouse=True)
def patch_pg_migrations(mock_psycopg_modules):
    """Skip actual schema migrations during tests."""
    with patch(
        "evalvault.adapters.outbound.storage.postgres_adapter.PostgreSQLStorageAdapter._apply_migrations",
        autospec=True,
    ) as mocked:
        yield mocked


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
        tracker_metadata={
            "phoenix": {
                "prompts": [
                    {
                        "path": "agent/prompts/baseline.txt",
                        "status": "missing_file",
                    }
                ]
            }
        },
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
def sample_statistical_analysis():
    """Create a sample StatisticalAnalysis for testing."""
    from evalvault.domain.entities.analysis import MetricStats, StatisticalAnalysis

    analysis = StatisticalAnalysis(
        run_id="analysis-run-001",
        metrics_summary={
            "faithfulness": MetricStats(
                mean=0.82,
                std=0.03,
                min=0.78,
                max=0.87,
                median=0.82,
                percentile_25=0.8,
                percentile_75=0.85,
                count=4,
            )
        },
        insights=["Keep pushing faithfulness above 85%"],
        correlation_matrix=[[1.0]],
        correlation_metrics=["faithfulness"],
        metric_pass_rates={"faithfulness": 0.75},
        overall_pass_rate=0.7,
    )
    return analysis


@pytest.fixture
def sample_nlp_analysis():
    """Create a sample NLPAnalysis for testing."""
    from evalvault.domain.entities.analysis import (
        KeywordInfo,
        NLPAnalysis,
        QuestionType,
        QuestionTypeStats,
        TextStats,
        TopicCluster,
    )

    return NLPAnalysis(
        run_id="analysis-run-001",
        question_stats=TextStats(
            char_count=120,
            word_count=24,
            sentence_count=3,
            avg_word_length=5.0,
            unique_word_ratio=0.6,
        ),
        answer_stats=TextStats(
            char_count=200,
            word_count=40,
            sentence_count=4,
            avg_word_length=5.0,
            unique_word_ratio=0.55,
        ),
        question_types=[
            QuestionTypeStats(
                question_type=QuestionType.FACTUAL,
                count=3,
                percentage=0.6,
                avg_scores={"faithfulness": 0.8},
            )
        ],
        top_keywords=[KeywordInfo(keyword="보험", frequency=3, tfidf_score=0.9)],
        topic_clusters=[
            TopicCluster(
                cluster_id=1,
                keywords=["보험료", "갱신"],
                document_count=6,
                avg_scores={"faithfulness": 0.72},
                representative_questions=["보험료 갱신 주기를 알려줘"],
            )
        ],
        insights=["질문 유형은 사실형이 우세합니다."],
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
                "metadata": '{"phoenix":{"prompts":[{"path":"agent/prompts/baseline.txt","status":"missing_file"}]}}',
                "retrieval_metadata": None,
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
            "metadata": None,
            "retrieval_metadata": None,
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


class TestPostgreSQLExperimentStorage:
    """Test suite for PostgreSQL Experiment storage methods."""

    @pytest.fixture
    def sample_experiment(self):
        """Create a sample Experiment for testing."""
        exp = Experiment(
            experiment_id="exp-001",
            name="Model Comparison",
            description="Compare GPT-4 vs GPT-3.5",
            hypothesis="GPT-4 will have higher faithfulness scores",
            status="running",
            metrics_to_compare=["faithfulness", "answer_relevancy"],
        )
        exp.add_group("control", "GPT-3.5 baseline")
        exp.add_group("variant_a", "GPT-4 test group")
        exp.groups[0].run_ids = ["run-001", "run-002"]
        exp.groups[1].run_ids = ["run-003", "run-004"]
        return exp

    def test_save_experiment_returns_experiment_id(
        self, mock_psycopg, mock_connection, sample_experiment
    ):
        """Test that save_experiment stores data and returns experiment_id."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        exp_id = adapter.save_experiment(sample_experiment)
        assert exp_id == "exp-001"

    def test_save_experiment_inserts_experiment_data(
        self, mock_psycopg, mock_connection, sample_experiment
    ):
        """Test that save_experiment correctly inserts experiment data."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        adapter.save_experiment(sample_experiment)

        # Verify execute was called for experiment and groups
        assert mock_connection.execute.called

    def test_save_experiment_inserts_groups(self, mock_psycopg, mock_connection, sample_experiment):
        """Test that save_experiment inserts experiment groups."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        adapter.save_experiment(sample_experiment)

        # Should insert 2 groups
        assert mock_connection.execute.called
        assert mock_connection.commit.called

    def test_get_experiment_returns_stored_experiment(self, mock_psycopg, mock_connection):
        """Test that get_experiment retrieves stored Experiment."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        mock_cursor = MagicMock()
        mock_connection.execute.return_value = mock_cursor

        # Mock experiment data
        mock_cursor.fetchone.return_value = {
            "experiment_id": "exp-001",
            "name": "Model Comparison",
            "description": "Compare models",
            "hypothesis": "GPT-4 is better",
            "created_at": datetime(2025, 1, 1, 10, 0, 0),
            "status": "running",
            "metrics_to_compare": '["faithfulness"]',
            "conclusion": None,
        }

        # Mock groups
        mock_cursor.fetchall.return_value = [
            {
                "name": "control",
                "description": "Baseline",
                "run_ids": '["run-001"]',
            }
        ]

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        exp = adapter.get_experiment("exp-001")

        assert exp.experiment_id == "exp-001"
        assert exp.name == "Model Comparison"
        assert exp.status == "running"

    def test_get_experiment_raises_key_error_for_nonexistent(self, mock_psycopg, mock_connection):
        """Test that get_experiment raises KeyError for non-existent experiment."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        mock_cursor = MagicMock()
        mock_connection.execute.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        with pytest.raises(KeyError, match="Experiment not found"):
            adapter.get_experiment("nonexistent")

    def test_list_experiments_returns_all_experiments(self, mock_psycopg, mock_connection):
        """Test that list_experiments returns all stored experiments."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        mock_cursor = MagicMock()
        mock_connection.execute.return_value = mock_cursor

        # Mock experiment IDs
        mock_cursor.fetchall.return_value = [
            {"experiment_id": "exp-001"},
            {"experiment_id": "exp-002"},
        ]

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        with patch.object(adapter, "get_experiment") as mock_get:
            mock_get.side_effect = lambda eid: Experiment(
                experiment_id=eid,
                name=f"Experiment {eid}",
            )

            experiments = adapter.list_experiments()
            assert len(experiments) == 2

    def test_list_experiments_filters_by_status(self, mock_psycopg, mock_connection):
        """Test that list_experiments filters by status."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        mock_cursor = MagicMock()
        mock_connection.execute.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{"experiment_id": "exp-001"}]

        with patch.object(adapter, "get_experiment") as mock_get:
            mock_get.return_value = Experiment(
                experiment_id="exp-001",
                name="Test",
                status="completed",
            )

            adapter.list_experiments(status="completed")
            assert mock_connection.execute.called

    def test_update_experiment_updates_data(self, mock_psycopg, mock_connection, sample_experiment):
        """Test that update_experiment updates experiment data."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        sample_experiment.status = "completed"
        sample_experiment.conclusion = "GPT-4 performed better"

        adapter.update_experiment(sample_experiment)

        assert mock_connection.execute.called
        assert mock_connection.commit.called


class TestPostgreSQLAnalysisStorage:
    """Analysis storage tests for PostgreSQL adapter."""

    def test_save_analysis_returns_id(
        self, mock_psycopg, mock_connection, sample_statistical_analysis
    ):
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        analysis_id = adapter.save_analysis(sample_statistical_analysis)

        assert analysis_id == sample_statistical_analysis.analysis_id
        assert mock_connection.execute.called
        assert mock_connection.commit.called

    def test_get_analysis_returns_object(
        self, mock_psycopg, mock_connection, sample_statistical_analysis
    ):
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        data = adapter._serialize_analysis(sample_statistical_analysis)  # type: ignore[attr-defined]
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "analysis_id": sample_statistical_analysis.analysis_id,
            "run_id": sample_statistical_analysis.run_id,
            "analysis_type": sample_statistical_analysis.analysis_type.value,
            "result_data": json.dumps(data),
            "created_at": datetime(2025, 1, 1, 10, 0, 0),
        }
        mock_connection.execute.return_value = mock_cursor

        retrieved = adapter.get_analysis(sample_statistical_analysis.analysis_id)

        assert retrieved.run_id == sample_statistical_analysis.run_id
        assert "faithfulness" in retrieved.metrics_summary

    def test_get_analysis_by_run_returns_list(
        self, mock_psycopg, mock_connection, sample_statistical_analysis
    ):
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        data = adapter._serialize_analysis(sample_statistical_analysis)  # type: ignore[attr-defined]
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "analysis_id": sample_statistical_analysis.analysis_id,
                "run_id": sample_statistical_analysis.run_id,
                "analysis_type": sample_statistical_analysis.analysis_type.value,
                "result_data": json.dumps(data),
                "created_at": datetime(2025, 1, 1, 10, 0, 0),
            }
        ]
        mock_connection.execute.return_value = mock_cursor

        analyses = adapter.get_analysis_by_run(sample_statistical_analysis.run_id)

        assert len(analyses) == 1
        assert analyses[0].analysis_id == sample_statistical_analysis.analysis_id

    def test_delete_analysis_returns_bool(self, mock_psycopg, mock_connection):
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_connection.execute.return_value = mock_cursor

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        assert adapter.delete_analysis("analysis-123") is True

    def test_save_nlp_analysis_returns_id(self, mock_psycopg, mock_connection, sample_nlp_analysis):
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        analysis_id = adapter.save_nlp_analysis(sample_nlp_analysis)

        assert analysis_id.startswith("nlp-analysis-run-001-")
        assert mock_connection.commit.called

    def test_get_nlp_analysis_returns_object(
        self, mock_psycopg, mock_connection, sample_nlp_analysis
    ):
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        data = adapter._serialize_nlp_analysis(sample_nlp_analysis)  # type: ignore[attr-defined]
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "analysis_id": "nlp-analysis-run-001-aaaa",
            "run_id": sample_nlp_analysis.run_id,
            "result_data": json.dumps(data),
        }
        mock_connection.execute.return_value = mock_cursor

        retrieved = adapter.get_nlp_analysis("nlp-analysis-run-001-aaaa")

        assert retrieved.run_id == sample_nlp_analysis.run_id
        assert retrieved.question_stats is not None

    def test_get_nlp_analysis_by_run_returns_latest(
        self, mock_psycopg, mock_connection, sample_nlp_analysis
    ):
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        data = adapter._serialize_nlp_analysis(sample_nlp_analysis)  # type: ignore[attr-defined]
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"result_data": json.dumps(data)}
        mock_connection.execute.return_value = mock_cursor

        retrieved = adapter.get_nlp_analysis_by_run(sample_nlp_analysis.run_id)

        assert retrieved is not None
        assert retrieved.run_id == sample_nlp_analysis.run_id

    def test_get_nlp_analysis_reconstructs_topic_clusters(
        self, mock_psycopg, mock_connection, sample_nlp_analysis
    ):
        """TopicCluster 정보 복원."""
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        data = adapter._serialize_nlp_analysis(sample_nlp_analysis)  # type: ignore[attr-defined]
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "analysis_id": "nlp-analysis-run-001-aaaa",
            "run_id": sample_nlp_analysis.run_id,
            "result_data": json.dumps(data),
        }
        mock_connection.execute.return_value = mock_cursor

        retrieved = adapter.get_nlp_analysis("nlp-analysis-run-001-aaaa")

        assert len(retrieved.topic_clusters) == 1
        cluster = retrieved.topic_clusters[0]
        assert cluster.keywords == ["보험료", "갱신"]
        assert cluster.avg_scores["faithfulness"] == 0.72
        assert cluster.representative_questions[0].startswith("보험료")


class TestPostgreSQLRegressionBaseline:
    def test_set_regression_baseline_calls_execute(self, mock_psycopg, mock_connection, sample_run):
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        adapter.set_regression_baseline(
            "default",
            sample_run.run_id,
            dataset_name="insurance-qa",
            branch="main",
            commit_sha="abc123",
            metadata={"ci": True},
        )

        assert mock_connection.execute.called
        assert mock_connection.commit.called

    def test_get_regression_baseline_returns_data(self, mock_psycopg, mock_connection):
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "baseline_key": "default",
            "run_id": "test-run-001",
            "dataset_name": "insurance-qa",
            "branch": "main",
            "commit_sha": "abc123",
            "metadata": '{"ci": true}',
            "created_at": datetime(2025, 1, 1, 10, 0, 0),
            "updated_at": datetime(2025, 1, 1, 10, 0, 0),
        }
        mock_connection.execute.return_value = mock_cursor

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        baseline = adapter.get_regression_baseline("default")

        assert baseline is not None
        assert baseline["baseline_key"] == "default"
        assert baseline["run_id"] == "test-run-001"
        assert baseline["dataset_name"] == "insurance-qa"
        assert baseline["branch"] == "main"
        assert baseline["commit_sha"] == "abc123"

    def test_get_regression_baseline_returns_none_for_missing(self, mock_psycopg, mock_connection):
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection.execute.return_value = mock_cursor

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        baseline = adapter.get_regression_baseline("nonexistent")

        assert baseline is None

    def test_set_regression_baseline_minimal(self, mock_psycopg, mock_connection, sample_run):
        from evalvault.adapters.outbound.storage.postgres_adapter import (
            PostgreSQLStorageAdapter,
        )

        with patch("builtins.open", MagicMock()):
            adapter = PostgreSQLStorageAdapter(connection_string="test")

        adapter.set_regression_baseline("minimal", sample_run.run_id)

        assert mock_connection.execute.called
        assert mock_connection.commit.called
