"""Integration tests for Langfuse tracking flow.

Tests marked with @pytest.mark.requires_langfuse require Langfuse credentials.
These tests are designed for self-hosted Langfuse instances.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from evalvault.domain.entities import (
    EvaluationRun,
    TestCaseResult,
    MetricScore,
)
from evalvault.adapters.outbound.tracker.langfuse_adapter import LangfuseAdapter
from evalvault.ports.outbound.tracker_port import TrackerPort
from tests.integration.conftest import get_test_model


class TestLangfuseFlowWithMock:
    """Mock을 사용한 Langfuse 플로우 통합 테스트."""

    @pytest.fixture
    def sample_evaluation_run(self):
        """테스트용 평가 결과."""
        return EvaluationRun(
            dataset_name="integration-test",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            started_at=datetime.now(),
            finished_at=datetime.now() + timedelta(seconds=30),
            metrics_evaluated=["faithfulness", "answer_relevancy"],
            thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[
                        MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.85, threshold=0.7),
                    ],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    metrics=[
                        MetricScore(name="faithfulness", score=0.7, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.8, threshold=0.7),
                    ],
                ),
            ],
        )

    @patch("evalvault.adapters.outbound.tracker.langfuse_adapter.Langfuse")
    def test_log_evaluation_run_creates_trace(
        self, mock_langfuse_cls, sample_evaluation_run
    ):
        """log_evaluation_run이 trace를 생성하는지 테스트."""
        # Setup mock for Langfuse v3 start_span() API
        mock_langfuse = MagicMock()
        mock_span = MagicMock()
        mock_span.trace_id = "trace-123"
        mock_langfuse.start_span.return_value = mock_span
        mock_langfuse_cls.return_value = mock_langfuse

        # Create adapter and log run
        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
            host="http://localhost:3000",  # Self-hosted
        )
        trace_id = adapter.log_evaluation_run(sample_evaluation_run)

        # Verify trace was created with input/output
        assert trace_id == "trace-123"
        mock_langfuse.start_span.assert_called_once()
        update_call = mock_span.update_trace.call_args
        assert "input" in update_call[1]
        assert "output" in update_call[1]

    @patch("evalvault.adapters.outbound.tracker.langfuse_adapter.Langfuse")
    def test_log_evaluation_run_logs_scores(
        self, mock_langfuse_cls, sample_evaluation_run
    ):
        """log_evaluation_run이 점수를 로깅하는지 테스트."""
        mock_langfuse = MagicMock()
        mock_span = MagicMock()
        mock_span.trace_id = "trace-123"
        mock_langfuse.start_span.return_value = mock_span
        mock_langfuse_cls.return_value = mock_langfuse

        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
            host="http://localhost:3000",
        )
        adapter.log_evaluation_run(sample_evaluation_run)

        # Verify scores were logged (via score_trace due to MagicMock)
        assert mock_span.score_trace.called

    @patch("evalvault.adapters.outbound.tracker.langfuse_adapter.Langfuse")
    def test_complete_tracking_flow(self, mock_langfuse_cls):
        """전체 트래킹 플로우 테스트."""
        mock_langfuse = MagicMock()
        mock_root_span = MagicMock()
        mock_root_span.trace_id = "trace-456"
        mock_child_span = MagicMock()
        mock_root_span.start_span.return_value = mock_child_span
        mock_langfuse.start_span.return_value = mock_root_span
        mock_langfuse_cls.return_value = mock_langfuse

        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
            host="http://localhost:3000",
        )

        # Start trace
        trace_id = adapter.start_trace(
            name="evaluation-run",
            metadata={"dataset": "test", "model": "gpt-4o"},
        )
        assert trace_id == "trace-456"

        # Add span
        adapter.add_span(
            trace_id=trace_id,
            name="test-case-evaluation",
            input_data={"question": "What is Python?"},
            output_data={"answer": "A programming language."},
        )

        # Log score
        adapter.log_score(
            trace_id=trace_id, name="faithfulness", value=0.9, comment="Good"
        )

        # End trace
        adapter.end_trace(trace_id)

        # Verify flush was called
        mock_langfuse.flush.assert_called()


class TestRealLangfuseFlow:
    """실제 Langfuse 인스턴스를 사용하는 테스트.

    이 테스트는 LANGFUSE_PUBLIC_KEY와 LANGFUSE_SECRET_KEY가
    설정되어 있을 때만 실행됩니다.

    셀프호스팅 환경에서는 LANGFUSE_HOST 환경변수도 설정해야 합니다.
    """

    @pytest.fixture
    def sample_run(self):
        """테스트용 간단한 평가 결과."""
        return EvaluationRun(
            dataset_name="real-langfuse-test",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            started_at=datetime.now(),
            finished_at=datetime.now() + timedelta(seconds=5),
            metrics_evaluated=["faithfulness"],
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[
                        MetricScore(name="faithfulness", score=0.85, threshold=0.7),
                    ],
                ),
            ],
        )

    @pytest.mark.requires_langfuse
    def test_real_langfuse_trace_creation(self, sample_run):
        """실제 Langfuse 서버에 trace 생성 테스트."""
        import os

        adapter = LangfuseAdapter(
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )

        trace_id = adapter.log_evaluation_run(sample_run)
        assert trace_id is not None
        assert len(trace_id) > 0


class TestTrackerPortCompliance:
    """TrackerPort 인터페이스 준수 테스트."""

    @patch("evalvault.adapters.outbound.tracker.langfuse_adapter.Langfuse")
    def test_adapter_implements_protocol(self, mock_langfuse_cls):
        """LangfuseAdapter가 TrackerPort를 구현하는지 테스트."""
        mock_langfuse = MagicMock()
        mock_langfuse_cls.return_value = mock_langfuse

        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
            host="http://localhost:3000",
        )

        # Check all required methods exist
        assert hasattr(adapter, "start_trace")
        assert hasattr(adapter, "add_span")
        assert hasattr(adapter, "log_score")
        assert hasattr(adapter, "save_artifact")
        assert hasattr(adapter, "end_trace")
        assert hasattr(adapter, "log_evaluation_run")

        # Check methods are callable
        assert callable(adapter.start_trace)
        assert callable(adapter.add_span)
        assert callable(adapter.log_score)
        assert callable(adapter.save_artifact)
        assert callable(adapter.end_trace)
        assert callable(adapter.log_evaluation_run)
