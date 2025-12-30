"""Tests for Langfuse tracker adapter."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from evalvault.adapters.outbound.tracker.langfuse_adapter import LangfuseAdapter
from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult


@pytest.fixture
def mock_langfuse():
    """Mock Langfuse client."""
    with patch("evalvault.adapters.outbound.tracker.langfuse_adapter.Langfuse") as mock:
        yield mock


@pytest.fixture
def langfuse_adapter(mock_langfuse):
    """Create LangfuseAdapter with mocked Langfuse client."""
    mock_client = MagicMock()
    mock_langfuse.return_value = mock_client

    adapter = LangfuseAdapter(
        public_key="pk-test-key",
        secret_key="sk-test-key",
        host="https://cloud.langfuse.com",
    )
    adapter._client = mock_client
    return adapter


class TestLangfuseAdapterInitialization:
    """Test Langfuse adapter initialization."""

    def test_initialization_with_credentials(self, mock_langfuse):
        """Test adapter initialization with credentials."""
        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
            host="https://cloud.langfuse.com",
        )

        mock_langfuse.assert_called_once_with(
            public_key="pk-test",
            secret_key="sk-test",
            host="https://cloud.langfuse.com",
        )
        assert adapter._client is not None

    def test_initialization_default_host(self, mock_langfuse):
        """Test adapter initialization with default host."""
        LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
        )

        mock_langfuse.assert_called_once_with(
            public_key="pk-test",
            secret_key="sk-test",
            host="https://cloud.langfuse.com",
        )


class TestStartTrace:
    """Test start_trace method."""

    def test_start_trace_without_metadata(self, langfuse_adapter):
        """Test starting a trace without metadata."""
        mock_span = MagicMock()
        mock_span.trace_id = "trace-123"
        langfuse_adapter._client.start_span.return_value = mock_span

        trace_id = langfuse_adapter.start_trace(name="test-trace")

        assert trace_id == "trace-123"
        langfuse_adapter._client.start_span.assert_called_once_with(name="test-trace")
        mock_span.update_trace.assert_not_called()
        assert "trace-123" in langfuse_adapter._traces

    def test_start_trace_with_metadata(self, langfuse_adapter):
        """Test starting a trace with metadata."""
        mock_span = MagicMock()
        mock_span.trace_id = "trace-456"
        langfuse_adapter._client.start_span.return_value = mock_span

        metadata = {"dataset": "test-dataset", "version": "1.0.0"}
        trace_id = langfuse_adapter.start_trace(name="evaluation-run", metadata=metadata)

        assert trace_id == "trace-456"
        langfuse_adapter._client.start_span.assert_called_once_with(name="evaluation-run")
        # update_trace should be called to set trace-level name and metadata
        mock_span.update_trace.assert_called_once_with(name="evaluation-run", metadata=metadata)


class TestAddSpan:
    """Test add_span method."""

    def test_add_span_without_data(self, langfuse_adapter):
        """Test adding a span without input/output data."""
        mock_root_span = MagicMock()
        mock_child_span = MagicMock()
        mock_root_span.start_span.return_value = mock_child_span
        langfuse_adapter._traces["trace-123"] = mock_root_span

        langfuse_adapter.add_span(trace_id="trace-123", name="test-span")

        mock_root_span.start_span.assert_called_once_with(
            name="test-span",
            input=None,
            output=None,
        )
        mock_child_span.end.assert_called_once()

    def test_add_span_with_input_output(self, langfuse_adapter):
        """Test adding a span with input and output data."""
        mock_root_span = MagicMock()
        mock_child_span = MagicMock()
        mock_root_span.start_span.return_value = mock_child_span
        langfuse_adapter._traces["trace-123"] = mock_root_span

        input_data = {"question": "What is Python?"}
        output_data = {"answer": "A programming language"}

        langfuse_adapter.add_span(
            trace_id="trace-123",
            name="llm-call",
            input_data=input_data,
            output_data=output_data,
        )

        mock_root_span.start_span.assert_called_once_with(
            name="llm-call",
            input=input_data,
            output=output_data,
        )
        mock_child_span.end.assert_called_once()

    def test_add_span_trace_not_found(self, langfuse_adapter):
        """Test adding a span to non-existent trace raises error."""
        with pytest.raises(ValueError, match="Trace not found"):
            langfuse_adapter.add_span(
                trace_id="non-existent",
                name="span",
            )


class TestLogScore:
    """Test log_score method."""

    def test_log_score_without_comment(self, langfuse_adapter):
        """Test logging a score without comment."""
        mock_root_span = MagicMock()
        langfuse_adapter._traces["trace-123"] = mock_root_span

        langfuse_adapter.log_score(
            trace_id="trace-123",
            name="faithfulness",
            value=0.85,
        )

        mock_root_span.score_trace.assert_called_once_with(
            name="faithfulness",
            value=0.85,
            comment=None,
        )

    def test_log_score_with_comment(self, langfuse_adapter):
        """Test logging a score with comment."""
        mock_root_span = MagicMock()
        langfuse_adapter._traces["trace-123"] = mock_root_span

        langfuse_adapter.log_score(
            trace_id="trace-123",
            name="answer_relevancy",
            value=0.92,
            comment="RAGAS evaluation result",
        )

        mock_root_span.score_trace.assert_called_once_with(
            name="answer_relevancy",
            value=0.92,
            comment="RAGAS evaluation result",
        )

    def test_log_score_trace_not_found(self, langfuse_adapter):
        """Test logging score to non-existent trace raises error."""
        with pytest.raises(ValueError, match="Trace not found"):
            langfuse_adapter.log_score(
                trace_id="non-existent",
                name="score",
                value=0.5,
            )


class TestSaveArtifact:
    """Test save_artifact method."""

    def test_save_artifact_json(self, langfuse_adapter):
        """Test saving JSON artifact."""
        mock_root_span = MagicMock()
        langfuse_adapter._traces["trace-123"] = mock_root_span

        data = {"key": "value", "number": 123}
        langfuse_adapter.save_artifact(
            trace_id="trace-123",
            name="test-artifact",
            data=data,
            artifact_type="json",
        )

        mock_root_span.update_trace.assert_called_once()
        call_kwargs = mock_root_span.update_trace.call_args[1]
        assert call_kwargs["metadata"]["artifact_test-artifact"] == data
        assert call_kwargs["metadata"]["artifact_test-artifact_type"] == "json"

    def test_save_artifact_text(self, langfuse_adapter):
        """Test saving text artifact."""
        mock_root_span = MagicMock()
        langfuse_adapter._traces["trace-123"] = mock_root_span

        data = "This is a text artifact"
        langfuse_adapter.save_artifact(
            trace_id="trace-123",
            name="log-output",
            data=data,
            artifact_type="text",
        )

        mock_root_span.update_trace.assert_called_once()
        call_kwargs = mock_root_span.update_trace.call_args[1]
        assert call_kwargs["metadata"]["artifact_log-output"] == data
        assert call_kwargs["metadata"]["artifact_log-output_type"] == "text"

    def test_save_artifact_trace_not_found(self, langfuse_adapter):
        """Test saving artifact to non-existent trace raises error."""
        with pytest.raises(ValueError, match="Trace not found"):
            langfuse_adapter.save_artifact(
                trace_id="non-existent",
                name="artifact",
                data={},
            )


class TestEndTrace:
    """Test end_trace method."""

    def test_end_trace(self, langfuse_adapter):
        """Test ending a trace."""
        mock_root_span = MagicMock()
        langfuse_adapter._traces["trace-123"] = mock_root_span

        langfuse_adapter.end_trace(trace_id="trace-123")

        mock_root_span.end.assert_called_once()
        langfuse_adapter._client.flush.assert_called_once()
        assert "trace-123" not in langfuse_adapter._traces

    def test_end_trace_not_found(self, langfuse_adapter):
        """Test ending a non-existent trace raises error."""
        with pytest.raises(ValueError, match="Trace not found"):
            langfuse_adapter.end_trace(trace_id="non-existent")


class TestLogEvaluationRun:
    """Test log_evaluation_run method."""

    def test_log_evaluation_run_complete(self, langfuse_adapter):
        """Test logging a complete evaluation run."""
        # Create evaluation run with results
        run = EvaluationRun(
            run_id="run-123",
            dataset_name="test-dataset",
            dataset_version="1.0.0",
            model_name="gpt-4o",
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            finished_at=datetime(2024, 1, 1, 12, 5, 0),
            metrics_evaluated=["faithfulness", "answer_relevancy"],
            thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[
                        MetricScore(name="faithfulness", score=0.85, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.92, threshold=0.7),
                    ],
                    tokens_used=1500,
                    latency_ms=250,
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    metrics=[
                        MetricScore(name="faithfulness", score=0.78, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.88, threshold=0.7),
                    ],
                    tokens_used=1200,
                    latency_ms=200,
                ),
            ],
            total_tokens=2700,
        )

        # Mock start_span() method for log_evaluation_run (Langfuse v3 API)
        mock_span = MagicMock()
        mock_span.trace_id = "trace-eval-123"
        langfuse_adapter._client.start_span.return_value = mock_span

        with patch.object(
            langfuse_adapter, "save_artifact", wraps=langfuse_adapter.save_artifact
        ) as mock_save_artifact:
            trace_id = langfuse_adapter.log_evaluation_run(run)

        # Verify trace was created with input/output
        assert trace_id == "trace-eval-123"
        langfuse_adapter._client.start_span.assert_called_once()

        # Verify update_trace was called with input/output
        assert mock_span.update_trace.call_count >= 1
        update_call = mock_span.update_trace.call_args_list[0]

        # Verify trace input contains dataset and config
        assert "input" in update_call[1]
        assert update_call[1]["input"]["dataset"]["name"] == "test-dataset"
        assert update_call[1]["input"]["evaluation_config"]["model"] == "gpt-4o"

        # Verify trace output contains summary
        assert "output" in update_call[1]
        assert update_call[1]["output"]["summary"]["total_test_cases"] == 2
        assert update_call[1]["output"]["summary"]["pass_rate"] == 1.0

        # Verify metadata
        assert update_call[1]["metadata"]["dataset_name"] == "test-dataset"
        assert update_call[1]["metadata"]["model_name"] == "gpt-4o"
        assert update_call[1]["metadata"]["total_test_cases"] == 2

        # Verify metadata includes event type
        assert update_call[1]["metadata"]["event_type"] == "ragas_evaluation"

        # Verify child spans were created for each test case
        assert mock_span.start_span.call_count == 2

        # Verify scores were logged (score_trace is called due to MagicMock having all attrs)
        assert mock_span.score_trace.call_count >= 2  # At least avg scores

        # Verify structured artifact saved
        mock_save_artifact.assert_called_once()
        artifact_payload = mock_save_artifact.call_args[1]["data"]
        assert artifact_payload["type"] == "ragas_evaluation"

        # Verify flush was called
        langfuse_adapter._client.flush.assert_called_once()

    def test_log_evaluation_run_with_failures(self, langfuse_adapter):
        """Test logging evaluation run with some failed test cases."""
        run = EvaluationRun(
            run_id="run-456",
            dataset_name="test-dataset",
            dataset_version="1.0.0",
            model_name="gpt-4o",
            metrics_evaluated=["faithfulness"],
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="faithfulness", score=0.85, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    metrics=[MetricScore(name="faithfulness", score=0.5, threshold=0.7)],
                ),
            ],
        )

        # Mock start_span() method (Langfuse v3 API)
        mock_span = MagicMock()
        mock_span.trace_id = "trace-eval-456"
        langfuse_adapter._client.start_span.return_value = mock_span

        trace_id = langfuse_adapter.log_evaluation_run(run)

        assert trace_id == "trace-eval-456"
        # Verify metadata via update_trace call
        update_call = mock_span.update_trace.call_args_list[0]
        assert update_call[1]["metadata"]["passed_test_cases"] == 1
        # 메트릭 "faithfulness"의 평균: (0.85 + 0.5) / 2 = 0.675 < 0.7 → 실패
        assert update_call[1]["metadata"]["pass_rate"] == 0.0  # 메트릭 기준 통과율
        # Verify output shows failure
        assert update_call[1]["output"]["summary"]["passed"] == 1
        assert update_call[1]["output"]["summary"]["failed"] == 1

    def test_log_evaluation_run_empty_results(self, langfuse_adapter):
        """Test logging evaluation run with no results."""
        run = EvaluationRun(
            run_id="run-empty",
            dataset_name="test-dataset",
            dataset_version="1.0.0",
            model_name="gpt-4o",
        )

        # Mock start_span() method (Langfuse v3 API)
        mock_span = MagicMock()
        mock_span.trace_id = "trace-empty"
        langfuse_adapter._client.start_span.return_value = mock_span

        trace_id = langfuse_adapter.log_evaluation_run(run)

        assert trace_id == "trace-empty"
        # Verify metadata via update_trace call
        update_call = mock_span.update_trace.call_args_list[0]
        assert update_call[1]["metadata"]["total_test_cases"] == 0
        assert update_call[1]["metadata"]["pass_rate"] == 0.0
        # Verify no child spans created
        assert mock_span.start_span.call_count == 0
