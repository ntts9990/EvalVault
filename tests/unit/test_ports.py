"""Port 인터페이스 정의 확인 테스트."""

from typing import Protocol, get_type_hints

from evalvault.domain.entities import Dataset, EvaluationRun
from evalvault.ports.inbound.evaluator_port import EvaluatorPort
from evalvault.ports.outbound.dataset_port import DatasetPort
from evalvault.ports.outbound.llm_port import LLMPort
from evalvault.ports.outbound.storage_port import StoragePort
from evalvault.ports.outbound.tracker_port import TrackerPort


class TestLLMPort:
    """LLM Port 인터페이스 테스트."""

    def test_is_abc(self):
        """LLMPort가 ABC로 정의되어 있는지 확인."""
        from abc import ABC

        assert issubclass(LLMPort, ABC)

    def test_has_get_model_name_method(self):
        """get_model_name 메서드가 정의되어 있는지 확인."""
        assert hasattr(LLMPort, "get_model_name")

    def test_has_as_ragas_llm_method(self):
        """as_ragas_llm 메서드가 정의되어 있는지 확인."""
        assert hasattr(LLMPort, "as_ragas_llm")


class TestDatasetPort:
    """Dataset Port 인터페이스 테스트."""

    def test_is_protocol(self):
        """DatasetPort가 Protocol로 정의되어 있는지 확인."""
        assert issubclass(DatasetPort, Protocol)

    def test_has_load_method(self):
        """load 메서드가 정의되어 있는지 확인."""
        assert hasattr(DatasetPort, "load")
        method = DatasetPort.load
        assert callable(method)

    def test_load_returns_dataset(self):
        """load 메서드가 Dataset을 반환하는지 타입 힌트 확인."""
        hints = get_type_hints(DatasetPort.load)
        assert "return" in hints
        # Dataset 반환 타입 확인
        assert hints["return"] == Dataset

    def test_has_supports_method(self):
        """supports 메서드가 정의되어 있는지 확인."""
        assert hasattr(DatasetPort, "supports")
        method = DatasetPort.supports
        assert callable(method)

    def test_supports_returns_bool(self):
        """supports 메서드가 bool을 반환하는지 타입 힌트 확인."""
        hints = get_type_hints(DatasetPort.supports)
        assert "return" in hints
        assert hints["return"] is bool


class TestStoragePort:
    """Storage Port 인터페이스 테스트."""

    def test_is_protocol(self):
        """StoragePort가 Protocol로 정의되어 있는지 확인."""
        assert issubclass(StoragePort, Protocol)

    def test_has_save_run_method(self):
        """save_run 메서드가 정의되어 있는지 확인."""
        assert hasattr(StoragePort, "save_run")
        method = StoragePort.save_run
        assert callable(method)

    def test_save_run_returns_str(self):
        """save_run 메서드가 str을 반환하는지 타입 힌트 확인."""
        hints = get_type_hints(StoragePort.save_run)
        assert "return" in hints
        assert hints["return"] is str

    def test_has_get_run_method(self):
        """get_run 메서드가 정의되어 있는지 확인."""
        assert hasattr(StoragePort, "get_run")
        method = StoragePort.get_run
        assert callable(method)

    def test_get_run_returns_evaluation_run(self):
        """get_run 메서드가 EvaluationRun을 반환하는지 타입 힌트 확인."""
        hints = get_type_hints(StoragePort.get_run)
        assert "return" in hints
        assert hints["return"] == EvaluationRun

    def test_has_list_runs_method(self):
        """list_runs 메서드가 정의되어 있는지 확인."""
        assert hasattr(StoragePort, "list_runs")
        method = StoragePort.list_runs
        assert callable(method)

    def test_has_cluster_map_methods(self):
        """클러스터 맵 관련 메서드가 정의되어 있는지 확인."""
        assert hasattr(StoragePort, "save_run_cluster_map")
        assert hasattr(StoragePort, "get_run_cluster_map")
        assert hasattr(StoragePort, "list_run_cluster_maps")
        assert hasattr(StoragePort, "delete_run_cluster_map")

        assert callable(StoragePort.save_run_cluster_map)
        assert callable(StoragePort.get_run_cluster_map)
        assert callable(StoragePort.list_run_cluster_maps)
        assert callable(StoragePort.delete_run_cluster_map)

    def test_cluster_map_method_hints(self):
        """클러스터 맵 메서드 반환 타입 힌트 확인."""
        hints = get_type_hints(StoragePort.save_run_cluster_map)
        assert hints.get("return") is str

        hints = get_type_hints(StoragePort.get_run_cluster_map)
        assert "return" in hints

        hints = get_type_hints(StoragePort.list_run_cluster_maps)
        assert "return" in hints

        hints = get_type_hints(StoragePort.delete_run_cluster_map)
        assert hints.get("return") is int


class TestTrackerPort:
    """Tracker Port 인터페이스 테스트."""

    def test_is_protocol(self):
        """TrackerPort가 Protocol로 정의되어 있는지 확인."""
        assert issubclass(TrackerPort, Protocol)

    def test_has_start_trace_method(self):
        """start_trace 메서드가 정의되어 있는지 확인."""
        assert hasattr(TrackerPort, "start_trace")
        method = TrackerPort.start_trace
        assert callable(method)

    def test_start_trace_returns_str(self):
        """start_trace 메서드가 str을 반환하는지 타입 힌트 확인."""
        hints = get_type_hints(TrackerPort.start_trace)
        assert "return" in hints
        assert hints["return"] is str

    def test_has_log_score_method(self):
        """log_score 메서드가 정의되어 있는지 확인."""
        assert hasattr(TrackerPort, "log_score")
        method = TrackerPort.log_score
        assert callable(method)

    def test_has_save_artifact_method(self):
        """save_artifact 메서드가 정의되어 있는지 확인."""
        assert hasattr(TrackerPort, "save_artifact")
        method = TrackerPort.save_artifact
        assert callable(method)

    def test_has_end_trace_method(self):
        """end_trace 메서드가 정의되어 있는지 확인."""
        assert hasattr(TrackerPort, "end_trace")
        method = TrackerPort.end_trace
        assert callable(method)


class TestEvaluatorPort:
    """Evaluator Port 인터페이스 테스트."""

    def test_is_protocol(self):
        """EvaluatorPort가 Protocol로 정의되어 있는지 확인."""
        assert issubclass(EvaluatorPort, Protocol)

    def test_has_evaluate_method(self):
        """evaluate 메서드가 정의되어 있는지 확인."""
        assert hasattr(EvaluatorPort, "evaluate")
        method = EvaluatorPort.evaluate
        assert callable(method)

    def test_evaluate_returns_evaluation_run(self):
        """evaluate 메서드가 EvaluationRun을 반환하는지 타입 힌트 확인."""
        hints = get_type_hints(EvaluatorPort.evaluate)
        assert "return" in hints
        assert hints["return"] == EvaluationRun
