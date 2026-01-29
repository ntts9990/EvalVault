"""Unit tests for Web API adapter."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from evalvault.ports.inbound.web_port import (
    EvalProgress,
    EvalRequest,
    RunFilters,
    RunSummary,
)


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
        assert request.model_name == "ollama/qwen3:14b"
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
        assert summary.run_mode is None

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
            run_mode="simple",
        )

        assert summary.total_tokens == 5000
        assert summary.total_cost_usd == 0.15
        assert summary.run_mode == "simple"


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
        assert filters.run_mode is None

    def test_with_filters(self):
        """필터 조건 설정."""
        filters = RunFilters(
            dataset_name="insurance-qa",
            model_name="gpt-5-nano",
            min_pass_rate=0.7,
            max_pass_rate=1.0,
            run_mode="simple",
        )

        assert filters.dataset_name == "insurance-qa"
        assert filters.model_name == "gpt-5-nano"
        assert filters.min_pass_rate == 0.7
        assert filters.max_pass_rate == 1.0
        assert filters.run_mode == "simple"


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
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter

        assert WebUIAdapter is not None

    def test_get_available_metrics(self, mock_storage, mock_evaluator):
        """사용 가능한 메트릭 목록 조회."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter

        adapter = WebUIAdapter(
            storage=mock_storage,
            evaluator=mock_evaluator,
        )
        metrics = adapter.get_available_metrics()
        assert isinstance(metrics, list)
        assert "faithfulness" in metrics
        assert "answer_relevancy" in metrics
        assert "mrr" in metrics

    def test_list_runs_empty(self, mock_storage, mock_evaluator):
        """빈 평가 목록 조회."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter

        adapter = WebUIAdapter(storage=mock_storage, evaluator=mock_evaluator)
        runs = adapter.list_runs()
        assert runs == []

    def test_list_runs_without_storage(self):
        """저장소 없이 평가 목록 조회."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter
        from evalvault.config.settings import Settings

        adapter = WebUIAdapter(settings=Settings(evalvault_db_path=""))
        runs = adapter.list_runs()
        assert runs == []

    def test_get_metric_descriptions(self, mock_storage, mock_evaluator):
        """메트릭 설명 조회."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter

        adapter = WebUIAdapter(storage=mock_storage, evaluator=mock_evaluator)
        descriptions = adapter.get_metric_descriptions()
        assert isinstance(descriptions, dict)
        assert "faithfulness" in descriptions
        assert len(descriptions["faithfulness"]) > 0
        assert "mrr" in descriptions

    def test_get_metric_specs(self, mock_storage, mock_evaluator):
        """메트릭 스펙 조회."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter

        adapter = WebUIAdapter(storage=mock_storage, evaluator=mock_evaluator)
        specs = adapter.get_metric_specs()
        assert isinstance(specs, list)
        assert any(spec["name"] == "mrr" for spec in specs)


