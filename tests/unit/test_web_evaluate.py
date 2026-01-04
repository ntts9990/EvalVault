"""Unit tests for Web UI Evaluate page components."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from tests.optional_deps import skip_if_missing_web

if TYPE_CHECKING:
    pass

skip_if_missing_web()


class TestFileUploadHandler:
    """FileUploadHandler 컴포넌트 테스트."""

    def test_handler_can_be_imported(self):
        """핸들러 임포트 확인."""
        from evalvault.adapters.inbound.web.components.upload import FileUploadHandler

        assert FileUploadHandler is not None

    def test_validate_csv_file(self):
        """CSV 파일 검증."""
        from evalvault.adapters.inbound.web.components.upload import FileUploadHandler

        handler = FileUploadHandler()

        csv_content = b"id,question,answer,contexts,ground_truth\n1,Q1,A1,[],GT1"
        result = handler.validate_file("test.csv", csv_content)

        assert result.is_valid is True
        assert result.file_type == "csv"
        assert result.row_count >= 1

    def test_validate_json_file(self):
        """JSON 파일 검증."""
        from evalvault.adapters.inbound.web.components.upload import FileUploadHandler

        handler = FileUploadHandler()

        json_data = {
            "name": "test-dataset",
            "test_cases": [
                {
                    "id": "tc-1",
                    "question": "Q1",
                    "answer": "A1",
                    "contexts": [],
                    "ground_truth": "GT1",
                }
            ],
        }
        json_content = json.dumps(json_data).encode("utf-8")
        result = handler.validate_file("test.json", json_content)

        assert result.is_valid is True
        assert result.file_type == "json"
        assert result.row_count == 1
        assert result.dataset_name == "test-dataset"

    def test_validate_invalid_file_type(self):
        """잘못된 파일 타입 검증."""
        from evalvault.adapters.inbound.web.components.upload import FileUploadHandler

        handler = FileUploadHandler()

        result = handler.validate_file("test.txt", b"some content")

        assert result.is_valid is False
        assert "Unsupported file type" in result.error_message

    def test_validate_empty_csv(self):
        """빈 CSV 파일 검증."""
        from evalvault.adapters.inbound.web.components.upload import FileUploadHandler

        handler = FileUploadHandler()

        csv_content = b"id,question,answer,contexts,ground_truth"  # 헤더만
        result = handler.validate_file("test.csv", csv_content)

        assert result.is_valid is False
        assert "empty" in result.error_message.lower()

    def test_validate_csv_missing_columns(self):
        """필수 컬럼 누락 CSV 검증."""
        from evalvault.adapters.inbound.web.components.upload import FileUploadHandler

        handler = FileUploadHandler()

        csv_content = b"id,question\n1,Q1"  # answer, contexts 누락
        result = handler.validate_file("test.csv", csv_content)

        assert result.is_valid is False
        assert "missing" in result.error_message.lower()

    def test_parse_csv_to_test_cases(self):
        """CSV를 TestCase로 파싱."""
        from evalvault.adapters.inbound.web.components.upload import FileUploadHandler

        handler = FileUploadHandler()

        csv_content = (
            b"id,question,answer,contexts,ground_truth\n"
            b'1,"What is RAG?","RAG is...","[""context1""]","Answer about RAG"'
        )

        test_cases = handler.parse_to_test_cases("test.csv", csv_content)

        assert len(test_cases) == 1
        assert test_cases[0]["question"] == "What is RAG?"

    def test_parse_json_to_test_cases(self):
        """JSON을 TestCase로 파싱."""
        from evalvault.adapters.inbound.web.components.upload import FileUploadHandler

        handler = FileUploadHandler()

        json_data = {
            "name": "test",
            "test_cases": [
                {
                    "id": "tc-1",
                    "question": "What is RAG?",
                    "answer": "RAG is...",
                    "contexts": ["context1"],
                    "ground_truth": "Answer about RAG",
                }
            ],
        }
        json_content = json.dumps(json_data).encode("utf-8")

        test_cases = handler.parse_to_test_cases("test.json", json_content)

        assert len(test_cases) == 1
        assert test_cases[0]["question"] == "What is RAG?"


class TestValidationResult:
    """ValidationResult 데이터 클래스 테스트."""

    def test_create_valid_result(self):
        """유효한 결과 생성."""
        from evalvault.adapters.inbound.web.components.upload import ValidationResult

        result = ValidationResult(
            is_valid=True,
            file_type="csv",
            row_count=10,
            columns=["id", "question", "answer"],
        )

        assert result.is_valid is True
        assert result.error_message is None

    def test_create_invalid_result(self):
        """무효한 결과 생성."""
        from evalvault.adapters.inbound.web.components.upload import ValidationResult

        result = ValidationResult(
            is_valid=False,
            error_message="File is empty",
        )

        assert result.is_valid is False
        assert result.error_message == "File is empty"


class TestMetricSelector:
    """MetricSelector 컴포넌트 테스트."""

    def test_selector_can_be_imported(self):
        """선택기 임포트 확인."""
        from evalvault.adapters.inbound.web.components.metrics import MetricSelector

        assert MetricSelector is not None

    def test_get_available_metrics(self):
        """사용 가능한 메트릭 목록."""
        from evalvault.adapters.inbound.web.components.metrics import MetricSelector

        selector = MetricSelector()
        metrics = selector.get_available_metrics()

        assert "faithfulness" in metrics
        assert "answer_relevancy" in metrics

    def test_get_metric_description(self):
        """메트릭 설명 조회."""
        from evalvault.adapters.inbound.web.components.metrics import MetricSelector

        selector = MetricSelector()
        desc = selector.get_description("faithfulness")

        assert desc is not None
        assert len(desc) > 0

    def test_get_default_metrics(self):
        """기본 메트릭 목록."""
        from evalvault.adapters.inbound.web.components.metrics import MetricSelector

        selector = MetricSelector()
        defaults = selector.get_default_metrics()

        assert "faithfulness" in defaults
        assert "answer_relevancy" in defaults

    def test_validate_metric_selection(self):
        """메트릭 선택 검증."""
        from evalvault.adapters.inbound.web.components.metrics import MetricSelector

        selector = MetricSelector()

        # 유효한 선택
        assert selector.validate_selection(["faithfulness"]) is True

        # 빈 선택
        assert selector.validate_selection([]) is False

        # 잘못된 메트릭
        assert selector.validate_selection(["invalid_metric"]) is False

    def test_get_metric_icon(self):
        """메트릭 아이콘 조회."""
        from evalvault.adapters.inbound.web.components.metrics import MetricSelector

        selector = MetricSelector()
        icon = selector.get_icon("faithfulness")

        assert icon is not None


class TestEvaluationProgress:
    """EvaluationProgress 컴포넌트 테스트."""

    def test_progress_can_be_imported(self):
        """진행률 컴포넌트 임포트 확인."""
        from evalvault.adapters.inbound.web.components.progress import (
            EvaluationProgress,
        )

        assert EvaluationProgress is not None

    def test_create_initial_progress(self):
        """초기 진행률 생성."""
        from evalvault.adapters.inbound.web.components.progress import (
            EvaluationProgress,
        )

        progress = EvaluationProgress(
            total_steps=10,
            current_step=0,
            current_metric=None,
        )

        assert progress.percent == 0.0
        assert progress.is_complete is False

    def test_update_progress(self):
        """진행률 업데이트."""
        from evalvault.adapters.inbound.web.components.progress import (
            EvaluationProgress,
        )

        progress = EvaluationProgress(
            total_steps=10,
            current_step=0,
            current_metric=None,
        )

        progress.update(step=5, metric="faithfulness")

        assert progress.current_step == 5
        assert progress.current_metric == "faithfulness"
        assert progress.percent == 50.0

    def test_complete_progress(self):
        """완료 상태."""
        from evalvault.adapters.inbound.web.components.progress import (
            EvaluationProgress,
        )

        progress = EvaluationProgress(
            total_steps=10,
            current_step=10,
            current_metric="complete",
        )

        assert progress.is_complete is True
        assert progress.percent == 100.0

    def test_progress_status_message(self):
        """상태 메시지."""
        from evalvault.adapters.inbound.web.components.progress import (
            EvaluationProgress,
        )

        progress = EvaluationProgress(
            total_steps=10,
            current_step=5,
            current_metric="faithfulness",
        )

        message = progress.get_status_message()

        assert "faithfulness" in message
        assert "5" in message or "50" in message

    def test_progress_with_error(self):
        """에러 상태."""
        from evalvault.adapters.inbound.web.components.progress import (
            EvaluationProgress,
        )

        progress = EvaluationProgress(
            total_steps=10,
            current_step=3,
            current_metric="faithfulness",
            error="API rate limit exceeded",
        )

        assert progress.has_error is True
        assert progress.error == "API rate limit exceeded"


class TestEvaluationConfig:
    """EvaluationConfig 테스트."""

    def test_config_can_be_imported(self):
        """설정 클래스 임포트 확인."""
        from evalvault.adapters.inbound.web.components.evaluate import EvaluationConfig

        assert EvaluationConfig is not None

    def test_create_config(self):
        """설정 생성."""
        from evalvault.adapters.inbound.web.components.evaluate import EvaluationConfig

        config = EvaluationConfig(
            dataset_path="/path/to/dataset.json",
            metrics=["faithfulness", "answer_relevancy"],
            model_name="gpt-5-nano",
            langfuse_enabled=True,
        )

        assert config.dataset_path == "/path/to/dataset.json"
        assert len(config.metrics) == 2
        assert config.langfuse_enabled is True

    def test_config_validation(self):
        """설정 검증."""
        from evalvault.adapters.inbound.web.components.evaluate import EvaluationConfig

        # 유효한 설정
        config = EvaluationConfig(
            dataset_path="/path/to/dataset.json",
            metrics=["faithfulness"],
            model_name="gpt-5-nano",
        )
        assert config.is_valid() is True

        # 빈 메트릭
        config_empty = EvaluationConfig(
            dataset_path="/path/to/dataset.json",
            metrics=[],
            model_name="gpt-5-nano",
        )
        assert config_empty.is_valid() is False

    def test_config_to_eval_request(self):
        """EvalRequest로 변환."""
        from evalvault.adapters.inbound.web.components.evaluate import EvaluationConfig
        from evalvault.ports.inbound.web_port import EvalRequest

        config = EvaluationConfig(
            dataset_path="/path/to/dataset.json",
            metrics=["faithfulness"],
            model_name="gpt-4",
            langfuse_enabled=True,
            thresholds={"faithfulness": 0.8},
        )

        request = config.to_eval_request()

        assert isinstance(request, EvalRequest)
        assert request.dataset_path == "/path/to/dataset.json"
        assert request.model_name == "gpt-4"
        assert request.langfuse_enabled is True
