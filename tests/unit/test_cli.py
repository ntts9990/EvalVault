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

    @patch("evalvault.adapters.inbound.cli._fetch_langfuse_traces")
    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_dashboard_no_traces_found(self, mock_settings_cls, mock_fetch):
        """No traces found 메시지 테스트."""
        mock_settings = MagicMock()
        mock_settings.langfuse_public_key = "pub"
        mock_settings.langfuse_secret_key = "sec"
        mock_settings.langfuse_host = "https://example"
        mock_settings_cls.return_value = mock_settings
        mock_fetch.return_value = []

        result = runner.invoke(app, ["langfuse-dashboard"])
        assert result.exit_code == 0
        assert "No traces found" in result.stdout


class TestCLIRunEdgeCases:
    """CLI run 명령 엣지 케이스 테스트."""

    def test_run_invalid_metrics(self, tmp_path):
        """잘못된 메트릭 이름 사용 시 에러."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")

        result = runner.invoke(
            app, ["run", str(test_file), "--metrics", "invalid_metric,faithfulness"]
        )
        assert result.exit_code == 1
        assert "Invalid metrics" in result.stdout

    @patch("evalvault.adapters.inbound.cli.get_loader")
    @patch("evalvault.adapters.inbound.cli.RagasEvaluator")
    @patch("evalvault.adapters.inbound.cli.get_llm_adapter")
    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_run_with_profile(
        self, mock_settings_cls, mock_get_llm, mock_evaluator_cls, mock_get_loader, tmp_path
    ):
        """프로필 옵션 테스트."""
        from datetime import datetime, timedelta

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
                TestCase(id="tc-001", question="Q", answer="A", contexts=["C"]),
            ],
        )
        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        mock_run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=start + timedelta(seconds=1),
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
            ],
        )
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_run)
        mock_evaluator_cls.return_value = mock_evaluator

        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")

        with patch("evalvault.adapters.inbound.cli.apply_profile") as mock_apply:
            mock_apply.return_value = mock_settings
            result = runner.invoke(
                app, ["run", str(test_file), "--profile", "prod", "--metrics", "faithfulness"]
            )

        assert result.exit_code == 0
        assert "prod" in result.stdout

    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_run_missing_openai_key(self, mock_settings_cls, tmp_path):
        """OpenAI API 키 누락 시 에러."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = None
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings_cls.return_value = mock_settings

        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")

        result = runner.invoke(app, ["run", str(test_file), "--metrics", "faithfulness"])
        assert result.exit_code == 1
        assert "OPENAI_API_KEY" in result.stdout

    @patch("evalvault.adapters.inbound.cli.get_loader")
    @patch("evalvault.adapters.inbound.cli.RagasEvaluator")
    @patch("evalvault.adapters.inbound.cli.get_llm_adapter")
    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_run_with_ollama_provider(
        self, mock_settings_cls, mock_get_llm, mock_evaluator_cls, mock_get_loader, tmp_path
    ):
        """Ollama 프로바이더 테스트."""
        from datetime import datetime, timedelta

        mock_settings = MagicMock()
        mock_settings.openai_api_key = None
        mock_settings.ollama_model = "llama2"
        mock_settings.llm_provider = "ollama"
        mock_settings.evalvault_profile = None
        mock_settings_cls.return_value = mock_settings

        mock_dataset = Dataset(
            name="test",
            version="1.0.0",
            test_cases=[
                TestCase(id="tc-001", question="Q", answer="A", contexts=["C"]),
            ],
        )
        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        mock_run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0.0",
            model_name="ollama/llama2",
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=start + timedelta(seconds=1),
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
            ],
        )
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_run)
        mock_evaluator_cls.return_value = mock_evaluator

        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")

        result = runner.invoke(app, ["run", str(test_file), "--metrics", "faithfulness"])
        assert result.exit_code == 0
        assert "ollama" in result.stdout.lower()

    @patch("evalvault.adapters.inbound.cli.get_loader")
    @patch("evalvault.adapters.inbound.cli.RagasEvaluator")
    @patch("evalvault.adapters.inbound.cli.get_llm_adapter")
    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_run_with_verbose_output(
        self, mock_settings_cls, mock_get_llm, mock_evaluator_cls, mock_get_loader, tmp_path
    ):
        """Verbose 모드 테스트."""
        from datetime import datetime, timedelta

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
                TestCase(id="tc-001", question="Q", answer="A", contexts=["C"]),
            ],
        )
        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        mock_run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=start + timedelta(seconds=1),
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
            ],
        )
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_run)
        mock_evaluator_cls.return_value = mock_evaluator

        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")

        result = runner.invoke(
            app, ["run", str(test_file), "--metrics", "faithfulness", "--verbose"]
        )
        assert result.exit_code == 0
        assert "tc-001" in result.stdout

    @patch("evalvault.adapters.inbound.cli.get_loader")
    @patch("evalvault.adapters.inbound.cli.RagasEvaluator")
    @patch("evalvault.adapters.inbound.cli.get_llm_adapter")
    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_run_with_output_file(
        self, mock_settings_cls, mock_get_llm, mock_evaluator_cls, mock_get_loader, tmp_path
    ):
        """결과 파일 저장 테스트."""
        from datetime import datetime, timedelta

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
                TestCase(id="tc-001", question="Q", answer="A", contexts=["C"]),
            ],
        )
        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        mock_run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=start + timedelta(seconds=1),
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
            ],
        )
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_run)
        mock_evaluator_cls.return_value = mock_evaluator

        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")
        output_file = tmp_path / "results.json"

        result = runner.invoke(
            app,
            ["run", str(test_file), "--metrics", "faithfulness", "--output", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        data = json.loads(output_file.read_text(encoding="utf-8"))
        assert "results" in data

    @patch("evalvault.adapters.inbound.cli.get_loader")
    @patch("evalvault.adapters.inbound.cli.RagasEvaluator")
    @patch("evalvault.adapters.inbound.cli.get_llm_adapter")
    @patch("evalvault.adapters.inbound.cli.Settings")
    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    def test_run_with_db_save(
        self,
        mock_storage_cls,
        mock_settings_cls,
        mock_get_llm,
        mock_evaluator_cls,
        mock_get_loader,
        tmp_path,
    ):
        """DB 저장 테스트."""
        from datetime import datetime, timedelta

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
                TestCase(id="tc-001", question="Q", answer="A", contexts=["C"]),
            ],
        )
        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        mock_run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=start + timedelta(seconds=1),
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
            ],
        )
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_run)
        mock_evaluator_cls.return_value = mock_evaluator

        mock_storage = MagicMock()
        mock_storage_cls.return_value = mock_storage

        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")
        db_file = tmp_path / "test.db"

        result = runner.invoke(
            app,
            ["run", str(test_file), "--metrics", "faithfulness", "--db", str(db_file)],
        )
        assert result.exit_code == 0
        mock_storage.save_run.assert_called_once()

    @patch("evalvault.adapters.inbound.cli.get_loader")
    @patch("evalvault.adapters.inbound.cli.RagasEvaluator")
    @patch("evalvault.adapters.inbound.cli.get_llm_adapter")
    @patch("evalvault.adapters.inbound.cli.Settings")
    @patch("evalvault.adapters.inbound.cli.LangfuseAdapter")
    def test_run_with_langfuse_logging(
        self,
        mock_langfuse_cls,
        mock_settings_cls,
        mock_get_llm,
        mock_evaluator_cls,
        mock_get_loader,
        tmp_path,
    ):
        """Langfuse 로깅 테스트."""
        from datetime import datetime, timedelta

        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = get_test_model()
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings.langfuse_public_key = "pub"
        mock_settings.langfuse_secret_key = "sec"
        mock_settings.langfuse_host = "https://example"
        mock_settings_cls.return_value = mock_settings

        mock_dataset = Dataset(
            name="test",
            version="1.0.0",
            test_cases=[
                TestCase(id="tc-001", question="Q", answer="A", contexts=["C"]),
            ],
        )
        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        mock_run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=start + timedelta(seconds=1),
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
            ],
        )
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_run)
        mock_evaluator_cls.return_value = mock_evaluator

        mock_tracker = MagicMock()
        mock_tracker.log_evaluation_run.return_value = "trace-123"
        mock_langfuse_cls.return_value = mock_tracker

        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")

        result = runner.invoke(
            app,
            ["run", str(test_file), "--metrics", "faithfulness", "--langfuse"],
        )
        assert result.exit_code == 0
        mock_tracker.log_evaluation_run.assert_called_once()

    @patch("evalvault.adapters.inbound.cli.get_loader")
    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_run_dataset_load_error(self, mock_settings_cls, mock_get_loader, tmp_path):
        """데이터셋 로드 에러 테스트."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings_cls.return_value = mock_settings

        mock_loader = MagicMock()
        mock_loader.load.side_effect = ValueError("Invalid format")
        mock_get_loader.return_value = mock_loader

        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")

        result = runner.invoke(app, ["run", str(test_file), "--metrics", "faithfulness"])
        assert result.exit_code == 1
        assert "Error loading dataset" in result.stdout

    @patch("evalvault.adapters.inbound.cli.get_loader")
    @patch("evalvault.adapters.inbound.cli.RagasEvaluator")
    @patch("evalvault.adapters.inbound.cli.get_llm_adapter")
    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_run_evaluation_error(
        self, mock_settings_cls, mock_get_llm, mock_evaluator_cls, mock_get_loader, tmp_path
    ):
        """평가 중 에러 테스트."""
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
                TestCase(id="tc-001", question="Q", answer="A", contexts=["C"]),
            ],
        )
        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_dataset
        mock_get_loader.return_value = mock_loader

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(side_effect=RuntimeError("API Error"))
        mock_evaluator_cls.return_value = mock_evaluator

        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")

        result = runner.invoke(app, ["run", str(test_file), "--metrics", "faithfulness"])
        assert result.exit_code == 1
        assert "Error during evaluation" in result.stdout

    @patch("evalvault.adapters.inbound.cli.get_loader")
    @patch("evalvault.adapters.inbound.cli.RagasEvaluator")
    @patch("evalvault.adapters.inbound.cli.get_llm_adapter")
    @patch("evalvault.adapters.inbound.cli.Settings")
    def test_run_with_parallel(
        self, mock_settings_cls, mock_get_llm, mock_evaluator_cls, mock_get_loader, tmp_path
    ):
        """병렬 평가 옵션 테스트."""
        from datetime import datetime, timedelta

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
                TestCase(id="tc-001", question="Q", answer="A", contexts=["C"]),
            ],
        )
        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        mock_run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=start + timedelta(seconds=1),
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
            ],
        )
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_run)
        mock_evaluator_cls.return_value = mock_evaluator

        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")

        result = runner.invoke(
            app,
            [
                "run",
                str(test_file),
                "--metrics",
                "faithfulness",
                "--parallel",
                "--batch-size",
                "10",
            ],
        )
        assert result.exit_code == 0
        # Verify parallel and batch_size were passed to evaluate
        mock_evaluator.evaluate.assert_called_once()
        call_kwargs = mock_evaluator.evaluate.call_args[1]
        assert call_kwargs["parallel"] is True
        assert call_kwargs["batch_size"] == 10


class TestCLIHistory:
    """CLI history 명령 테스트."""

    def test_history_help(self):
        """history 명령 help 테스트."""
        result = runner.invoke(app, ["history", "--help"])
        assert result.exit_code == 0
        assert "limit" in result.stdout.lower()

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    def test_history_no_runs(self, mock_storage_cls, tmp_path):
        """실행 이력이 없을 때 테스트."""
        mock_storage = MagicMock()
        mock_storage.list_runs.return_value = []
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(app, ["history", "--db", str(tmp_path / "test.db")])
        assert result.exit_code == 0
        assert "No evaluation runs found" in result.stdout

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    def test_history_with_runs(self, mock_storage_cls, tmp_path):
        """실행 이력 조회 테스트."""
        from datetime import datetime

        mock_run = MagicMock()
        mock_run.run_id = "abc12345-6789"
        mock_run.dataset_name = "test-dataset"
        mock_run.model_name = get_test_model()
        mock_run.started_at = datetime.now()
        mock_run.pass_rate = 0.85
        mock_run.total_test_cases = 10

        mock_storage = MagicMock()
        mock_storage.list_runs.return_value = [mock_run]
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(app, ["history", "--db", str(tmp_path / "test.db")])
        assert result.exit_code == 0
        assert "test-datas" in result.stdout  # Truncated in table

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    def test_history_with_filters(self, mock_storage_cls, tmp_path):
        """필터링 옵션 테스트."""
        mock_storage = MagicMock()
        mock_storage.list_runs.return_value = []
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            [
                "history",
                "--db",
                str(tmp_path / "test.db"),
                "--limit",
                "5",
                "--dataset",
                "my-dataset",
                "--model",
                "gpt-4",
            ],
        )
        assert result.exit_code == 0
        mock_storage.list_runs.assert_called_once_with(
            limit=5, dataset_name="my-dataset", model_name="gpt-4"
        )


class TestCLICompare:
    """CLI compare 명령 테스트."""

    def test_compare_help(self):
        """compare 명령 help 테스트."""
        result = runner.invoke(app, ["compare", "--help"])
        assert result.exit_code == 0

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    def test_compare_run_not_found(self, mock_storage_cls, tmp_path):
        """존재하지 않는 run ID 테스트."""
        mock_storage = MagicMock()
        mock_storage.get_run.side_effect = KeyError("Run not found")
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            ["compare", "run-1", "run-2", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 1

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    def test_compare_two_runs(self, mock_storage_cls, tmp_path):
        """두 실행 결과 비교 테스트."""

        mock_run1 = MagicMock()
        mock_run1.dataset_name = "test-dataset"
        mock_run1.model_name = "gpt-4"
        mock_run1.total_test_cases = 10
        mock_run1.pass_rate = 0.8
        mock_run1.metrics_evaluated = ["faithfulness"]
        mock_run1.get_avg_score.return_value = 0.85

        mock_run2 = MagicMock()
        mock_run2.dataset_name = "test-dataset"
        mock_run2.model_name = "gpt-4o"
        mock_run2.total_test_cases = 10
        mock_run2.pass_rate = 0.9
        mock_run2.metrics_evaluated = ["faithfulness"]
        mock_run2.get_avg_score.return_value = 0.90

        mock_storage = MagicMock()
        mock_storage.get_run.side_effect = [mock_run1, mock_run2]
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            ["compare", "run-1", "run-2", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        assert "Comparing" in result.stdout


class TestCLIExport:
    """CLI export 명령 테스트."""

    def test_export_help(self):
        """export 명령 help 테스트."""
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    def test_export_run_not_found(self, mock_storage_cls, tmp_path):
        """존재하지 않는 run ID 테스트."""
        mock_storage = MagicMock()
        mock_storage.get_run.side_effect = KeyError("Run not found")
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            [
                "export",
                "run-1",
                "--output",
                str(tmp_path / "output.json"),
                "--db",
                str(tmp_path / "test.db"),
            ],
        )
        assert result.exit_code == 1

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    def test_export_run_to_file(self, mock_storage_cls, tmp_path):
        """실행 결과 내보내기 테스트."""
        mock_run = MagicMock()
        mock_run.to_summary_dict.return_value = {
            "run_id": "run-123",
            "dataset_name": "test",
        }
        mock_run.results = []

        mock_storage = MagicMock()
        mock_storage.get_run.return_value = mock_run
        mock_storage_cls.return_value = mock_storage

        output_file = tmp_path / "output.json"
        result = runner.invoke(
            app,
            [
                "export",
                "run-1",
                "--output",
                str(output_file),
                "--db",
                str(tmp_path / "test.db"),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()


class TestCLIGenerate:
    """CLI generate 명령 테스트."""

    def test_generate_help(self):
        """generate 명령 help 테스트."""
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0

    def test_generate_invalid_method(self, tmp_path):
        """잘못된 메서드 테스트."""
        test_file = tmp_path / "doc.txt"
        test_file.write_text("Test document content.", encoding="utf-8")

        result = runner.invoke(
            app,
            ["generate", str(test_file), "--method", "invalid_method"],
        )
        assert result.exit_code == 1
        assert "Invalid method" in result.stdout

    def test_generate_basic_method(self, tmp_path):
        """기본 메서드로 테스트셋 생성 테스트."""
        test_file = tmp_path / "doc.txt"
        test_file.write_text(
            "This is a test document. It contains information about testing.", encoding="utf-8"
        )
        output_file = tmp_path / "testset.json"

        result = runner.invoke(
            app,
            [
                "generate",
                str(test_file),
                "--method",
                "basic",
                "--num",
                "3",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        data = json.loads(output_file.read_text(encoding="utf-8"))
        assert "test_cases" in data

    def test_generate_knowledge_graph_method(self, tmp_path):
        """지식 그래프 메서드로 테스트셋 생성 테스트."""
        test_file = tmp_path / "doc.txt"
        test_file.write_text(
            "삼성생명의 종신보험은 사망보험금 1억원을 보장합니다.", encoding="utf-8"
        )
        output_file = tmp_path / "testset.json"

        result = runner.invoke(
            app,
            [
                "generate",
                str(test_file),
                "--method",
                "knowledge_graph",
                "--num",
                "3",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()


class TestCLIExperiment:
    """CLI experiment 명령 테스트."""

    def test_experiment_create_help(self):
        """experiment-create 명령 help 테스트."""
        result = runner.invoke(app, ["experiment-create", "--help"])
        assert result.exit_code == 0

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    @patch("evalvault.adapters.inbound.cli.ExperimentManager")
    def test_experiment_create(self, mock_manager_cls, mock_storage_cls, tmp_path):
        """실험 생성 테스트."""

        from evalvault.domain.entities.experiment import Experiment

        mock_experiment = Experiment(
            name="Test Experiment",
            description="A test",
            hypothesis="Test hypothesis",
            metrics_to_compare=["faithfulness"],
        )
        mock_manager = MagicMock()
        mock_manager.create_experiment.return_value = mock_experiment
        mock_manager_cls.return_value = mock_manager

        result = runner.invoke(
            app,
            [
                "experiment-create",
                "--name",
                "Test Experiment",
                "--description",
                "A test",
                "--hypothesis",
                "Test hypothesis",
                "--metrics",
                "faithfulness",
                "--db",
                str(tmp_path / "test.db"),
            ],
        )
        assert result.exit_code == 0
        assert "Created experiment" in result.stdout

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    @patch("evalvault.adapters.inbound.cli.ExperimentManager")
    def test_experiment_add_group(self, mock_manager_cls, mock_storage_cls, tmp_path):
        """실험에 그룹 추가 테스트."""
        mock_manager = MagicMock()
        mock_manager_cls.return_value = mock_manager

        result = runner.invoke(
            app,
            [
                "experiment-add-group",
                "--id",
                "exp-123",
                "--group",
                "control",
                "--description",
                "Control group",
                "--db",
                str(tmp_path / "test.db"),
            ],
        )
        assert result.exit_code == 0
        mock_manager.add_group_to_experiment.assert_called_once()

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    @patch("evalvault.adapters.inbound.cli.ExperimentManager")
    def test_experiment_add_group_not_found(self, mock_manager_cls, mock_storage_cls, tmp_path):
        """존재하지 않는 실험에 그룹 추가 테스트."""
        mock_manager = MagicMock()
        mock_manager.add_group_to_experiment.side_effect = KeyError("Experiment not found")
        mock_manager_cls.return_value = mock_manager

        result = runner.invoke(
            app,
            [
                "experiment-add-group",
                "--id",
                "exp-123",
                "--group",
                "control",
                "--db",
                str(tmp_path / "test.db"),
            ],
        )
        assert result.exit_code == 1

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    @patch("evalvault.adapters.inbound.cli.ExperimentManager")
    def test_experiment_add_run(self, mock_manager_cls, mock_storage_cls, tmp_path):
        """실험 그룹에 run 추가 테스트."""
        mock_manager = MagicMock()
        mock_manager_cls.return_value = mock_manager

        result = runner.invoke(
            app,
            [
                "experiment-add-run",
                "--id",
                "exp-123",
                "--group",
                "control",
                "--run",
                "run-456",
                "--db",
                str(tmp_path / "test.db"),
            ],
        )
        assert result.exit_code == 0
        mock_manager.add_run_to_experiment_group.assert_called_once()

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    @patch("evalvault.adapters.inbound.cli.ExperimentManager")
    def test_experiment_list(self, mock_manager_cls, mock_storage_cls, tmp_path):
        """실험 목록 조회 테스트."""
        mock_manager = MagicMock()
        mock_manager.list_experiments.return_value = []
        mock_manager_cls.return_value = mock_manager

        result = runner.invoke(
            app,
            ["experiment-list", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        assert "No experiments found" in result.stdout

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    @patch("evalvault.adapters.inbound.cli.ExperimentManager")
    def test_experiment_list_with_experiments(self, mock_manager_cls, mock_storage_cls, tmp_path):
        """실험 목록 조회 테스트 (실험 있음)."""

        from evalvault.domain.entities.experiment import Experiment

        mock_experiment = Experiment(
            name="Test Exp",
            status="running",
        )
        mock_manager = MagicMock()
        mock_manager.list_experiments.return_value = [mock_experiment]
        mock_manager_cls.return_value = mock_manager

        result = runner.invoke(
            app,
            ["experiment-list", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        assert "Test Exp" in result.stdout

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    @patch("evalvault.adapters.inbound.cli.ExperimentManager")
    def test_experiment_compare(self, mock_manager_cls, mock_storage_cls, tmp_path):
        """실험 그룹 비교 테스트."""
        from evalvault.domain.entities.experiment import Experiment, ExperimentGroup

        mock_experiment = Experiment(
            name="Test Exp",
            groups=[
                ExperimentGroup(name="control"),
                ExperimentGroup(name="variant"),
            ],
        )
        mock_comparison = MagicMock()
        mock_comparison.metric_name = "faithfulness"
        mock_comparison.group_scores = {"control": 0.8, "variant": 0.9}
        mock_comparison.best_group = "variant"
        mock_comparison.improvement = 12.5

        mock_manager = MagicMock()
        mock_manager.get_experiment.return_value = mock_experiment
        mock_manager.compare_groups.return_value = [mock_comparison]
        mock_manager_cls.return_value = mock_manager

        result = runner.invoke(
            app,
            ["experiment-compare", "--id", "exp-123", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    @patch("evalvault.adapters.inbound.cli.ExperimentManager")
    def test_experiment_compare_no_data(self, mock_manager_cls, mock_storage_cls, tmp_path):
        """비교 데이터 없을 때 테스트."""
        from evalvault.domain.entities.experiment import Experiment

        mock_experiment = Experiment(name="Test Exp")
        mock_manager = MagicMock()
        mock_manager.get_experiment.return_value = mock_experiment
        mock_manager.compare_groups.return_value = []
        mock_manager_cls.return_value = mock_manager

        result = runner.invoke(
            app,
            ["experiment-compare", "--id", "exp-123", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        assert "No comparison data" in result.stdout

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    @patch("evalvault.adapters.inbound.cli.ExperimentManager")
    def test_experiment_conclude(self, mock_manager_cls, mock_storage_cls, tmp_path):
        """실험 종료 테스트."""
        mock_manager = MagicMock()
        mock_manager_cls.return_value = mock_manager

        result = runner.invoke(
            app,
            [
                "experiment-conclude",
                "--id",
                "exp-123",
                "--conclusion",
                "Variant A is better",
                "--db",
                str(tmp_path / "test.db"),
            ],
        )
        assert result.exit_code == 0
        mock_manager.conclude_experiment.assert_called_once()

    @patch("evalvault.adapters.inbound.cli.SQLiteStorageAdapter")
    @patch("evalvault.adapters.inbound.cli.ExperimentManager")
    def test_experiment_summary(self, mock_manager_cls, mock_storage_cls, tmp_path):
        """실험 요약 테스트."""
        mock_manager = MagicMock()
        mock_manager.get_summary.return_value = {
            "experiment_id": "exp-123",
            "name": "Test Experiment",
            "status": "completed",
            "created_at": "2024-01-01",
            "description": "A test experiment",
            "hypothesis": "Variant is better",
            "metrics_to_compare": ["faithfulness"],
            "groups": {
                "control": {"description": "Control group", "num_runs": 2, "run_ids": []},
            },
            "conclusion": "Hypothesis confirmed",
        }
        mock_manager_cls.return_value = mock_manager

        result = runner.invoke(
            app,
            ["experiment-summary", "--id", "exp-123", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        assert "Test Experiment" in result.stdout


class TestHelperFunctions:
    """Helper 함수 테스트."""

    def test_load_documents_from_directory(self, tmp_path):
        """디렉토리에서 문서 로드 테스트."""
        from evalvault.adapters.inbound.cli import _load_documents_from_source

        # Create test files
        (tmp_path / "doc1.txt").write_text("Document 1 content", encoding="utf-8")
        (tmp_path / "doc2.md").write_text("Document 2 content", encoding="utf-8")
        (tmp_path / "ignored.py").write_text("Not a document", encoding="utf-8")

        documents = _load_documents_from_source(tmp_path)
        assert len(documents) == 2

    def test_load_documents_from_json_list(self, tmp_path):
        """JSON 리스트에서 문서 로드 테스트."""
        from evalvault.adapters.inbound.cli import _load_documents_from_source

        json_file = tmp_path / "docs.json"
        json_file.write_text(
            json.dumps(["Doc 1", "Doc 2", "Doc 3"]),
            encoding="utf-8",
        )

        documents = _load_documents_from_source(json_file)
        assert len(documents) == 3

    def test_load_documents_from_json_with_content_field(self, tmp_path):
        """JSON 객체의 content 필드에서 문서 로드 테스트."""
        from evalvault.adapters.inbound.cli import _load_documents_from_source

        json_file = tmp_path / "docs.json"
        json_file.write_text(
            json.dumps([{"content": "Doc 1"}, {"content": "Doc 2"}]),
            encoding="utf-8",
        )

        documents = _load_documents_from_source(json_file)
        assert len(documents) == 2

    def test_load_documents_from_csv(self, tmp_path):
        """CSV에서 문서 로드 테스트."""
        from evalvault.adapters.inbound.cli import _load_documents_from_source

        csv_file = tmp_path / "docs.csv"
        csv_file.write_text("Line 1\nLine 2\nLine 3", encoding="utf-8")

        documents = _load_documents_from_source(csv_file)
        assert len(documents) == 3

    def test_load_documents_from_text_paragraphs(self, tmp_path):
        """텍스트 파일의 단락에서 문서 로드 테스트."""
        from evalvault.adapters.inbound.cli import _load_documents_from_source

        txt_file = tmp_path / "doc.txt"
        txt_file.write_text("Paragraph 1\n\nParagraph 2\n\nParagraph 3", encoding="utf-8")

        documents = _load_documents_from_source(txt_file)
        assert len(documents) == 3

    def test_extract_texts_from_mapping_with_documents_key(self, tmp_path):
        """JSON 매핑의 documents 키에서 텍스트 추출 테스트."""
        from evalvault.adapters.inbound.cli import _load_documents_from_source

        json_file = tmp_path / "docs.json"
        json_file.write_text(
            json.dumps({"documents": [{"content": "Doc 1"}, {"text": "Doc 2"}]}),
            encoding="utf-8",
        )

        documents = _load_documents_from_source(json_file)
        assert len(documents) == 2


class TestDisplayKGStats:
    """KG 통계 표시 함수 테스트."""

    def test_display_kg_stats_with_all_data(self, capsys):
        """모든 데이터가 있는 KG 통계 표시 테스트."""
        from evalvault.adapters.inbound.cli import _display_kg_stats

        stats = {
            "num_entities": 10,
            "num_relations": 15,
            "isolated_entities": ["Entity1", "Entity2"],
            "entity_types": {"COMPANY": 5, "PRODUCT": 5},
            "relation_types": {"PROVIDES": 10, "COVERS": 5},
            "build_metrics": {
                "documents_processed": 3,
                "entities_added": 10,
                "relations_added": 15,
            },
            "sample_entities": [
                {
                    "name": "Samsung",
                    "entity_type": "COMPANY",
                    "confidence": 0.95,
                    "provenance": "doc1",
                }
            ],
            "sample_relations": [
                {
                    "source": "Samsung",
                    "relation_type": "PROVIDES",
                    "target": "Insurance",
                    "confidence": 0.9,
                }
            ],
        }

        _display_kg_stats(stats)
        # No exception means success