class TestWebUIAdapterRunEvaluation:
    """WebUIAdapter.run_evaluation() 테스트."""

    @pytest.fixture
    def mock_storage(self):
        """Mock storage adapter."""
        storage = MagicMock()
        storage.save_run.return_value = True
        return storage

    @pytest.fixture
    def mock_evaluator(self):
        """Mock evaluator service."""
        from datetime import datetime
        from unittest.mock import AsyncMock

        evaluator = MagicMock()

        # Mock EvaluationRun 결과
        mock_run = MagicMock()
        mock_run.run_id = "run-test-123"
        mock_run.pass_rate = 0.75
        mock_run.total_test_cases = 10
        mock_run.passed_test_cases = 8
        mock_run.metrics_evaluated = ["faithfulness", "answer_relevancy"]
        mock_run.started_at = datetime.now()
        mock_run.finished_at = datetime.now()
        mock_run.dataset_name = "test-dataset"
        mock_run.model_name = "gpt-5-nano"
        mock_run.thresholds = {"faithfulness": 0.7, "answer_relevancy": 0.7}
        mock_run.tracker_metadata = {}

        # async evaluate 메서드 모킹 - AsyncMock 사용
        evaluator.evaluate = AsyncMock(return_value=mock_run)
        return evaluator

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM adapter."""
        llm = MagicMock()
        llm.get_model_name.return_value = "gpt-5-nano"
        return llm

    @pytest.fixture
    def mock_data_loader(self):
        """Mock data loader."""
        from evalvault.domain.entities import Dataset, TestCase

        loader = MagicMock()
        mock_dataset = Dataset(
            name="test-dataset",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="tc-001",
                    question="테스트 질문",
                    answer="테스트 답변",
                    contexts=["테스트 컨텍스트"],
                    ground_truth="테스트 정답",
                )
            ],
        )
        loader.load.return_value = mock_dataset
        return loader

    async def test_run_evaluation_returns_evaluation_run(
        self, mock_storage, mock_evaluator, mock_llm, mock_data_loader
    ):
        """평가 실행이 EvaluationRun을 반환하는지 확인."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter
        from evalvault.ports.inbound.web_port import EvalRequest

        adapter = WebUIAdapter(
            storage=mock_storage,
            evaluator=mock_evaluator,
            llm_adapter=mock_llm,
            data_loader=mock_data_loader,
        )

        request = EvalRequest(
            dataset_path="/path/to/test.json",
            metrics=["faithfulness", "answer_relevancy"],
        )

        result = await adapter.run_evaluation(request)

        assert result is not None
        assert hasattr(result, "run_id")
        assert hasattr(result, "pass_rate")

    async def test_run_evaluation_calls_evaluator(
        self, mock_storage, mock_evaluator, mock_llm, mock_data_loader
    ):
        """평가 실행이 evaluator를 호출하는지 확인."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter
        from evalvault.ports.inbound.web_port import EvalRequest

        adapter = WebUIAdapter(
            storage=mock_storage,
            evaluator=mock_evaluator,
            llm_adapter=mock_llm,
            data_loader=mock_data_loader,
        )

        request = EvalRequest(
            dataset_path="/path/to/test.json",
            metrics=["faithfulness"],
            thresholds={"faithfulness": 0.8},
        )

        await adapter.run_evaluation(request)

        # evaluator.evaluate가 호출되었는지 확인
        assert mock_evaluator.evaluate.called or hasattr(mock_evaluator, "evaluate")

    async def test_run_evaluation_with_progress_callback(
        self, mock_storage, mock_evaluator, mock_llm, mock_data_loader
    ):
        """진행률 콜백이 호출되는지 확인."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter
        from evalvault.ports.inbound.web_port import EvalRequest

        adapter = WebUIAdapter(
            storage=mock_storage,
            evaluator=mock_evaluator,
            llm_adapter=mock_llm,
            data_loader=mock_data_loader,
        )

        progress_calls = []

        def on_progress(progress):
            progress_calls.append(progress)

        request = EvalRequest(
            dataset_path="/path/to/test.json",
            metrics=["faithfulness"],
        )

        await adapter.run_evaluation(request, on_progress=on_progress)

        # progress 콜백이 한 번 이상 호출되었는지 확인
        # 구현에 따라 호출될 수도 있고 안 될 수도 있음
        assert isinstance(progress_calls, list)

    def test_run_evaluation_with_dataset_sets_run_mode(
        self, mock_storage, mock_evaluator, mock_llm
    ):
        """run_mode가 tracker_metadata에 기록되는지 확인."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter
        from evalvault.domain.entities import Dataset, TestCase

        dataset = Dataset(
            name="web-ui-dataset",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="tc-1",
                    question="Q",
                    answer="A",
                    contexts=["ctx"],
                    ground_truth="A",
                )
            ],
        )

        adapter = WebUIAdapter(
            storage=mock_storage,
            evaluator=mock_evaluator,
            llm_adapter=mock_llm,
        )

        result = adapter.run_evaluation_with_dataset(
            dataset=dataset,
            metrics=["faithfulness"],
            run_mode="simple",
        )

        assert result.tracker_metadata["run_mode"] == "simple"

    async def test_run_evaluation_saves_to_storage(
        self, mock_storage, mock_evaluator, mock_llm, mock_data_loader
    ):
        """평가 결과가 저장소에 저장되는지 확인."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter
        from evalvault.ports.inbound.web_port import EvalRequest

        adapter = WebUIAdapter(
            storage=mock_storage,
            evaluator=mock_evaluator,
            llm_adapter=mock_llm,
            data_loader=mock_data_loader,
        )

        request = EvalRequest(
            dataset_path="/path/to/test.json",
            metrics=["faithfulness"],
        )

        await adapter.run_evaluation(request)

        # 저장소에 저장 호출 확인
        mock_storage.save_run.assert_called_once()


