"""Unit tests for MLflow tracker adapter."""

import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, call, patch

import pytest

from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult


# Create a mock mlflow module
@pytest.fixture(autouse=True)
def mock_mlflow_module():
    """Automatically mock the mlflow module for all tests."""
    mock_mlflow = MagicMock()
    mock_mlflow.set_tracking_uri = MagicMock()
    mock_mlflow.set_experiment = MagicMock()
    mock_mlflow.start_run = MagicMock()
    mock_mlflow.end_run = MagicMock()
    mock_mlflow.log_param = MagicMock()
    mock_mlflow.log_metric = MagicMock()
    mock_mlflow.log_artifact = MagicMock()

    # Add mlflow to sys.modules to make import work
    sys.modules["mlflow"] = mock_mlflow

    yield mock_mlflow

    # Cleanup
    if "mlflow" in sys.modules:
        del sys.modules["mlflow"]
    # Clear adapter module cache to force reimport
    if "evalvault.adapters.outbound.tracker.mlflow_adapter" in sys.modules:
        del sys.modules["evalvault.adapters.outbound.tracker.mlflow_adapter"]


class TestMLflowAdapterInitialization:
    """Test MLflowAdapter initialization."""

    def test_init_with_default_parameters(self, mock_mlflow_module):
        """Test initialization with default parameters."""
        from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()

        mock_mlflow_module.set_tracking_uri.assert_called_once_with("http://localhost:5000")
        mock_mlflow_module.set_experiment.assert_called_once_with("evalvault")
        assert adapter._mlflow == mock_mlflow_module
        assert adapter._active_runs == {}

    def test_init_with_custom_parameters(self, mock_mlflow_module):
        """Test initialization with custom tracking URI and experiment name."""
        from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

        MLflowAdapter(
            tracking_uri="http://custom-host:8080",
            experiment_name="custom-experiment",
        )

        mock_mlflow_module.set_tracking_uri.assert_called_once_with("http://custom-host:8080")
        mock_mlflow_module.set_experiment.assert_called_once_with("custom-experiment")


class TestMLflowAdapterTraceManagement:
    """Test trace management methods."""

    @pytest.fixture
    def adapter(self, mock_mlflow_module):
        """Create adapter instance with mocked run."""
        from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

        mock_run = MagicMock()
        mock_run.info.run_id = "mlflow-run-123"
        mock_mlflow_module.start_run.return_value = mock_run
        return MLflowAdapter()

    def test_start_trace_without_metadata(self, adapter, mock_mlflow_module):
        """Test starting a trace without metadata."""
        trace_id = adapter.start_trace("test-run")

        assert trace_id == "mlflow-run-123"
        mock_mlflow_module.start_run.assert_called_with(run_name="test-run")
        assert trace_id in adapter._active_runs

    def test_start_trace_with_metadata(self, mock_mlflow_module):
        """Test starting a trace with metadata."""
        from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

        mock_run = MagicMock()
        mock_run.info.run_id = "mlflow-run-456"
        mock_mlflow_module.start_run.return_value = mock_run

        adapter = MLflowAdapter()
        metadata = {
            "dataset": "test-dataset",
            "version": "1.0.0",
            "model": "gpt-4",
            "count": 10,
            "threshold": 0.7,
            "flag": True,
        }
        trace_id = adapter.start_trace("test-run", metadata)

        assert trace_id == "mlflow-run-456"
        # Verify all metadata items were logged as parameters
        expected_calls = [
            call("dataset", "test-dataset"),
            call("version", "1.0.0"),
            call("model", "gpt-4"),
            call("count", 10),
            call("threshold", 0.7),
            call("flag", True),
        ]
        mock_mlflow_module.log_param.assert_has_calls(expected_calls, any_order=True)

    def test_start_trace_with_non_primitive_metadata_skips(self, mock_mlflow_module):
        """Test that non-primitive metadata values are skipped."""
        from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

        mock_run = MagicMock()
        mock_run.info.run_id = "mlflow-run-789"
        mock_mlflow_module.start_run.return_value = mock_run

        adapter = MLflowAdapter()
        metadata = {
            "valid_string": "test",
            "invalid_list": [1, 2, 3],
            "invalid_dict": {"key": "value"},
        }
        adapter.start_trace("test-run", metadata)

        # Only valid_string should be logged
        mock_mlflow_module.log_param.assert_called_once_with("valid_string", "test")

    def test_end_trace_success(self, adapter, mock_mlflow_module):
        """Test ending a trace successfully."""
        trace_id = adapter.start_trace("test-run")

        adapter.end_trace(trace_id)

        mock_mlflow_module.end_run.assert_called_once()
        assert trace_id not in adapter._active_runs

    def test_end_trace_invalid_id_raises(self, adapter):
        """Test that ending a non-existent trace raises ValueError."""
        with pytest.raises(ValueError, match="Run not found: invalid-id"):
            adapter.end_trace("invalid-id")

    def test_multiple_traces(self, mock_mlflow_module):
        """Test managing multiple active traces."""
        from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

        # Setup different run IDs for multiple calls
        run1 = MagicMock()
        run1.info.run_id = "run-1"
        run2 = MagicMock()
        run2.info.run_id = "run-2"
        mock_mlflow_module.start_run.side_effect = [run1, run2]

        adapter = MLflowAdapter()
        trace_id_1 = adapter.start_trace("run-1")
        trace_id_2 = adapter.start_trace("run-2")

        assert trace_id_1 == "run-1"
        assert trace_id_2 == "run-2"
        assert len(adapter._active_runs) == 2

        adapter.end_trace(trace_id_1)
        assert len(adapter._active_runs) == 1
        assert trace_id_2 in adapter._active_runs


