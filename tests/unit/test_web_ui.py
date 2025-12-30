"""Unit tests for Web UI adapter."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from evalvault.ports.inbound.web_port import (
    EvalProgress,
    EvalRequest,
    RunFilters,
    RunSummary,
)

if TYPE_CHECKING:
    pass


class TestEvalRequest:
    """EvalRequest 데이터 클래스 테스트."""

    def test_create_with_defaults(self):
        """기본값으로 생성."""
        request = EvalRequest(
            dataset_path="/path/to/dataset.json",
            metrics=["faithfulness", "answer_relevancy"],
        )

        assert request.dataset_path == "/path/to/dataset.json"
        assert request.metrics == ["faithfulness", "answer_relevancy"]
        assert request.model_name == "gpt-5-nano"
        assert request.langfuse_enabled is False
        assert request.thresholds == {}

    def test_create_with_custom_values(self):
        """커스텀 값으로 생성."""
        request = EvalRequest(
            dataset_path="/path/to/dataset.csv",
            metrics=["faithfulness"],
            model_name="gpt-4",
            langfuse_enabled=True,
            thresholds={"faithfulness": 0.8},
        )

        assert request.model_name == "gpt-4"
        assert request.langfuse_enabled is True
        assert request.thresholds == {"faithfulness": 0.8}


class TestEvalProgress:
    """EvalProgress 데이터 클래스 테스트."""

    def test_create_progress(self):
        """진행 상태 생성."""
        progress = EvalProgress(
            current=5,
            total=10,
            current_metric="faithfulness",
            percent=50.0,
        )

        assert progress.current == 5
        assert progress.total == 10
        assert progress.current_metric == "faithfulness"
        assert progress.percent == 50.0
        assert progress.status == "running"
        assert progress.error_message is None

    def test_create_completed_progress(self):
        """완료 상태 생성."""
        progress = EvalProgress(
            current=10,
            total=10,
            current_metric="",
            percent=100.0,
            status="completed",
        )

        assert progress.status == "completed"

    def test_create_failed_progress(self):
        """실패 상태 생성."""
        progress = EvalProgress(
            current=3,
            total=10,
            current_metric="faithfulness",
            percent=30.0,
            status="failed",
            error_message="API error",
        )

        assert progress.status == "failed"
        assert progress.error_message == "API error"


class TestRunSummary:
    """RunSummary 데이터 클래스 테스트."""

    def test_create_summary(self):
        """요약 정보 생성."""
        now = datetime.now()
        summary = RunSummary(
            run_id="run-123",
            dataset_name="test-dataset",
            model_name="gpt-5-nano",
            pass_rate=0.85,
            total_test_cases=100,
            started_at=now,
            finished_at=now,
            metrics_evaluated=["faithfulness", "answer_relevancy"],
        )

        assert summary.run_id == "run-123"
        assert summary.pass_rate == 0.85
        assert summary.total_test_cases == 100
        assert len(summary.metrics_evaluated) == 2
        assert summary.total_tokens == 0
        assert summary.total_cost_usd is None

    def test_summary_with_cost(self):
        """비용 정보 포함된 요약."""
        now = datetime.now()
        summary = RunSummary(
            run_id="run-456",
            dataset_name="test-dataset",
            model_name="gpt-4",
            pass_rate=0.75,
            total_test_cases=50,
            started_at=now,
            finished_at=now,
            metrics_evaluated=["faithfulness"],
            total_tokens=5000,
            total_cost_usd=0.15,
        )

        assert summary.total_tokens == 5000
        assert summary.total_cost_usd == 0.15


class TestRunFilters:
    """RunFilters 데이터 클래스 테스트."""

    def test_empty_filters(self):
        """빈 필터 생성."""
        filters = RunFilters()

        assert filters.dataset_name is None
        assert filters.model_name is None
        assert filters.date_from is None
        assert filters.date_to is None
        assert filters.min_pass_rate is None
        assert filters.max_pass_rate is None

    def test_with_filters(self):
        """필터 조건 설정."""
        filters = RunFilters(
            dataset_name="insurance-qa",
            model_name="gpt-5-nano",
            min_pass_rate=0.7,
            max_pass_rate=1.0,
        )

        assert filters.dataset_name == "insurance-qa"
        assert filters.model_name == "gpt-5-nano"
        assert filters.min_pass_rate == 0.7
        assert filters.max_pass_rate == 1.0


class TestWebUIAdapter:
    """WebUIAdapter 테스트."""

    @pytest.fixture
    def mock_storage(self):
        """Mock storage adapter."""
        storage = MagicMock()
        storage.list_runs.return_value = []
        storage.get_run.return_value = MagicMock()
        storage.delete_run.return_value = True
        return storage

    @pytest.fixture
    def mock_evaluator(self):
        """Mock evaluator service."""
        evaluator = MagicMock()
        return evaluator

    def test_adapter_can_be_imported(self):
        """어댑터 임포트 확인."""
        from evalvault.adapters.inbound.web.adapter import WebUIAdapter

        assert WebUIAdapter is not None

    def test_get_available_metrics(self, mock_storage, mock_evaluator):
        """사용 가능한 메트릭 목록 조회."""
        from evalvault.adapters.inbound.web.adapter import WebUIAdapter

        adapter = WebUIAdapter(
            storage=mock_storage,
            evaluator=mock_evaluator,
        )
        metrics = adapter.get_available_metrics()
        assert isinstance(metrics, list)
        assert "faithfulness" in metrics
        assert "answer_relevancy" in metrics

    def test_list_runs_empty(self, mock_storage, mock_evaluator):
        """빈 평가 목록 조회."""
        from evalvault.adapters.inbound.web.adapter import WebUIAdapter

        adapter = WebUIAdapter(storage=mock_storage, evaluator=mock_evaluator)
        runs = adapter.list_runs()
        assert runs == []

    def test_list_runs_without_storage(self):
        """저장소 없이 평가 목록 조회."""
        from evalvault.adapters.inbound.web.adapter import WebUIAdapter

        adapter = WebUIAdapter()
        runs = adapter.list_runs()
        assert runs == []

    def test_get_metric_descriptions(self, mock_storage, mock_evaluator):
        """메트릭 설명 조회."""
        from evalvault.adapters.inbound.web.adapter import WebUIAdapter

        adapter = WebUIAdapter(storage=mock_storage, evaluator=mock_evaluator)
        descriptions = adapter.get_metric_descriptions()
        assert isinstance(descriptions, dict)
        assert "faithfulness" in descriptions
        assert len(descriptions["faithfulness"]) > 0


class TestWebSession:
    """WebSession 테스트."""

    def test_session_can_be_imported(self):
        """세션 클래스 임포트 확인."""
        from evalvault.adapters.inbound.web.session import WebSession

        assert WebSession is not None

    def test_session_default_values(self):
        """세션 기본값 확인."""
        from evalvault.adapters.inbound.web.session import WebSession

        # Streamlit 없이 테스트하기 위해 직접 인스턴스 생성
        session = WebSession()
        assert session.current_run_id is None
        assert session.is_evaluating is False
        assert session.eval_progress is None
        assert session.selected_metrics == []

    def test_session_invalidate_cache(self):
        """캐시 무효화 테스트."""
        from evalvault.adapters.inbound.web.session import WebSession

        session = WebSession()
        session.runs_cache = []
        session.cache_updated_at = datetime.now()

        session.invalidate_cache()

        assert session.runs_cache is None
        assert session.cache_updated_at is None

    def test_session_reset_evaluation_state(self):
        """평가 상태 초기화 테스트."""
        from evalvault.adapters.inbound.web.session import WebSession

        session = WebSession()
        session.is_evaluating = True
        session.eval_task_id = "task-123"

        session.reset_evaluation_state()

        assert session.is_evaluating is False
        assert session.eval_task_id is None

    def test_session_get_default_metrics(self):
        """기본 메트릭 반환 테스트."""
        from evalvault.adapters.inbound.web.session import WebSession

        session = WebSession()
        metrics = session.get_default_metrics()

        assert isinstance(metrics, list)
        assert "faithfulness" in metrics
        assert "answer_relevancy" in metrics


class TestStreamlitApp:
    """Streamlit 앱 테스트."""

    def test_app_main_can_be_imported(self):
        """앱 메인 함수 임포트 확인."""
        from evalvault.adapters.inbound.web.app import main

        assert main is not None
        assert callable(main)

    def test_create_app_can_be_imported(self):
        """create_app 함수 임포트 확인."""
        from evalvault.adapters.inbound.web.app import create_app

        assert create_app is not None
        assert callable(create_app)


class TestWebComponents:
    """웹 컴포넌트 테스트."""

    def test_components_can_be_imported(self):
        """컴포넌트 패키지 임포트 확인."""
        from evalvault.adapters.inbound.web import components

        assert components is not None


class TestTheme:
    """테마 설정 테스트."""

    def test_theme_colors_defined(self):
        """테마 색상 정의 확인."""
        from evalvault.adapters.inbound.web.styles.theme import COLORS

        assert "primary" in COLORS
        assert "success" in COLORS
        assert "warning" in COLORS
        assert "error" in COLORS

    def test_pass_rate_colors_defined(self):
        """통과율 색상 정의 확인."""
        from evalvault.adapters.inbound.web.styles.theme import PASS_RATE_COLORS

        assert "excellent" in PASS_RATE_COLORS
        assert "good" in PASS_RATE_COLORS
        assert "warning" in PASS_RATE_COLORS
        assert "critical" in PASS_RATE_COLORS

    def test_get_pass_rate_color(self):
        """통과율 색상 함수 테스트."""
        from evalvault.adapters.inbound.web.styles.theme import (
            PASS_RATE_COLORS,
            get_pass_rate_color,
        )

        assert get_pass_rate_color(0.95) == PASS_RATE_COLORS["excellent"]
        assert get_pass_rate_color(0.75) == PASS_RATE_COLORS["good"]
        assert get_pass_rate_color(0.55) == PASS_RATE_COLORS["warning"]
        assert get_pass_rate_color(0.35) == PASS_RATE_COLORS["critical"]

    def test_get_pass_rate_label(self):
        """통과율 레이블 함수 테스트."""
        from evalvault.adapters.inbound.web.styles.theme import get_pass_rate_label

        assert get_pass_rate_label(0.95) == "Excellent"
        assert get_pass_rate_label(0.75) == "Good"
        assert get_pass_rate_label(0.55) == "Warning"
        assert get_pass_rate_label(0.35) == "Critical"

    def test_get_metric_color(self):
        """메트릭 색상 함수 테스트."""
        from evalvault.adapters.inbound.web.styles.theme import COLORS, get_metric_color

        # 정의된 메트릭
        assert get_metric_color("faithfulness") is not None
        # 정의되지 않은 메트릭은 primary 반환
        assert get_metric_color("unknown_metric") == COLORS["primary"]