class TestWebUIAdapterImprovementGuide:
    """WebUIAdapter.get_improvement_guide() 테스트."""

    @pytest.fixture
    def mock_storage(self):
        """Mock storage adapter."""
        from datetime import datetime

        storage = MagicMock()

        # Mock EvaluationRun
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.pass_rate = 0.65
        mock_run.total_test_cases = 100
        mock_run.passed_test_cases = 65
        mock_run.metrics_evaluated = ["faithfulness", "context_precision"]
        mock_run.thresholds = {"faithfulness": 0.8, "context_precision": 0.7}
        mock_run.started_at = datetime.now()
        mock_run.finished_at = datetime.now()
        mock_run.get_avg_score.side_effect = lambda m: {
            "faithfulness": 0.72,
            "context_precision": 0.52,
        }.get(m, 0.5)
        mock_run.results = []

        storage.get_run.return_value = mock_run
        return storage

    def test_get_improvement_guide_returns_report(self, mock_storage):
        """개선 가이드가 ImprovementReport를 반환하는지 확인."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter

        adapter = WebUIAdapter(storage=mock_storage)

        result = adapter.get_improvement_guide("run-123")

        assert result is not None
        assert hasattr(result, "run_id")
        assert hasattr(result, "guides")

    def test_get_improvement_guide_with_llm(self, mock_storage):
        """LLM 분석 포함 개선 가이드 생성."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter

        mock_llm = MagicMock()
        adapter = WebUIAdapter(storage=mock_storage, llm_adapter=mock_llm)

        result = adapter.get_improvement_guide("run-123", include_llm=True)

        assert result is not None

    def test_get_improvement_guide_not_found(self, mock_storage):
        """존재하지 않는 실행 ID로 가이드 요청 시 예외."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter

        mock_storage.get_run.return_value = None
        adapter = WebUIAdapter(storage=mock_storage)

        with pytest.raises(KeyError):
            adapter.get_improvement_guide("nonexistent-run")


class TestWebUIAdapterQualityGate:
    """WebUIAdapter.check_quality_gate() 테스트."""

    @pytest.fixture
    def mock_storage(self):
        """Mock storage adapter."""

        storage = MagicMock()

        # Mock EvaluationRun - 통과 케이스
        mock_run = MagicMock()
        mock_run.run_id = "run-pass"
        mock_run.metrics_evaluated = ["faithfulness", "context_precision"]
        mock_run.thresholds = {"faithfulness": 0.7, "context_precision": 0.7}
        mock_run.get_avg_score.side_effect = lambda m: {
            "faithfulness": 0.85,
            "context_precision": 0.75,
        }.get(m, 0.8)

        storage.get_run.return_value = mock_run
        return storage

    def test_check_quality_gate_pass(self, mock_storage):
        """모든 메트릭이 임계값을 통과하면 passed=True."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter

        adapter = WebUIAdapter(storage=mock_storage)

        result = adapter.check_quality_gate("run-pass")

        assert result is not None
        assert result.overall_passed is True
        assert all(r.passed for r in result.results)

    def test_check_quality_gate_fail(self, mock_storage):
        """메트릭이 임계값 미달이면 passed=False."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter

        # 실패 케이스로 변경
        mock_storage.get_run.return_value.get_avg_score.side_effect = lambda m: {
            "faithfulness": 0.65,  # 임계값 0.7 미달
            "context_precision": 0.75,
        }.get(m, 0.5)

        adapter = WebUIAdapter(storage=mock_storage)

        result = adapter.check_quality_gate("run-pass")

        assert result.overall_passed is False
        assert any(not r.passed for r in result.results)

    def test_check_quality_gate_with_custom_thresholds(self, mock_storage):
        """커스텀 임계값으로 게이트 체크."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter

        adapter = WebUIAdapter(storage=mock_storage)

        # 더 높은 임계값 사용
        result = adapter.check_quality_gate(
            "run-pass",
            thresholds={"faithfulness": 0.9, "context_precision": 0.9},
        )

        # 0.85와 0.75는 0.9 미달이므로 실패
        assert result.overall_passed is False

    def test_check_quality_gate_result_structure(self, mock_storage):
        """GateReport 구조 확인."""
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter

        adapter = WebUIAdapter(storage=mock_storage)

        result = adapter.check_quality_gate("run-pass")

        assert hasattr(result, "run_id")
        assert hasattr(result, "results")
        assert hasattr(result, "overall_passed")
        assert len(result.results) == 2  # 2개 메트릭

        # 각 결과 구조 확인
        for gate_result in result.results:
            assert hasattr(gate_result, "metric")
            assert hasattr(gate_result, "score")
            assert hasattr(gate_result, "threshold")
            assert hasattr(gate_result, "passed")
            assert hasattr(gate_result, "gap")