class TestMLflowAdapterSpanManagement:
    """Test span management (stored as artifacts in MLflow)."""

    @pytest.fixture
    def adapter(self, mock_mlflow_module):
        """Create adapter instance with mocked run."""
        from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

        mock_run = MagicMock()
        mock_run.info.run_id = "mlflow-run-123"
        mock_mlflow_module.start_run.return_value = mock_run
        return MLflowAdapter()

    @patch("evalvault.adapters.outbound.tracker.mlflow_adapter.tempfile.NamedTemporaryFile")
    @patch("evalvault.adapters.outbound.tracker.mlflow_adapter.json")
    def test_add_span_with_input_and_output(
        self, mock_json, mock_tempfile, adapter, mock_mlflow_module
    ):
        """Test adding a span with input and output data."""
        # Setup temp file mock
        mock_file = MagicMock()
        mock_file.name = "/tmp/test.json"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        trace_id = adapter.start_trace("test-run")

        input_data = {"question": "What is RAG?"}
        output_data = {"answer": "Retrieval-Augmented Generation"}

        adapter.add_span(trace_id, "test-span", input_data, output_data)

        # Verify JSON was dumped with correct data
        mock_json.dump.assert_called_once()
        span_data = mock_json.dump.call_args[0][0]
        assert span_data["name"] == "test-span"
        assert span_data["input"] == input_data
        assert span_data["output"] == output_data

        # Verify artifact was logged
        mock_mlflow_module.log_artifact.assert_called_once_with("/tmp/test.json", "spans/test-span")

    @patch("evalvault.adapters.outbound.tracker.mlflow_adapter.tempfile.NamedTemporaryFile")
    @patch("evalvault.adapters.outbound.tracker.mlflow_adapter.json")
    def test_add_span_without_data(self, mock_json, mock_tempfile, adapter, mock_mlflow_module):
        """Test adding a span without input/output data."""
        mock_file = MagicMock()
        mock_file.name = "/tmp/test.json"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        trace_id = adapter.start_trace("test-run")

        adapter.add_span(trace_id, "empty-span")

        span_data = mock_json.dump.call_args[0][0]
        assert span_data["name"] == "empty-span"
        assert span_data["input"] is None
        assert span_data["output"] is None

    def test_add_span_invalid_trace_id_raises(self, adapter):
        """Test that adding span to non-existent trace raises ValueError."""
        with pytest.raises(ValueError, match="Run not found: invalid-id"):
            adapter.add_span("invalid-id", "span-name")


