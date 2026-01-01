"""Unit tests for PhoenixAdapter.

Phoenix는 OpenTelemetry 기반 RAG 옵저버빌리티 플랫폼입니다.
Langfuse 대비 검색 품질 분석, 임베딩 시각화 등 RAG 특화 기능을 제공합니다.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_otel():
    """Mock OpenTelemetry dependencies for all tests."""
    mock_tracer = MagicMock()
    mock_span = MagicMock()
    mock_tracer.start_span.return_value = mock_span

    mock_tracer_provider = MagicMock()
    mock_trace = MagicMock()
    mock_trace.get_tracer.return_value = mock_tracer

    with patch.multiple(
        "evalvault.adapters.outbound.tracker.phoenix_adapter",
        create=True,
    ):
        yield {
            "tracer": mock_tracer,
            "span": mock_span,
            "tracer_provider": mock_tracer_provider,
            "trace": mock_trace,
        }


class TestPhoenixAdapter:
    """PhoenixAdapter 단위 테스트."""

    def test_adapter_initialization(self):
        """어댑터 초기화 테스트."""
        from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

        adapter = PhoenixAdapter(
            endpoint="http://localhost:6006/v1/traces",
            service_name="evalvault-test",
        )

        assert adapter._endpoint == "http://localhost:6006/v1/traces"
        assert adapter._service_name == "evalvault-test"
        assert adapter._initialized is False
        assert adapter._active_spans == {}

    def test_default_values(self):
        """기본값 테스트."""
        from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

        adapter = PhoenixAdapter()

        assert adapter._endpoint == "http://localhost:6006/v1/traces"
        assert adapter._service_name == "evalvault"

    def test_start_trace_adds_to_active_spans(self):
        """start_trace가 active_spans에 추가하는지 테스트."""
        from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

        adapter = PhoenixAdapter()
        adapter._initialized = True

        # Mock tracer
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_span.return_value = mock_span
        adapter._tracer = mock_tracer

        trace_id = adapter.start_trace(
            name="test-trace",
            metadata={"key": "value"},
        )

        assert trace_id is not None
        assert trace_id in adapter._active_spans
        mock_tracer.start_span.assert_called_once_with("test-trace")

    def test_log_score_sets_attribute(self):
        """log_score가 span attribute를 설정하는지 테스트."""
        from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

        adapter = PhoenixAdapter()
        adapter._initialized = True

        # Setup mock span
        mock_span = MagicMock()
        trace_id = "test-trace-id"
        adapter._active_spans[trace_id] = mock_span

        adapter.log_score(
            trace_id=trace_id,
            name="faithfulness",
            value=0.85,
            comment="Good faithfulness",
        )

        mock_span.set_attribute.assert_any_call("score.faithfulness", 0.85)
        mock_span.set_attribute.assert_any_call(
            "score.faithfulness.comment",
            "Good faithfulness",
        )

    def test_log_score_not_found_raises_error(self):
        """존재하지 않는 trace_id에 대한 log_score 테스트."""
        from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

        adapter = PhoenixAdapter()
        adapter._initialized = True

        with pytest.raises(ValueError, match="Trace not found"):
            adapter.log_score(
                trace_id="non-existent",
                name="faithfulness",
                value=0.85,
            )

    def test_save_artifact_sets_attribute(self):
        """save_artifact가 span attribute를 설정하는지 테스트."""
        from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

        adapter = PhoenixAdapter()
        adapter._initialized = True

        # Setup mock span
        mock_span = MagicMock()
        trace_id = "test-trace-id"
        adapter._active_spans[trace_id] = mock_span

        adapter.save_artifact(
            trace_id=trace_id,
            name="test_artifact",
            data={"key": "value"},
            artifact_type="json",
        )

        # Verify attribute was set
        assert mock_span.set_attribute.called

    def test_end_trace_removes_from_active_spans(self):
        """end_trace가 active_spans에서 제거하는지 테스트."""
        from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

        adapter = PhoenixAdapter()
        adapter._initialized = True

        # Setup mock span and tracer provider
        mock_span = MagicMock()
        mock_provider = MagicMock()
        trace_id = "test-trace-id"
        adapter._active_spans[trace_id] = mock_span
        adapter._tracer_provider = mock_provider

        adapter.end_trace(trace_id)

        mock_span.end.assert_called_once()
        mock_provider.force_flush.assert_called_once()
        assert trace_id not in adapter._active_spans

    def test_end_trace_not_found_raises_error(self):
        """존재하지 않는 trace_id에 대한 end_trace 테스트."""
        from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

        adapter = PhoenixAdapter()
        adapter._initialized = True

        with pytest.raises(ValueError, match="Trace not found"):
            adapter.end_trace("non-existent")

    def test_tracker_port_methods_exist(self):
        """TrackerPort 인터페이스 메서드가 존재하는지 테스트."""
        from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

        adapter = PhoenixAdapter()

        # Check required methods exist
        assert hasattr(adapter, "start_trace")
        assert hasattr(adapter, "add_span")
        assert hasattr(adapter, "log_score")
        assert hasattr(adapter, "save_artifact")
        assert hasattr(adapter, "end_trace")
        assert hasattr(adapter, "log_evaluation_run")


class TestPhoenixAdapterWithEvaluationRun:
    """PhoenixAdapter log_evaluation_run 테스트."""

    @pytest.fixture
    def mock_evaluation_run(self):
        """Mock EvaluationRun fixture."""
        from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult

        metric1 = MetricScore(
            name="faithfulness",
            score=0.85,
            threshold=0.7,
        )
        metric2 = MetricScore(
            name="answer_relevancy",
            score=0.72,
            threshold=0.7,
        )

        result1 = TestCaseResult(
            test_case_id="tc-001",
            question="What is the coverage?",
            answer="The coverage is $1M.",
            contexts=["Coverage information..."],
            ground_truth="$1M coverage",
            metrics=[metric1, metric2],
            tokens_used=150,
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
        )

        run = EvaluationRun(
            dataset_name="test-dataset",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            metrics_evaluated=["faithfulness", "answer_relevancy"],
            thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7},
            results=[result1],
        )

        return run

    def test_log_evaluation_run_flow(self, mock_evaluation_run):
        """log_evaluation_run 전체 흐름 테스트."""
        from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

        adapter = PhoenixAdapter()
        adapter._initialized = True

        # Setup mocks
        mock_tracer = MagicMock()
        mock_provider = MagicMock()

        # Configure mock span as context manager
        mock_child_span = MagicMock()
        mock_child_span.__enter__ = MagicMock(return_value=mock_child_span)
        mock_child_span.__exit__ = MagicMock(return_value=False)

        mock_tracer.start_span.return_value = mock_child_span

        adapter._tracer = mock_tracer
        adapter._tracer_provider = mock_provider

        # Patch the trace module import inside the method
        with patch.object(adapter, "_log_test_case_span"):
            trace_id = adapter.log_evaluation_run(mock_evaluation_run)

        assert trace_id is not None
        # Verify tracer was called (for start_trace)
        assert mock_tracer.start_span.called


class TestPhoenixSettings:
    """Phoenix 설정 테스트."""

    def test_settings_have_phoenix_fields(self):
        """Settings에 Phoenix 필드가 있는지 테스트."""
        from evalvault.config.settings import Settings

        # Check field definitions exist in model
        fields = Settings.model_fields

        assert "phoenix_endpoint" in fields
        assert "phoenix_enabled" in fields
        assert "tracker_provider" in fields

        # Check default values from field definitions
        assert fields["phoenix_endpoint"].default == "http://localhost:6006/v1/traces"
        assert fields["phoenix_enabled"].default is False
        assert fields["tracker_provider"].default == "langfuse"


class TestTrackerModuleExports:
    """Tracker 모듈 export 테스트."""

    def test_phoenix_adapter_exported(self):
        """PhoenixAdapter가 tracker 모듈에서 export되는지 테스트."""
        from evalvault.adapters.outbound.tracker import PhoenixAdapter

        assert PhoenixAdapter is not None

    def test_all_adapters_exported(self):
        """모든 어댑터가 export되는지 테스트."""
        from evalvault.adapters.outbound import tracker

        assert hasattr(tracker, "LangfuseAdapter")
        assert hasattr(tracker, "MLflowAdapter")
        assert hasattr(tracker, "PhoenixAdapter")
