"""Integration tests for Phoenix tracking flow.

Tests marked with @pytest.mark.requires_phoenix require Phoenix dependencies.
These tests verify OpenTelemetry-based tracing with real dependencies.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from evalvault.domain.entities import (
    EvaluationRun,
    MetricScore,
    TestCaseResult,
)
from tests.integration.conftest import get_test_model


class TestPhoenixFlowWithMock:
    """Mock을 사용한 Phoenix 플로우 통합 테스트."""

    @pytest.fixture
    def sample_evaluation_run(self):
        """테스트용 평가 결과."""
        started_at = datetime.now()
        finished_at = started_at + timedelta(seconds=30)
        tc1_started = started_at + timedelta(seconds=1)
        tc1_finished = started_at + timedelta(seconds=15)
        tc2_started = started_at + timedelta(seconds=16)
        tc2_finished = started_at + timedelta(seconds=29)

        return EvaluationRun(
            dataset_name="phoenix-integration-test",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            started_at=started_at,
            finished_at=finished_at,
            metrics_evaluated=["faithfulness", "answer_relevancy"],
            thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7},
            total_tokens=1250,
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[
                        MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.85, threshold=0.7),
                    ],
                    tokens_used=650,
                    latency_ms=14000,
                    started_at=tc1_started,
                    finished_at=tc1_finished,
                    question="이 보험의 보장금액은 얼마인가요?",
                    answer="보장금액은 1억원입니다.",
                    contexts=["해당 보험의 사망 보장금액은 1억원입니다."],
                    ground_truth="1억원",
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    metrics=[
                        MetricScore(name="faithfulness", score=0.7, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.8, threshold=0.7),
                    ],
                    tokens_used=600,
                    latency_ms=13000,
                    started_at=tc2_started,
                    finished_at=tc2_finished,
                    question="보험료 납입 기간은 어떻게 되나요?",
                    answer="납입 기간은 10년입니다.",
                    contexts=["보험료 납입 기간은 10년으로 설정됩니다."],
                    ground_truth="10년",
                ),
            ],
        )

    def test_phoenix_adapter_initialization(self):
        """PhoenixAdapter 초기화 테스트."""
        from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

        adapter = PhoenixAdapter(
            endpoint="http://localhost:6006/v1/traces",
            service_name="evalvault-test",
        )

        assert adapter._endpoint == "http://localhost:6006/v1/traces"
        assert adapter._service_name == "evalvault-test"
        assert adapter._initialized is False

    def test_phoenix_adapter_with_mocked_otel(self, sample_evaluation_run):
        """Mocked OpenTelemetry로 PhoenixAdapter 테스트."""
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

        # Patch the internal method
        with patch.object(adapter, "_log_test_case_span"):
            trace_id = adapter.log_evaluation_run(sample_evaluation_run)

        assert trace_id is not None
        assert mock_tracer.start_span.called
        mock_provider.force_flush.assert_called()

    def test_phoenix_adapter_start_and_end_trace(self):
        """start_trace와 end_trace 플로우 테스트."""
        from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

        adapter = PhoenixAdapter()
        adapter._initialized = True

        # Setup mocks
        mock_tracer = MagicMock()
        mock_provider = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        adapter._tracer = mock_tracer
        adapter._tracer_provider = mock_provider

        # Start trace
        trace_id = adapter.start_trace(
            name="test-trace",
            metadata={"test_key": "test_value"},
        )

        assert trace_id is not None
        assert trace_id in adapter._active_spans
        mock_tracer.start_span.assert_called_with("test-trace")

        # Log score
        adapter.log_score(
            trace_id=trace_id,
            name="faithfulness",
            value=0.85,
            comment="Good score",
        )
        mock_span.set_attribute.assert_any_call("score.faithfulness", 0.85)

        # End trace
        adapter.end_trace(trace_id)
        mock_span.end.assert_called_once()
        mock_provider.force_flush.assert_called()
        assert trace_id not in adapter._active_spans


@pytest.mark.requires_phoenix
class TestPhoenixFlowWithRealDependencies:
    """실제 OpenTelemetry 의존성을 사용한 Phoenix 플로우 테스트.

    이 테스트는 실제 Phoenix 서버 없이 OpenTelemetry SDK만 사용합니다.
    Phoenix 서버가 실행 중이면 실제로 트레이스가 전송됩니다.
    """

    @pytest.fixture
    def sample_evaluation_run(self):
        """테스트용 평가 결과."""
        started_at = datetime.now()
        finished_at = started_at + timedelta(seconds=5)

        return EvaluationRun(
            dataset_name="phoenix-e2e-test",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            started_at=started_at,
            finished_at=finished_at,
            metrics_evaluated=["faithfulness"],
            thresholds={"faithfulness": 0.7},
            total_tokens=500,
            results=[
                TestCaseResult(
                    test_case_id="tc-e2e-001",
                    metrics=[
                        MetricScore(name="faithfulness", score=0.92, threshold=0.7),
                    ],
                    tokens_used=500,
                    latency_ms=5000,
                    started_at=started_at,
                    finished_at=finished_at,
                    question="What is the coverage amount?",
                    answer="The coverage amount is $1 million.",
                    contexts=["The policy provides $1 million coverage."],
                    ground_truth="$1 million",
                ),
            ],
        )

    def test_phoenix_adapter_with_real_otel(self, sample_evaluation_run):
        """실제 OpenTelemetry SDK로 PhoenixAdapter 테스트."""
        from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

        # Use a non-existent endpoint to avoid actual network calls
        adapter = PhoenixAdapter(
            endpoint="http://localhost:19999/v1/traces",
            service_name="evalvault-e2e-test",
        )

        # This will initialize OpenTelemetry
        trace_id = adapter.log_evaluation_run(sample_evaluation_run)

        assert trace_id is not None
        assert adapter._initialized is True
        assert adapter._tracer is not None

        # Cleanup
        adapter.shutdown()
        assert adapter._initialized is False


class TestPhoenixInstrumentation:
    """Phoenix instrumentation 테스트."""

    def test_instrumentation_setup_without_dependencies(self):
        """OpenTelemetry 의존성 없이 instrumentation 설정 테스트."""
        from evalvault.config.instrumentation import (
            is_instrumentation_enabled,
            shutdown_instrumentation,
        )

        # Initially should be disabled
        # (may be enabled from previous tests, so we shutdown first)
        shutdown_instrumentation()
        assert is_instrumentation_enabled() is False

    @pytest.mark.requires_phoenix
    def test_instrumentation_setup_with_dependencies(self):
        """실제 OpenTelemetry 의존성으로 instrumentation 설정 테스트."""
        from evalvault.config.instrumentation import (
            get_tracer_provider,
            is_instrumentation_enabled,
            setup_phoenix_instrumentation,
            shutdown_instrumentation,
        )

        # Ensure clean state
        shutdown_instrumentation()

        # Setup instrumentation
        provider = setup_phoenix_instrumentation(
            endpoint="http://localhost:19999/v1/traces",
            service_name="evalvault-instrumentation-test",
            enable_langchain=False,  # Skip if not installed
            enable_openai=False,  # Skip if not installed
        )

        assert provider is not None
        assert is_instrumentation_enabled() is True
        assert get_tracer_provider() is provider

        # Cleanup
        shutdown_instrumentation()
        assert is_instrumentation_enabled() is False


class TestPhoenixCLIIntegration:
    """Phoenix CLI 통합 테스트."""

    def test_tracker_option_parsing(self):
        """--tracker 옵션 파싱 테스트."""
        from typer.testing import CliRunner

        from evalvault.adapters.inbound.cli.app import app

        runner = CliRunner()

        # Test help includes phoenix option
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "phoenix" in result.stdout

    def test_settings_have_phoenix_fields(self):
        """Settings에 Phoenix 필드가 있는지 테스트."""
        from evalvault.config.settings import Settings

        fields = Settings.model_fields

        assert "phoenix_endpoint" in fields
        assert "phoenix_enabled" in fields
        assert "tracker_provider" in fields

        # Check defaults
        assert fields["phoenix_endpoint"].default == "http://localhost:6006/v1/traces"
        assert fields["phoenix_enabled"].default is False

    def test_tracker_module_exports(self):
        """Tracker 모듈에서 PhoenixAdapter가 export되는지 테스트."""
        from evalvault.adapters.outbound import tracker

        assert hasattr(tracker, "PhoenixAdapter")
        assert hasattr(tracker, "LangfuseAdapter")
        assert hasattr(tracker, "MLflowAdapter")