class TestMLflowAdapterScoreLogging:
    """Test score logging functionality."""

    @pytest.fixture
    def adapter(self, mock_mlflow_module):
        """Create adapter instance with mocked run."""
        from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

        mock_run = MagicMock()
        mock_run.info.run_id = "mlflow-run-123"
        mock_mlflow_module.start_run.return_value = mock_run
        return MLflowAdapter()

    def test_log_score_without_comment(self, adapter, mock_mlflow_module):
        """Test logging a score without comment."""
        trace_id = adapter.start_trace("test-run")

        adapter.log_score(trace_id, "faithfulness", 0.9)

        # Should have logged metric
        assert any(
            call_args[0] == ("faithfulness", 0.9)
            for call_args in mock_mlflow_module.log_metric.call_args_list
        )

    def test_log_score_with_comment(self, adapter, mock_mlflow_module):
        """Test logging a score with comment."""
        trace_id = adapter.start_trace("test-run")

        adapter.log_score(trace_id, "faithfulness", 0.9, "Good score")

        # Should have logged metric
        assert any(
            call_args[0] == ("faithfulness", 0.9)
            for call_args in mock_mlflow_module.log_metric.call_args_list
        )
        # Should have logged comment as param
        assert any(
            call_args[0] == ("faithfulness_comment", "Good score")
            for call_args in mock_mlflow_module.log_param.call_args_list
        )

    def test_log_score_with_long_comment_truncates(self, adapter, mock_mlflow_module):
        """Test that long comments are truncated to 250 chars."""
        trace_id = adapter.start_trace("test-run")

        long_comment = "x" * 300
        adapter.log_score(trace_id, "metric", 0.8, long_comment)

        # Check that comment was truncated
        comment_calls = [
            call_args
            for call_args in mock_mlflow_module.log_param.call_args_list
            if len(call_args[0]) > 0 and call_args[0][0] == "metric_comment"
        ]
        assert len(comment_calls) == 1
        assert len(comment_calls[0][0][1]) == 250

    def test_log_score_invalid_trace_id_raises(self, adapter):
        """Test that logging score to non-existent trace raises ValueError."""
        with pytest.raises(ValueError, match="Run not found: invalid-id"):
            adapter.log_score("invalid-id", "metric", 0.9)

    def test_log_multiple_scores(self, adapter, mock_mlflow_module):
        """Test logging multiple scores to the same trace."""
        trace_id = adapter.start_trace("test-run")

        adapter.log_score(trace_id, "faithfulness", 0.9)
        adapter.log_score(trace_id, "answer_relevancy", 0.8)
        adapter.log_score(trace_id, "context_precision", 0.95)

        # Verify all metrics were logged
        metric_calls = [c[0] for c in mock_mlflow_module.log_metric.call_args_list]
        assert ("faithfulness", 0.9) in metric_calls
        assert ("answer_relevancy", 0.8) in metric_calls
        assert ("context_precision", 0.95) in metric_calls


class TestMLflowAdapterArtifactSaving:
    """Test artifact saving functionality."""

    @pytest.fixture
    def adapter(self, mock_mlflow_module):
        """Create adapter instance with mocked run."""
        from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

        mock_run = MagicMock()
        mock_run.info.run_id = "mlflow-run-123"
        mock_mlflow_module.start_run.return_value = mock_run
        return MLflowAdapter()

    @patch("evalvault.adapters.outbound.tracker.mlflow_adapter.tempfile.NamedTemporaryFile")
    @patch("evalvault.adapters.outbound.tracker.mlflow_adapter.json")
    def test_save_json_artifact(self, mock_json, mock_tempfile, adapter, mock_mlflow_module):
        """Test saving a JSON artifact."""
        mock_file = MagicMock()
        mock_file.name = "/tmp/artifact.json"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        trace_id = adapter.start_trace("test-run")

        artifact_data = {"results": [1, 2, 3], "summary": "test"}
        adapter.save_artifact(trace_id, "results", artifact_data, "json")

        # Verify JSON dump was called with correct data
        mock_json.dump.assert_called_once()
        assert mock_json.dump.call_args[0][0] == artifact_data

        # Verify artifact was logged to correct path
        mock_mlflow_module.log_artifact.assert_called_with(
            "/tmp/artifact.json", "artifacts/results"
        )

    def test_save_artifact_invalid_trace_id_raises(self, adapter):
        """Test that saving artifact to non-existent trace raises ValueError."""
        with pytest.raises(ValueError, match="Run not found: invalid-id"):
            adapter.save_artifact("invalid-id", "artifact", {"data": "value"})


