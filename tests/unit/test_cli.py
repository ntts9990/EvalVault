"""Tests for CLI interface."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.error import HTTPError

import pytest
from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app
from evalvault.domain.entities import (
    Dataset,
    EvaluationRun,
    MetricScore,
    TestCase,
    TestCaseResult,
)
from tests.unit.conftest import get_test_model

runner = CliRunner()


class TestCLIVersion:
    """CLI 버전 명령 테스트."""

    def test_version_command(self):
        """--version 플래그 테스트."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout


class TestCLIRun:
    """CLI run 명령 테스트."""

    @pytest.fixture
    def mock_dataset(self):
        """테스트용 데이터셋."""
        return Dataset(
            name="test-dataset",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="tc-001",
                    question="What is Python?",
                    answer="Python is a programming language.",
                    contexts=["Python is a high-level language."],
                    ground_truth="A programming language",
                ),
            ],
        )

    @pytest.fixture
    def mock_evaluation_run(self):
        """테스트용 평가 결과."""
        from datetime import datetime, timedelta

        start = datetime.now()
        end = start + timedelta(seconds=10)

        return EvaluationRun(
            dataset_name="test-dataset",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=end,
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

    def test_run_help(self):
        """run 명령 help 테스트."""
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "dataset" in result.stdout.lower()
        assert "metrics" in result.stdout.lower()

    def test_run_missing_dataset(self):
        """데이터셋 파일 누락 시 에러."""
        result = runner.invoke(app, ["run", "nonexistent.csv"])
        assert result.exit_code != 0

    @patch("evalvault.adapters.inbound.cli.get_loader")
    @patch("evalvault.adapters.inbound.cli.RagasEvaluator")
    @patch("evalvault.adapters.inbound.cli.get_llm_adapter")
    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_run_with_valid_dataset(
        self,
        mock_settings_cls,
        mock_get_llm_adapter,
        mock_evaluator_cls,
        mock_get_loader,
        mock_dataset,
        mock_evaluation_run,
        tmp_path,
    ):
        """유효한 데이터셋으로 run 명령 테스트."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = get_test_model()
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings_cls.return_value = mock_settings

        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_dataset
        mock_get_loader.return_value = mock_loader

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_evaluation_run)
        mock_evaluator_cls.return_value = mock_evaluator

        mock_llm = MagicMock()
        mock_get_llm_adapter.return_value = mock_llm

        # Create test file
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")

        # Run command
        result = runner.invoke(app, ["run", str(test_file), "--metrics", "faithfulness"])

        # Assert
        assert result.exit_code == 0
        assert "test-dataset" in result.stdout or "faithfulness" in result.stdout

    @patch("evalvault.adapters.inbound.cli.get_loader")
    @patch("evalvault.adapters.inbound.cli.RagasEvaluator")
    @patch("evalvault.adapters.inbound.cli.get_llm_adapter")
    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_run_with_multiple_metrics(
        self,
        mock_settings_cls,
        mock_get_llm_adapter,
        mock_evaluator_cls,
        mock_get_loader,
        tmp_path,
    ):
        """여러 메트릭으로 run 명령 테스트."""
        from datetime import datetime, timedelta

        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = get_test_model()
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings_cls.return_value = mock_settings

        mock_dataset = Dataset(
            name="test",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="tc-001",
                    question="Q1",
                    answer="A1",
                    contexts=["C1"],
                ),
            ],
        )

        start = datetime.now()
        end = start + timedelta(seconds=5)
        mock_run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness", "answer_relevancy"],
            started_at=start,
            finished_at=end,
            thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[
                        MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.85, threshold=0.7),
                    ],
                ),
            ],
        )

        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_dataset
        mock_get_loader.return_value = mock_loader

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_run)
        mock_evaluator_cls.return_value = mock_evaluator

        mock_llm = MagicMock()
        mock_get_llm_adapter.return_value = mock_llm

        # Create test file
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")

        # Run command with multiple metrics
        result = runner.invoke(
            app,
            ["run", str(test_file), "--metrics", "faithfulness,answer_relevancy"],
        )

        assert result.exit_code == 0


class TestCLIMetrics:
    """CLI metrics 명령 테스트."""

    def test_metrics_list(self):
        """metrics 명령으로 사용 가능한 메트릭 목록 출력."""
        result = runner.invoke(app, ["metrics"])
        assert result.exit_code == 0
        assert "faithfulness" in result.stdout.lower()
        assert "answer_relevancy" in result.stdout.lower()
        assert "context_precision" in result.stdout.lower()
        assert "context_recall" in result.stdout.lower()


class TestKGCLI:
    """CLI kg stats 명령 테스트."""

    def test_kg_stats_help(self):
        """kg stats help 출력."""
        result = runner.invoke(app, ["kg", "stats", "--help"])
        assert result.exit_code == 0
        assert "threshold" in result.stdout.lower()

    def test_kg_stats_runs_on_text_file(self, tmp_path):
        """간단한 텍스트 파일로 kg stats 실행."""
        sample_file = tmp_path / "doc.txt"
        sample_file.write_text("삼성생명의 종신보험은 사망보험금을 보장합니다.", encoding="utf-8")

        result = runner.invoke(app, ["kg", "stats", str(sample_file), "--no-langfuse"])

        assert result.exit_code == 0
        assert "Knowledge Graph Overview" in result.stdout

    @patch("evalvault.adapters.inbound.cli.LangfuseAdapter")
    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_kg_stats_logs_to_langfuse(self, mock_settings_cls, mock_langfuse, tmp_path):
        """Langfuse 설정이 있으면 자동으로 로깅된다."""
        sample_file = tmp_path / "doc.txt"
        sample_file.write_text("삼성생명의 종신보험은 사망보험금을 보장합니다.", encoding="utf-8")

        mock_settings = MagicMock()
        mock_settings.langfuse_public_key = "pub"
        mock_settings.langfuse_secret_key = "sec"
        mock_settings.langfuse_host = "https://example"
        mock_settings.evalvault_profile = None
        mock_settings.llm_provider = "openai"
        mock_settings.openai_api_key = "key"
        mock_settings_cls.return_value = mock_settings

        mock_tracker = MagicMock()
        mock_tracker.start_trace.return_value = "trace-123"
        mock_langfuse.return_value = mock_tracker

        result = runner.invoke(app, ["kg", "stats", str(sample_file)])

        assert result.exit_code == 0
        mock_langfuse.assert_called_once()
        mock_tracker.start_trace.assert_called_once()
        mock_tracker.save_artifact.assert_called_once()
        args, kwargs = mock_tracker.save_artifact.call_args
        artifact_payload = kwargs.get("data") or (args[2] if len(args) >= 3 else None)
        assert artifact_payload["type"] == "kg_stats"
        assert "Langfuse trace ID" in result.stdout

    def test_kg_stats_report_file(self, tmp_path):
        """--report-file 옵션으로 JSON 저장."""
        sample_file = tmp_path / "doc.txt"
        sample_file.write_text("삼성생명의 종신보험은 사망보험금을 보장합니다.", encoding="utf-8")
        report = tmp_path / "report.json"

        result = runner.invoke(
            app,
            ["kg", "stats", str(sample_file), "--no-langfuse", "--report-file", str(report)],
        )

        assert result.exit_code == 0
        data = json.loads(report.read_text(encoding="utf-8"))
        assert data["type"] == "kg_stats_report"


class TestCLIConfig:
    """CLI config 명령 테스트."""

    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_config_show(self, mock_settings_cls):
        """config 명령으로 현재 설정 출력."""
        test_model = get_test_model()
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = test_model
        mock_settings.openai_embedding_model = "text-embedding-3-small"
        mock_settings.openai_base_url = None
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None  # No profile set
        mock_settings.langfuse_public_key = None
        mock_settings.langfuse_secret_key = None
        mock_settings.langfuse_host = "https://cloud.langfuse.com"
        mock_settings_cls.return_value = mock_settings

        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        # Check for configuration related text
        assert "Configuration" in result.stdout


class TestLangfuseDashboard:
    """Langfuse dashboard 명령 테스트."""

    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_dashboard_requires_credentials(self, mock_settings_cls):
        mock_settings = MagicMock()
        mock_settings.langfuse_public_key = None
        mock_settings.langfuse_secret_key = None
        mock_settings_cls.return_value = mock_settings

        result = runner.invoke(app, ["langfuse-dashboard"])
        assert result.exit_code != 0
        assert "credentials" in result.stdout.lower()

    @patch("evalvault.adapters.inbound.cli._fetch_langfuse_traces")
    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_dashboard_outputs_table(self, mock_settings_cls, mock_fetch):
        mock_settings = MagicMock()
        mock_settings.langfuse_public_key = "pub"
        mock_settings.langfuse_secret_key = "sec"
        mock_settings.langfuse_host = "https://example"
        mock_settings_cls.return_value = mock_settings
        mock_fetch.return_value = [
            {
                "id": "trace-1",
                "metadata": {
                    "dataset_name": "test",
                    "model_name": "gpt",
                    "pass_rate": 0.9,
                    "total_test_cases": 10,
                },
                "createdAt": "2024-06-01T00:00:00Z",
            }
        ]

        result = runner.invoke(app, ["langfuse-dashboard"])
        assert result.exit_code == 0
        assert "trace-1" in result.stdout
        mock_fetch.assert_called_once()

    @patch("evalvault.adapters.inbound.cli._fetch_langfuse_traces")
    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_dashboard_handles_http_error(self, mock_settings_cls, mock_fetch):
        mock_settings = MagicMock()
        mock_settings.langfuse_public_key = "pub"
        mock_settings.langfuse_secret_key = "sec"
        mock_settings.langfuse_host = "https://example"
        mock_settings_cls.return_value = mock_settings

        mock_fetch.side_effect = HTTPError(
            url="https://example/api/public/traces",
            code=405,
            msg="Method Not Allowed",
            hdrs=None,
            fp=None,
        )

        result = runner.invoke(app, ["langfuse-dashboard"])

        assert result.exit_code == 0
        assert "public API not available" in result.stdout