class TestMLflowAdapterEvaluationRun:
    """Test logging complete evaluation runs."""

    @pytest.fixture
    def sample_run(self):
        """Create a sample evaluation run."""
        started = datetime(2024, 1, 1, 10, 0, 0)
        finished = started + timedelta(seconds=30)

        return EvaluationRun(
            run_id="test-run-123",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-4",
            started_at=started,
            finished_at=finished,
            metrics_evaluated=["faithfulness", "answer_relevancy"],
            thresholds={"faithfulness": 0.7, "answer_relevancy": 0.8},
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[
                        MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.85, threshold=0.8),
                    ],
                    tokens_used=100,
                    question="What is insurance?",
                    answer="Insurance is a contract...",
                    contexts=["Insurance provides financial protection..."],
                    ground_truth="Insurance is financial protection",
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    metrics=[
                        MetricScore(name="faithfulness", score=0.75, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.65, threshold=0.8),
                    ],
                    tokens_used=120,
                    question="What is a premium?",
                    answer="A premium is a payment...",
                    contexts=["Premium is the amount paid..."],
                    ground_truth="Premium is the payment amount",
                ),
            ],
            total_tokens=220,
        )

    @patch("evalvault.adapters.outbound.tracker.mlflow_adapter.tempfile.NamedTemporaryFile")
    @patch("evalvault.adapters.outbound.tracker.mlflow_adapter.json")
    def test_log_evaluation_run_success(
        self, mock_json, mock_tempfile, mock_mlflow_module, sample_run
    ):
        """Test logging a complete evaluation run."""
        from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

        mock_file = MagicMock()
        mock_file.name = "/tmp/results.json"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        mock_run = MagicMock()
        mock_run.info.run_id = "mlflow-run-456"
        mock_mlflow_module.start_run.return_value = mock_run

        adapter = MLflowAdapter()
        trace_id = adapter.log_evaluation_run(sample_run)

        assert trace_id == "mlflow-run-456"

        # Verify run was started with correct name
        assert any(
            "evaluation-test-run" in str(call_args)
            for call_args in mock_mlflow_module.start_run.call_args_list
        )

        # Verify metadata parameters were logged
        param_calls = [c[0] for c in mock_mlflow_module.log_param.call_args_list]
        assert ("dataset_name", "insurance-qa") in param_calls
        assert ("dataset_version", "1.0.0") in param_calls
        assert ("model_name", "gpt-4") in param_calls
        assert ("total_test_cases", 2) in param_calls

        # Verify metrics were logged
        metric_calls = [c[0][0] for c in mock_mlflow_module.log_metric.call_args_list]
        assert "avg_faithfulness" in metric_calls
        assert "avg_answer_relevancy" in metric_calls
        assert "pass_rate" in metric_calls
        assert "total_tokens" in metric_calls
        assert "duration_seconds" in metric_calls

        # Verify test results artifact was saved
        assert mock_json.dump.called
        # Get the first json.dump call (test_results), not the last (custom_metric_snapshot)
        results_data = mock_json.dump.call_args_list[0][0][0]
        assert len(results_data) == 2
        assert results_data[0]["test_case_id"] == "tc-001"
        assert results_data[0]["all_passed"] is True
        assert results_data[1]["test_case_id"] == "tc-002"
        assert results_data[1]["all_passed"] is False

        # Verify run was ended
        mock_mlflow_module.end_run.assert_called()

    def test_log_evaluation_run_empty_results(self, mock_mlflow_module):
        """Test logging evaluation run with no results."""
        from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

        mock_run = MagicMock()
        mock_run.info.run_id = "mlflow-run-789"
        mock_mlflow_module.start_run.return_value = mock_run

        empty_run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0",
            model_name="gpt-4",
            metrics_evaluated=["faithfulness"],
            thresholds={"faithfulness": 0.7},
            results=[],
        )

        adapter = MLflowAdapter()
        trace_id = adapter.log_evaluation_run(empty_run)

        assert trace_id is not None
        # Should still log basic metrics
        metric_calls = [c[0] for c in mock_mlflow_module.log_metric.call_args_list]
        assert ("pass_rate", 0.0) in metric_calls


class TestMLflowAdapterTrackerPortCompliance:
    """Test that MLflowAdapter correctly implements TrackerPort interface."""

    def test_has_all_required_methods(self, mock_mlflow_module):
        """Test that adapter has all required TrackerPort methods."""
        from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()

        # Check all required methods exist
        assert hasattr(adapter, "start_trace")
        assert callable(adapter.start_trace)

        assert hasattr(adapter, "add_span")
        assert callable(adapter.add_span)

        assert hasattr(adapter, "log_score")
        assert callable(adapter.log_score)

        assert hasattr(adapter, "save_artifact")
        assert callable(adapter.save_artifact)

        assert hasattr(adapter, "end_trace")
        assert callable(adapter.end_trace)

        assert hasattr(adapter, "log_evaluation_run")
        assert callable(adapter.log_evaluation_run)

    def test_method_signatures_match_port(self, mock_mlflow_module):
        """Test that method signatures match TrackerPort interface."""
        import inspect

        from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter
        from evalvault.ports.outbound.tracker_port import TrackerPort

        adapter = MLflowAdapter()

        # Get signatures for TrackerPort methods
        port_methods = {
            name: inspect.signature(getattr(TrackerPort, name))
            for name in dir(TrackerPort)
            if not name.startswith("_") and callable(getattr(TrackerPort, name))
        }

        # Verify adapter methods have compatible signatures
        for method_name, port_sig in port_methods.items():
            adapter_method = getattr(adapter, method_name)
            adapter_sig = inspect.signature(adapter_method)

            # Both should have same parameter names (excluding 'self')
            port_params = [p for p in port_sig.parameters if p != "self"]
            adapter_params = [p for p in adapter_sig.parameters if p != "self"]

            assert port_params == adapter_params, f"Method {method_name} signature mismatch"
