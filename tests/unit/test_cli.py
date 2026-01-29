"""Tests for CLI interface."""

import json
import os
import re
from datetime import datetime
from email.message import Message
from importlib.metadata import version as get_version
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import ANY, AsyncMock, MagicMock, patch
from urllib.error import HTTPError

import pytest
from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app
from evalvault.adapters.inbound.cli.commands import run as run_command_module
from evalvault.adapters.outbound.phoenix.sync_service import (
    PhoenixDatasetInfo,
    PhoenixExperimentInfo,
)
from evalvault.domain.entities import (
    Dataset,
    EffortLevel,
    EvaluationRun,
    MetricScore,
    TestCase,
    TestCaseResult,
)
from evalvault.domain.entities.analysis import ComparisonResult
from tests.optional_deps import sklearn_ready
from tests.unit.conftest import get_test_model


def strip_ansi(text: str) -> str:
    ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_pattern.sub("", text)


runner = CliRunner()
RUN_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.run"
HISTORY_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.history"
COMPARE_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.compare"
ANALYZE_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.analyze"
PIPELINE_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.pipeline"
GATE_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.gate"

HAS_SKLEARN, SKLEARN_SKIP_REASON = sklearn_ready()
SKLEARN_SKIP_REASON = SKLEARN_SKIP_REASON or "scikit-learn unavailable"
GENERATE_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.generate"
EXPERIMENT_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.experiment"
KG_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.kg"
BENCHMARK_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.benchmark"
CONFIG_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.config"
LANGFUSE_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.langfuse"
PROFILE_DIFFICULTY_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.profile_difficulty"


class TestCLIVersion:
    def test_version_command(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        expected_version = get_version("evalvault")
        assert expected_version in result.stdout


class TestCLIProfileDifficulty:
    def test_profile_difficulty_requires_target(self):
        result = runner.invoke(app, ["profile-difficulty", "--db", "data/db/evalvault.db"])
        assert result.exit_code != 0

    @patch(f"{PROFILE_DIFFICULTY_COMMAND_MODULE}.DifficultyProfilingService")
    @patch(f"{PROFILE_DIFFICULTY_COMMAND_MODULE}.build_storage_adapter")
    def test_profile_difficulty_writes_output(
        self,
        mock_storage_cls,
        mock_service_cls,
        tmp_path,
    ):
        output_path = tmp_path / "difficulty.json"
        artifacts_dir = tmp_path / "artifacts"
        mock_storage_cls.return_value = MagicMock()
        mock_service = MagicMock()
        mock_service.profile.return_value = {"artifacts": {"dir": str(artifacts_dir)}}
        mock_service_cls.return_value = mock_service

        result = runner.invoke(
            app,
            [
                "profile-difficulty",
                "--dataset-name",
                "demo",
                "--db",
                "data/db/evalvault.db",
                "--output",
                str(output_path),
                "--artifacts-dir",
                str(artifacts_dir),
            ],
        )

        assert result.exit_code == 0, result.stdout
        mock_service.profile.assert_called_once()
        call_args = mock_service.profile.call_args[0][0]
        assert call_args.dataset_name == "demo"
        assert call_args.output_path == output_path
        assert call_args.artifacts_dir == artifacts_dir


class TestCLIRun:
    @pytest.fixture
    def mock_dataset(self):
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
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "dataset" in result.stdout.lower()
        assert "metrics" in result.stdout.lower()

    def test_run_missing_dataset(self):
        result = runner.invoke(app, ["run", "nonexistent.csv"])
        assert result.exit_code != 0

    @patch(f"{RUN_COMMAND_MODULE}._evaluate_streaming_run", new_callable=AsyncMock)
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
    def test_run_streaming_invokes_helper(
        self,
        mock_settings_cls,
        mock_get_loader,
        mock_evaluator_cls,
        mock_get_llm_adapter,
        mock_stream_helper,
        mock_evaluation_run,
        tmp_path,
    ):
        dataset_file = tmp_path / "dataset.csv"
        dataset_file.write_text("id,question,answer,contexts\n", encoding="utf-8")

        mock_settings = MagicMock()
        mock_settings.openai_api_key = "key"
        mock_settings.openai_model = get_test_model()
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings.phoenix_enabled = False
        mock_settings_cls.return_value = mock_settings

        mock_get_loader.return_value = MagicMock()
        mock_evaluator_cls.return_value = MagicMock()

        mock_llm = MagicMock()
        mock_get_llm_adapter.return_value = mock_llm

        mock_stream_helper.return_value = mock_evaluation_run

        result = runner.invoke(
            app,
            [
                "run",
                str(dataset_file),
                "--metrics",
                "faithfulness",
                "--stream",
                "--stream-chunk-size",
                "1",
            ],
        )

        assert result.exit_code == 0, result.stdout
        mock_stream_helper.assert_awaited_once()
        args, kwargs = mock_stream_helper.await_args
        assert kwargs["dataset_path"] == dataset_file
        assert kwargs["metrics"] == ["faithfulness"]
        assert kwargs["chunk_size"] == 1
        mock_get_loader.assert_not_called()

    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
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

        # Assert with better error message
        assert result.exit_code == 0, f"CLI failed with output: {result.stdout}"

    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
    def test_run_with_summary_preset(
        self,
        mock_settings_cls,
        mock_get_llm_adapter,
        mock_evaluator_cls,
        mock_get_loader,
        mock_dataset,
        tmp_path,
    ):
        """--summary 플래그가 요약 프리셋 메트릭을 적용한다."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = get_test_model()
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings_cls.return_value = mock_settings

        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_dataset
        mock_get_loader.return_value = mock_loader

        summary_metrics = [
            MetricScore(name="summary_score", score=0.9, threshold=0.7),
            MetricScore(name="summary_faithfulness", score=0.92, threshold=0.7),
            MetricScore(name="entity_preservation", score=0.88, threshold=0.7),
        ]
        summary_run = EvaluationRun(
            dataset_name="test-dataset",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            metrics_evaluated=[
                "summary_score",
                "summary_faithfulness",
                "entity_preservation",
            ],
            thresholds={
                "summary_score": 0.7,
                "summary_faithfulness": 0.7,
                "entity_preservation": 0.7,
            },
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=summary_metrics,
                )
            ],
        )

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=summary_run)
        mock_evaluator_cls.return_value = mock_evaluator

        mock_llm = MagicMock()
        mock_get_llm_adapter.return_value = mock_llm

        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n")

        result = runner.invoke(app, ["run", str(test_file), "--summary"])

        assert result.exit_code == 0, result.stdout
        eval_kwargs = mock_evaluator.evaluate.await_args.kwargs
        assert eval_kwargs["metrics"] == [
            "summary_score",
            "summary_faithfulness",
            "entity_preservation",
        ]
        assert "test-dataset" in result.stdout or "faithfulness" in result.stdout

    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
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

    @pytest.mark.skipif(
        bool(os.environ.get("CI")),
        reason="CI 환경에서는 Ollama 서버가 없습니다.",
    )
    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
    def test_run_with_oss_model_routes_to_ollama(
        self,
        mock_settings_cls,
        mock_get_llm_adapter,
        mock_evaluator_cls,
        mock_get_loader,
        mock_dataset,
        mock_evaluation_run,
        tmp_path,
    ):
        """gpt-oss-* 모델은 자동으로 Ollama 백엔드로 전환."""

        mock_settings = MagicMock()
        mock_settings.openai_api_key = None
        mock_settings.openai_model = get_test_model()
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings.ollama_model = "gemma3:1b"
        mock_settings.ollama_embedding_model = "qwen3-embedding:0.6b"
        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_settings_cls.return_value = mock_settings

        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_dataset
        mock_get_loader.return_value = mock_loader

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_evaluation_run)
        mock_evaluator_cls.return_value = mock_evaluator

        mock_llm = MagicMock()
        mock_get_llm_adapter.return_value = mock_llm

        test_file = tmp_path / "test.csv"
        test_file.write_text("id,question,answer,contexts\n", encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "run",
                str(test_file),
                "--metrics",
                "faithfulness",
                "--model",
                "gpt-oss-safeguard:20b",
            ],
        )

        assert result.exit_code == 0, result.stdout
        assert mock_settings.llm_provider == "ollama"
        assert mock_settings.ollama_model == "gpt-oss-safeguard:20b"

    @patch(f"{RUN_COMMAND_MODULE}.MemoryBasedAnalysis")
    @patch(f"{RUN_COMMAND_MODULE}.MemoryAwareEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.build_domain_memory_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
    def test_run_with_domain_memory_options(
        self,
        mock_settings_cls,
        mock_get_llm_adapter,
        mock_evaluator_cls,
        mock_get_loader,
        mock_memory_adapter_cls,
        mock_memory_eval_cls,
        mock_memory_analysis_cls,
        tmp_path,
    ):
        """Domain Memory 옵션이 활성화되면 관련 서비스가 호출된다."""
        from datetime import datetime, timedelta

        mock_settings = MagicMock()
        mock_settings.openai_api_key = "key"
        mock_settings.openai_model = get_test_model()
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings.phoenix_endpoint = "http://localhost:6006"
        mock_settings_cls.return_value = mock_settings

        dataset = Dataset(
            name="domain-dataset",
            version="0.1.0",
            metadata={},
            test_cases=[TestCase(id="tc-1", question="질문", answer="답", contexts=[])],
        )
        mock_loader = MagicMock()
        mock_loader.load.return_value = dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        end = start + timedelta(seconds=1)
        mock_run = EvaluationRun(
            dataset_name="domain-dataset",
            dataset_version="0.1.0",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            thresholds={"faithfulness": 0.7},
            started_at=start,
            finished_at=end,
            results=[
                TestCaseResult(
                    test_case_id="tc-1",
                    metrics=[MetricScore(name="faithfulness", score=0.8, threshold=0.7)],
                )
            ],
        )

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_run)
        mock_evaluator_cls.return_value = mock_evaluator
        mock_get_llm_adapter.return_value = MagicMock()

        mock_memory_adapter = MagicMock()
        mock_memory_adapter.get_aggregated_reliability.return_value = {"faithfulness": 0.65}
        mock_memory_adapter_cls.return_value = mock_memory_adapter

        mock_memory_eval = MagicMock()
        mock_memory_eval.evaluate_with_memory = AsyncMock(return_value=mock_run)
        mock_memory_eval.augment_context_with_facts.return_value = "[관련 사실]\n- Fact"
        mock_memory_eval_cls.return_value = mock_memory_eval

        mock_analysis = mock_memory_analysis_cls.return_value
        mock_analysis.generate_insights.return_value = {
            "trends": {"faithfulness": {"delta": 0.1, "baseline": 0.6, "current": 0.7}},
            "recommendations": ["컨텍스트를 보강하세요."],
        }

        test_file = tmp_path / "cases.csv"
        test_file.write_text("id,question,answer,contexts\n")

        result = runner.invoke(
            app,
            [
                "run",
                str(test_file),
                "--metrics",
                "faithfulness",
                "--use-domain-memory",
                "--memory-domain",
                "insurance",
                "--augment-context",
            ],
        )

        assert result.exit_code == 0
        mock_memory_adapter_cls.assert_called_once()
        mock_memory_eval.evaluate_with_memory.assert_awaited()
        mock_analysis.generate_insights.assert_called_once()
        assert "Domain Memory Insights" in result.stdout


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

    @patch(f"{KG_COMMAND_MODULE}.LangfuseAdapter")
    @patch(f"{KG_COMMAND_MODULE}.Settings")
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
        artifact_payload = kwargs.get("data")
        if artifact_payload is None and len(args) >= 3:
            artifact_payload = args[2]
        assert isinstance(artifact_payload, dict)
        artifact_payload = cast(dict[str, Any], artifact_payload)
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

    def test_kg_build_help(self):
        """kg build help 출력."""
        result = runner.invoke(app, ["kg", "build", "--help"])
        assert result.exit_code == 0
        assert "--workers" in result.stdout or "-w" in result.stdout
        assert "--batch-size" in result.stdout or "-b" in result.stdout
        assert "--output" in result.stdout or "-o" in result.stdout

    def test_kg_build_runs_on_text_file(self, tmp_path):
        """간단한 텍스트 파일로 kg build 실행."""
        sample_file = tmp_path / "doc.txt"
        sample_file.write_text("삼성생명의 종신보험은 사망보험금을 보장합니다.", encoding="utf-8")

        result = runner.invoke(app, ["kg", "build", str(sample_file)])

        assert result.exit_code == 0
        assert "KG Build Summary" in result.stdout
        assert "Documents Processed" in result.stdout

    def test_kg_build_with_output(self, tmp_path):
        """--output 옵션으로 JSON 저장."""
        sample_file = tmp_path / "doc.txt"
        sample_file.write_text("삼성생명의 종신보험은 사망보험금을 보장합니다.", encoding="utf-8")
        output = tmp_path / "kg_result.json"

        result = runner.invoke(
            app,
            ["kg", "build", str(sample_file), "--output", str(output)],
        )

        assert result.exit_code == 0
        assert output.exists()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["type"] == "kg_build_result"
        assert "stats" in data
        assert "graph" in data

    def test_kg_build_with_workers_and_batch(self, tmp_path):
        """--workers, --batch-size 옵션 전달."""
        sample_file = tmp_path / "doc.txt"
        sample_file.write_text("삼성생명의 종신보험은 사망보험금을 보장합니다.", encoding="utf-8")

        result = runner.invoke(
            app,
            ["kg", "build", str(sample_file), "--workers", "2", "--batch-size", "16"],
        )

        assert result.exit_code == 0
        assert "workers=2" in result.stdout
        assert "batch_size=16" in result.stdout

    def test_kg_build_verbose(self, tmp_path):
        """--verbose 옵션으로 상세 진행 출력."""
        sample_file = tmp_path / "doc.txt"
        sample_file.write_text("삼성생명의 종신보험은 사망보험금을 보장합니다.", encoding="utf-8")

        result = runner.invoke(
            app,
            ["kg", "build", str(sample_file), "--verbose"],
        )

        assert result.exit_code == 0
        # verbose 모드에서는 Chunk 진행 상황이 출력됨
        assert "Chunk" in result.stdout or "KG Build Summary" in result.stdout

    def test_kg_build_empty_file(self, tmp_path):
        """빈 파일에서 에러 처리."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("", encoding="utf-8")

        result = runner.invoke(app, ["kg", "build", str(empty_file)])

        assert result.exit_code == 1
        assert "Error" in result.stdout

    def test_kg_build_directory(self, tmp_path):
        """디렉터리에서 여러 파일 처리."""
        doc1 = tmp_path / "doc1.txt"
        doc2 = tmp_path / "doc2.txt"
        doc1.write_text("삼성생명의 종신보험은 사망보험금을 보장합니다.", encoding="utf-8")
        doc2.write_text("현대해상의 자동차보험은 사고 시 보상합니다.", encoding="utf-8")

        result = runner.invoke(app, ["kg", "build", str(tmp_path)])

        assert result.exit_code == 0
        assert "2 documents" in result.stdout


class TestCLIConfig:
    """CLI config 명령 테스트."""

    @patch(f"{RUN_COMMAND_MODULE}.Settings")
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

    @patch(f"{LANGFUSE_COMMAND_MODULE}.Settings")
    def test_dashboard_requires_credentials(self, mock_settings_cls):
        mock_settings = MagicMock()
        mock_settings.langfuse_public_key = None
        mock_settings.langfuse_secret_key = None
        mock_settings_cls.return_value = mock_settings

        result = runner.invoke(app, ["langfuse-dashboard"])
        assert result.exit_code != 0
        assert "credentials" in result.stdout.lower()

    @patch(f"{LANGFUSE_COMMAND_MODULE}._fetch_langfuse_traces")
    @patch(f"{LANGFUSE_COMMAND_MODULE}.Settings")
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

    @patch(f"{LANGFUSE_COMMAND_MODULE}._fetch_langfuse_traces")
    @patch(f"{LANGFUSE_COMMAND_MODULE}.Settings")
    def test_dashboard_handles_http_error(self, mock_settings_cls, mock_fetch):
        mock_settings = MagicMock()
        mock_settings.langfuse_public_key = "pub"
        mock_settings.langfuse_secret_key = "sec"
        mock_settings.langfuse_host = "https://example"
        mock_settings_cls.return_value = mock_settings

        headers: Message = Message()
        mock_fetch.side_effect = HTTPError(
            url="https://example/api/public/traces",
            code=405,
            msg="Method Not Allowed",
            hdrs=headers,
            fp=None,
        )

        result = runner.invoke(app, ["langfuse-dashboard"])

        assert result.exit_code == 0
        assert "public API not available" in result.stdout

    @patch(f"{LANGFUSE_COMMAND_MODULE}._fetch_langfuse_traces")
    @patch(f"{LANGFUSE_COMMAND_MODULE}.Settings")
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

    @patch("evalvault.adapters.outbound.tracker.phoenix_adapter.PhoenixAdapter")
    @patch(f"{RUN_COMMAND_MODULE}.ensure_phoenix_instrumentation", return_value=True)
    @patch(f"{RUN_COMMAND_MODULE}.log_phoenix_traces")
    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
    def test_run_logs_phoenix_traces(
        self,
        mock_settings_cls,
        mock_get_llm,
        mock_evaluator_cls,
        mock_get_loader,
        mock_log_traces,
        mock_ensure_phoenix,
        mock_phoenix_adapter,
        tmp_path,
    ):
        """--tracker phoenix 사용 시 RAG trace 로깅이 호출된다."""
        from datetime import datetime, timedelta

        mock_settings = MagicMock()
        mock_settings.openai_api_key = "key"
        mock_settings.openai_model = get_test_model()
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings_cls.return_value = mock_settings

        dataset = Dataset(
            name="phoenix-dataset",
            version="0.1.0",
            test_cases=[TestCase(id="tc-1", question="Q", answer="A", contexts=["ctx"])],
        )
        mock_loader = MagicMock()
        mock_loader.load.return_value = dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        mock_run = EvaluationRun(
            dataset_name="phoenix-dataset",
            dataset_version="0.1.0",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=start + timedelta(seconds=1),
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-1",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                    contexts=["ctx"],
                    question="Q",
                    answer="A",
                )
            ],
        )
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_run)
        mock_evaluator_cls.return_value = mock_evaluator
        mock_get_llm.return_value = MagicMock()

        tracker = MagicMock()
        tracker.log_evaluation_run.return_value = "trace-123"
        mock_phoenix_adapter.return_value = tracker

        test_file = tmp_path / "phoenix.csv"
        test_file.write_text("id,question,answer,contexts\n")

        result = runner.invoke(
            app,
            ["run", str(test_file), "--metrics", "faithfulness", "--tracker", "phoenix"],
        )

        assert result.exit_code == 0
        tracker.log_evaluation_run.assert_called_once()
        assert mock_ensure_phoenix.called
        mock_log_traces.assert_called_once()
        args, kwargs = mock_log_traces.call_args
        assert args == (tracker, mock_run)
        assert kwargs["max_traces"] is None
        assert "metadata" in kwargs

    @patch(f"{RUN_COMMAND_MODULE}.PhoenixSyncService")
    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
    def test_run_uploads_phoenix_dataset_when_requested(
        self,
        mock_settings_cls,
        mock_get_llm,
        mock_evaluator_cls,
        mock_get_loader,
        mock_phoenix_sync,
        tmp_path,
    ):
        """--phoenix-dataset 옵션 사용 시 Dataset 업로드 로직이 호출된다."""
        from datetime import datetime, timedelta

        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = get_test_model()
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings.phoenix_endpoint = "http://localhost:6006/v1/traces"
        mock_settings_cls.return_value = mock_settings

        dataset = Dataset(
            name="phoenix-ds",
            version="2024.12",
            metadata={"description": "Customer QA"},
            test_cases=[
                TestCase(id="tc-01", question="Q", answer="A", contexts=["ctx"]),
            ],
        )
        mock_loader = MagicMock()
        mock_loader.load.return_value = dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        mock_run = EvaluationRun(
            dataset_name="phoenix-ds",
            dataset_version="2024.12",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=start + timedelta(seconds=1),
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-01",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                )
            ],
        )
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_run)
        mock_evaluator_cls.return_value = mock_evaluator
        mock_get_llm.return_value = MagicMock()

        service = MagicMock()
        dataset_info = PhoenixDatasetInfo(
            dataset_id="ds_123",
            dataset_name="phoenix-ds",
            dataset_version_id="ver_1",
            url="http://phoenix/datasets/ds_123",
        )
        service.upload_dataset.return_value = dataset_info
        mock_phoenix_sync.return_value = service

        test_file = tmp_path / "phoenix.csv"
        test_file.write_text("id,question,answer,contexts\n")

        result = runner.invoke(
            app,
            [
                "run",
                str(test_file),
                "--metrics",
                "faithfulness",
                "--phoenix-dataset",
                "phoenix-ds",
            ],
        )

        assert result.exit_code == 0
        service.upload_dataset.assert_called_once_with(
            dataset=dataset,
            dataset_name="phoenix-ds",
            description="Customer QA",
        )
        phoenix_meta = mock_run.tracker_metadata["phoenix"]
        assert phoenix_meta["dataset"] == dataset_info.to_dict()
        assert phoenix_meta["schema_version"] == 2
        export_meta = phoenix_meta["embedding_export"]
        assert export_meta["dataset_id"] == "ds_123"
        assert "export-embeddings" in export_meta["cli"]

    @patch(f"{RUN_COMMAND_MODULE}.build_experiment_metadata")
    @patch(f"{RUN_COMMAND_MODULE}.PhoenixSyncService")
    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
    def test_run_creates_phoenix_experiment(
        self,
        mock_settings_cls,
        mock_get_llm,
        mock_evaluator_cls,
        mock_get_loader,
        mock_phoenix_sync,
        mock_build_metadata,
        tmp_path,
    ):
        """--phoenix-experiment 옵션 사용 시 Experiment가 생성된다."""
        from datetime import datetime, timedelta

        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = get_test_model()
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings.phoenix_endpoint = "http://localhost:6006/v1/traces"
        mock_settings_cls.return_value = mock_settings

        dataset = Dataset(
            name="phoenix-ds",
            version="2024.12",
            metadata={"description": "Customer QA"},
            test_cases=[
                TestCase(id="tc-01", question="Q", answer="A", contexts=["ctx"]),
            ],
        )
        mock_loader = MagicMock()
        mock_loader.load.return_value = dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        mock_run = EvaluationRun(
            dataset_name="phoenix-ds",
            dataset_version="2024.12",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=start + timedelta(seconds=1),
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-01",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                )
            ],
        )
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_run)
        mock_evaluator_cls.return_value = mock_evaluator
        mock_get_llm.return_value = MagicMock()

        service = MagicMock()
        dataset_info = PhoenixDatasetInfo(
            dataset_id="ds_123",
            dataset_name="phoenix-ds",
            dataset_version_id="ver_1",
            url="http://phoenix/datasets/ds_123",
        )
        experiment_info = PhoenixExperimentInfo(
            experiment_id="exp_555",
            dataset_id="ds_123",
            url="http://phoenix/experiments/exp_555",
            dataset_url="http://phoenix/datasets/ds_123",
        )
        service.upload_dataset.return_value = dataset_info
        service.create_experiment_record.return_value = experiment_info
        mock_phoenix_sync.return_value = service
        mock_build_metadata.return_value = {"pass_rate": 0.9}

        test_file = tmp_path / "phoenix.csv"
        test_file.write_text("id,question,answer,contexts\n")

        result = runner.invoke(
            app,
            [
                "run",
                str(test_file),
                "--metrics",
                "faithfulness",
                "--phoenix-dataset",
                "phoenix-ds",
                "--phoenix-experiment",
                "exp-A",
                "--phoenix-experiment-description",
                "Smoke run",
            ],
        )

        assert result.exit_code == 0
        service.upload_dataset.assert_called_once()
        mock_build_metadata.assert_called_once_with(
            run=mock_run,
            dataset=dataset,
            reliability_snapshot=None,
            extra=ANY,
        )
        service.create_experiment_record.assert_called_once_with(
            dataset_info=ANY,
            experiment_name="exp-A",
            description="Smoke run",
            metadata={"pass_rate": 0.9},
        )
        phoenix_meta = mock_run.tracker_metadata["phoenix"]
        assert phoenix_meta["experiment"] == experiment_info.to_dict()
        assert phoenix_meta["schema_version"] == 2

    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
    def test_run_attaches_prompt_metadata(
        self,
        mock_settings_cls,
        mock_get_llm,
        mock_evaluator_cls,
        mock_get_loader,
        tmp_path,
    ):
        """--prompt-files 사용 시 Phoenix 메타데이터에 Prompt 상태가 포함된다."""
        from datetime import datetime, timedelta

        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = get_test_model()
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings.phoenix_enabled = False
        mock_settings_cls.return_value = mock_settings

        dataset = Dataset(
            name="phoenix-ds",
            version="2024.12",
            test_cases=[
                TestCase(id="tc-01", question="Q", answer="A", contexts=["ctx"]),
            ],
        )
        mock_loader = MagicMock()
        mock_loader.load.return_value = dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        mock_run = EvaluationRun(
            dataset_name="phoenix-ds",
            dataset_version="2024.12",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=start + timedelta(seconds=1),
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-01",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                )
            ],
        )
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=mock_run)
        mock_evaluator_cls.return_value = mock_evaluator
        mock_get_llm.return_value = MagicMock()

        test_file = tmp_path / "phoenix.csv"
        test_file.write_text("id,question,answer,contexts\n")
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("prompt draft", encoding="utf-8")
        manifest_path = tmp_path / "prompt_manifest.json"

        result = runner.invoke(
            app,
            [
                "run",
                str(test_file),
                "--metrics",
                "faithfulness",
                "--prompt-manifest",
                str(manifest_path),
                "--prompt-files",
                str(prompt_file),
            ],
        )

        assert result.exit_code == 0
        phoenix_meta = mock_run.tracker_metadata["phoenix"]
        assert phoenix_meta["schema_version"] == 2
        assert phoenix_meta["prompts"]


class TestCLIRunModes:
    """심플/전체 실행 모드 전용 테스트."""

    @pytest.mark.parametrize(
        "command",
        [
            pytest.param(["run", "__DATASET__", "--mode", "simple"], id="with-flag"),
            pytest.param(["run-simple", "__DATASET__"], id="alias"),
        ],
    )
    @patch("evalvault.adapters.outbound.tracker.phoenix_adapter.PhoenixAdapter")
    @patch(f"{RUN_COMMAND_MODULE}.build_domain_memory_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.ensure_phoenix_instrumentation", return_value=True)
    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
    def test_simple_mode_forces_defaults(
        self,
        mock_settings_cls,
        mock_get_llm,
        mock_evaluator_cls,
        mock_get_loader,
        mock_ensure_phoenix,
        mock_memory_adapter,
        mock_phoenix_adapter,
        tmp_path,
        command,
    ):
        """심플 모드가 기본 metrics/phoenix tracker 적용 및 Domain Memory 비활성화."""
        from datetime import datetime, timedelta

        dataset = Dataset(
            name="simple-dataset",
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
        mock_loader = MagicMock()
        mock_loader.load.return_value = dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        run = EvaluationRun(
            dataset_name="simple-dataset",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=start + timedelta(seconds=1),
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-1",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                )
            ],
        )
        run.tracker_metadata = {}
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=run)
        mock_evaluator_cls.return_value = mock_evaluator
        mock_get_llm.return_value = MagicMock()

        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = get_test_model()
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings.phoenix_enabled = False
        mock_settings_cls.return_value = mock_settings

        test_file = tmp_path / "simple.csv"
        test_file.write_text("id,question,answer,contexts\n", encoding="utf-8")

        args = [str(test_file) if value == "__DATASET__" else value for value in command]
        result = runner.invoke(app, args)

        assert result.exit_code == 0, result.stdout
        assert "Run Mode: Simple" in result.stdout
        mock_memory_adapter.assert_not_called()
        mock_ensure_phoenix.assert_called_once()
        tracker_instance = mock_phoenix_adapter.return_value
        tracker_instance.log_evaluation_run.assert_called_once()
        eval_kwargs = mock_evaluator.evaluate.await_args.kwargs
        assert eval_kwargs["metrics"] == ["faithfulness", "answer_relevancy"]
        assert run.tracker_metadata.get("run_mode") == "simple"

    def test_invalid_mode_rejected(self, tmp_path):
        """지원하지 않는 --mode 값 사용 시 에러."""
        dataset_file = tmp_path / "dataset.csv"
        dataset_file.write_text("id,question,answer,contexts\n", encoding="utf-8")

        result = runner.invoke(app, ["run", str(dataset_file), "--mode", "invalid"])

        assert result.exit_code != 0
        assert "Error" in result.stdout

    @patch("evalvault.adapters.outbound.tracker.phoenix_adapter.PhoenixAdapter")
    @patch(f"{RUN_COMMAND_MODULE}.build_domain_memory_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.ensure_phoenix_instrumentation", return_value=True)
    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
    def test_full_mode_alias_shows_banner(
        self,
        mock_settings_cls,
        mock_get_llm,
        mock_evaluator_cls,
        mock_get_loader,
        mock_ensure_phoenix,
        mock_memory_adapter,
        mock_phoenix_adapter,
        tmp_path,
    ):
        """`run-full` 별칭도 모드 배너와 메타데이터를 출력."""
        from datetime import datetime, timedelta

        dataset = Dataset(
            name="full-dataset",
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
        mock_loader = MagicMock()
        mock_loader.load.return_value = dataset
        mock_get_loader.return_value = mock_loader

        start = datetime.now()
        run = EvaluationRun(
            dataset_name="full-dataset",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            metrics_evaluated=["faithfulness"],
            started_at=start,
            finished_at=start + timedelta(seconds=1),
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-1",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                )
            ],
        )
        run.tracker_metadata = {}
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(return_value=run)
        mock_evaluator_cls.return_value = mock_evaluator
        mock_get_llm.return_value = MagicMock()

        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = get_test_model()
        mock_settings.llm_provider = "openai"
        mock_settings.evalvault_profile = None
        mock_settings.phoenix_enabled = False
        mock_settings_cls.return_value = mock_settings

        test_file = tmp_path / "full.csv"
        test_file.write_text("id,question,answer,contexts\n", encoding="utf-8")

        result = runner.invoke(app, ["run-full", str(test_file)])

        assert result.exit_code == 0, result.stdout
        assert "Run Mode: Full" in result.stdout
        assert run.tracker_metadata.get("run_mode") == "full"

    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
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

        with patch(f"{RUN_COMMAND_MODULE}.apply_profile") as mock_apply:
            mock_apply.return_value = mock_settings
            result = runner.invoke(
                app, ["run", str(test_file), "--profile", "prod", "--metrics", "faithfulness"]
            )

        assert result.exit_code == 0
        assert "prod" in result.stdout

    @patch(f"{RUN_COMMAND_MODULE}.Settings")
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

    @pytest.mark.skipif(
        bool(os.environ.get("CI")),
        reason="CI 환경에서는 Ollama 서버가 없습니다.",
    )
    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
    def test_run_with_ollama_provider(
        self, mock_settings_cls, mock_get_llm, mock_evaluator_cls, mock_get_loader, tmp_path
    ):
        """Ollama 프로바이더 테스트."""
        from datetime import datetime, timedelta

        mock_settings = MagicMock()
        mock_settings.openai_api_key = None
        mock_settings.ollama_model = "gemma3:1b"
        mock_settings.ollama_embedding_model = "qwen3-embedding:0.6b"
        mock_settings.ollama_base_url = "http://localhost:11434"
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
            model_name="ollama/gemma3:1b",
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
        assert result.exit_code == 0, result.stdout
        assert "ollama" in result.stdout.lower()

    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
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

    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
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

    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
    @patch("evalvault.adapters.inbound.cli.commands.run_helpers.build_storage_adapter")
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

    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
    @patch("evalvault.adapters.outbound.tracker.langfuse_adapter.LangfuseAdapter")
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

    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
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
        assert "데이터셋을 불러오지 못했습니다." in strip_ansi(result.stdout)

    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
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
        assert "평가 실행 중 오류가 발생했습니다." in strip_ansi(result.stdout)

    @patch(f"{RUN_COMMAND_MODULE}.get_loader")
    @patch(f"{RUN_COMMAND_MODULE}.RagasEvaluator")
    @patch(f"{RUN_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{RUN_COMMAND_MODULE}.Settings")
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

    @patch(f"{HISTORY_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{HISTORY_COMMAND_MODULE}.Settings")
    @patch(f"{HISTORY_COMMAND_MODULE}.PhoenixExperimentResolver")
    def test_history_no_runs(
        self,
        mock_resolver_cls,
        mock_settings_cls,
        mock_storage_cls,
        tmp_path,
    ):
        """실행 이력이 없을 때 테스트."""
        mock_storage = MagicMock()
        mock_storage.list_runs.return_value = []
        mock_storage_cls.return_value = mock_storage
        mock_settings_cls.return_value = SimpleNamespace(
            phoenix_endpoint="http://localhost:6006/v1/traces",
            phoenix_api_token=None,
        )
        mock_resolver = mock_resolver_cls.return_value
        mock_resolver.is_available = False

        result = runner.invoke(app, ["history", "--db", str(tmp_path / "test.db")])
        assert result.exit_code == 0
        assert "No evaluation runs found" in result.stdout

    @patch(f"{HISTORY_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{HISTORY_COMMAND_MODULE}.Settings")
    @patch(f"{HISTORY_COMMAND_MODULE}.PhoenixExperimentResolver")
    def test_history_with_runs(
        self,
        mock_resolver_cls,
        mock_settings_cls,
        mock_storage_cls,
        tmp_path,
    ):
        """실행 이력 조회 테스트."""
        from datetime import datetime

        mock_run = MagicMock()
        mock_run.run_id = "abc12345-6789"
        mock_run.dataset_name = "test-dataset"
        mock_run.model_name = get_test_model()
        mock_run.started_at = datetime.now()
        mock_run.pass_rate = 0.85
        mock_run.total_test_cases = 10
        mock_run.tracker_metadata = {"run_mode": "simple"}

        mock_storage = MagicMock()
        mock_storage.list_runs.return_value = [mock_run]
        mock_storage_cls.return_value = mock_storage
        mock_settings_cls.return_value = SimpleNamespace(
            phoenix_endpoint="http://localhost:6006/v1/traces",
            phoenix_api_token=None,
        )
        mock_resolver = mock_resolver_cls.return_value
        mock_resolver.is_available = False

        result = runner.invoke(app, ["history", "--db", str(tmp_path / "test.db")])
        assert result.exit_code == 0
        assert "abc12345" in result.stdout  # Run ID truncated
        assert "Simple" in result.stdout

    @patch(f"{HISTORY_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{HISTORY_COMMAND_MODULE}.Settings")
    @patch(f"{HISTORY_COMMAND_MODULE}.PhoenixExperimentResolver")
    def test_history_with_filters(
        self,
        mock_resolver_cls,
        mock_settings_cls,
        mock_storage_cls,
        tmp_path,
    ):
        """필터링 옵션 테스트."""
        mock_storage = MagicMock()
        mock_storage.list_runs.return_value = []
        mock_storage_cls.return_value = mock_storage
        mock_settings_cls.return_value = SimpleNamespace(
            phoenix_endpoint="http://localhost:6006/v1/traces",
            phoenix_api_token=None,
        )
        mock_resolver = mock_resolver_cls.return_value
        mock_resolver.is_available = False

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
                "--mode",
                "simple",
            ],
        )
        assert result.exit_code == 0

    @patch(f"{HISTORY_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{HISTORY_COMMAND_MODULE}.Settings")
    @patch(f"{HISTORY_COMMAND_MODULE}.PhoenixExperimentResolver")
    def test_history_with_phoenix_metrics(
        self,
        mock_resolver_cls,
        mock_settings_cls,
        mock_storage_cls,
        tmp_path,
    ):
        """Phoenix Experiment 메트릭 표시 테스트."""
        from datetime import datetime

        mock_run = MagicMock()
        mock_run.run_id = "abc12345-6789"
        mock_run.dataset_name = "test-dataset"
        mock_run.model_name = get_test_model()
        mock_run.started_at = datetime.now()
        mock_run.pass_rate = 0.85
        mock_run.total_test_cases = 10
        mock_run.tracker_metadata = {
            "phoenix": {
                "dataset": {"dataset_id": "ds_123"},
                "experiment": {"experiment_id": "exp_456"},
            }
        }
        mock_run.tracker_metadata["run_mode"] = "full"

        mock_storage = MagicMock()
        mock_storage.list_runs.return_value = [mock_run]
        mock_storage_cls.return_value = mock_storage
        mock_settings_cls.return_value = SimpleNamespace(
            phoenix_endpoint="http://localhost:6006/v1/traces",
            phoenix_api_token=None,
        )
        mock_resolver = mock_resolver_cls.return_value
        mock_resolver.is_available = True
        mock_resolver.can_resolve.return_value = True
        mock_resolver.get_stats.return_value = SimpleNamespace(
            precision_at_k=0.82,
            drift_score=0.12,
        )

        result = runner.invoke(app, ["history", "--db", str(tmp_path / "test.db")])
        assert result.exit_code == 0
        assert "0.82" in result.stdout

    @patch(f"{HISTORY_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{HISTORY_COMMAND_MODULE}.Settings")
    @patch(f"{HISTORY_COMMAND_MODULE}.PhoenixExperimentResolver")
    def test_history_filters_by_mode(
        self,
        mock_resolver_cls,
        mock_settings_cls,
        mock_storage_cls,
        tmp_path,
    ):
        """--mode 필터가 해당 모드만 표시한다."""
        from datetime import datetime

        simple_run = MagicMock()
        simple_run.run_id = "simple-run"
        simple_run.dataset_name = "simple-dataset"
        simple_run.model_name = get_test_model()
        simple_run.started_at = datetime.now()
        simple_run.pass_rate = 0.9
        simple_run.total_test_cases = 5
        simple_run.tracker_metadata = {"run_mode": "simple"}

        full_run = MagicMock()
        full_run.run_id = "full-run"
        full_run.dataset_name = "full-dataset"
        full_run.model_name = get_test_model()
        full_run.started_at = datetime.now()
        full_run.pass_rate = 0.8
        full_run.total_test_cases = 8
        full_run.tracker_metadata = {"run_mode": "full"}

        mock_storage = MagicMock()
        mock_storage.list_runs.return_value = [simple_run, full_run]
        mock_storage_cls.return_value = mock_storage
        mock_settings_cls.return_value = SimpleNamespace(
            phoenix_endpoint="http://localhost:6006/v1/traces",
            phoenix_api_token=None,
        )
        mock_resolver = mock_resolver_cls.return_value
        mock_resolver.is_available = False

        result = runner.invoke(
            app,
            [
                "history",
                "--db",
                str(tmp_path / "test.db"),
                "--mode",
                "simple",
            ],
        )
        assert result.exit_code == 0
        # Check for truncated dataset name (may vary by terminal width)
        assert "simple-" in result.stdout or "simple-d" in result.stdout
        assert "full-" not in result.stdout


class TestCLICompare:
    """CLI compare 명령 테스트."""

    def test_compare_help(self):
        """compare 명령 help 테스트."""
        result = runner.invoke(app, ["compare", "--help"])
        assert result.exit_code == 0

    @patch(f"{COMPARE_COMMAND_MODULE}.ComparisonPipelineAdapter")
    @patch(f"{COMPARE_COMMAND_MODULE}.build_analysis_pipeline_service")
    @patch(f"{COMPARE_COMMAND_MODULE}.build_storage_adapter")
    def test_compare_run_not_found(
        self,
        mock_storage_cls,
        mock_pipeline_factory,
        mock_pipeline_adapter_cls,
        tmp_path,
    ):
        """존재하지 않는 run ID 테스트."""
        mock_storage = MagicMock()
        mock_storage.get_run.side_effect = KeyError("Run not found")
        mock_storage_cls.return_value = mock_storage

        mock_pipeline_adapter = MagicMock()
        mock_pipeline_adapter_cls.return_value = mock_pipeline_adapter
        mock_pipeline_factory.return_value = MagicMock()

        result = runner.invoke(
            app,
            ["compare", "run-1", "run-2", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 1

    @patch(f"{COMPARE_COMMAND_MODULE}.ComparisonPipelineAdapter")
    @patch(f"{COMPARE_COMMAND_MODULE}.build_analysis_pipeline_service")
    @patch(f"{COMPARE_COMMAND_MODULE}.build_storage_adapter")
    def test_compare_two_runs(
        self,
        mock_storage_cls,
        mock_pipeline_factory,
        mock_pipeline_adapter_cls,
        tmp_path,
    ):
        """두 실행 결과 비교 테스트."""

        mock_run1 = MagicMock()
        mock_run1.run_id = "run-1"
        mock_run1.dataset_name = "test-dataset"
        mock_run1.model_name = "gpt-4"
        mock_run1.total_test_cases = 10
        mock_run1.pass_rate = 0.8
        mock_run1.metrics_evaluated = ["faithfulness"]
        mock_run1.get_avg_score.return_value = 0.85
        mock_run1.thresholds = {"faithfulness": 0.7}

        mock_run2 = MagicMock()
        mock_run2.run_id = "run-2"
        mock_run2.dataset_name = "test-dataset"
        mock_run2.model_name = "gpt-4o"
        mock_run2.total_test_cases = 10
        mock_run2.pass_rate = 0.9
        mock_run2.metrics_evaluated = ["faithfulness"]
        mock_run2.get_avg_score.return_value = 0.90
        mock_run2.thresholds = {"faithfulness": 0.7}

        mock_storage = MagicMock()
        mock_storage.get_run.side_effect = [mock_run1, mock_run2]
        mock_storage_cls.return_value = mock_storage

        pipeline_result = MagicMock()
        pipeline_result.final_output = {"report": "# 비교 분석 보고서"}
        pipeline_result.all_succeeded = True
        pipeline_result.node_results = {}
        pipeline_result.is_complete = True
        pipeline_result.total_duration_ms = 1200
        pipeline_result.started_at = datetime.now()
        pipeline_result.finished_at = datetime.now()
        pipeline_result.pipeline_id = "pipeline-1"
        pipeline_result.intent = SimpleNamespace(value="generate_comparison")

        comparison_result = ComparisonResult.from_values(
            run_id_a="run-1",
            run_id_b="run-2",
            metric="faithfulness",
            mean_a=0.85,
            mean_b=0.90,
            p_value=0.03,
            effect_size=0.4,
        )

        mock_pipeline_adapter = MagicMock()
        mock_pipeline_adapter.run_comparison.return_value = pipeline_result
        mock_pipeline_adapter_cls.return_value = mock_pipeline_adapter
        mock_pipeline_factory.return_value = MagicMock()

        with patch(f"{COMPARE_COMMAND_MODULE}.StatisticalAnalysisAdapter") as mock_analysis_cls:
            mock_analysis = mock_analysis_cls.return_value
            mock_analysis.compare_runs.return_value = [comparison_result]

            result = runner.invoke(
                app,
                ["compare", "run-1", "run-2", "--db", str(tmp_path / "test.db")],
            )
        assert result.exit_code == 0
        assert "비교" in result.stdout or "comparison" in result.stdout.lower()


class TestCLIExport:
    """CLI export 명령 테스트."""

    def test_export_help(self):
        """export 명령 help 테스트."""
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0

    @patch(f"{HISTORY_COMMAND_MODULE}.build_storage_adapter")
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

    @patch(f"{HISTORY_COMMAND_MODULE}.build_storage_adapter")
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

    @patch(f"{EXPERIMENT_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{EXPERIMENT_COMMAND_MODULE}.ExperimentManager")
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

    @patch(f"{EXPERIMENT_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{EXPERIMENT_COMMAND_MODULE}.ExperimentManager")
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

    @patch(f"{EXPERIMENT_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{EXPERIMENT_COMMAND_MODULE}.ExperimentManager")
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

    @patch(f"{EXPERIMENT_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{EXPERIMENT_COMMAND_MODULE}.ExperimentManager")
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

    @patch(f"{EXPERIMENT_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{EXPERIMENT_COMMAND_MODULE}.ExperimentManager")
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

    @patch(f"{EXPERIMENT_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{EXPERIMENT_COMMAND_MODULE}.ExperimentManager")
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

    @patch(f"{EXPERIMENT_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{EXPERIMENT_COMMAND_MODULE}.ExperimentManager")
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

    @patch(f"{EXPERIMENT_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{EXPERIMENT_COMMAND_MODULE}.ExperimentManager")
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

    @patch(f"{EXPERIMENT_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{EXPERIMENT_COMMAND_MODULE}.ExperimentManager")
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

    @patch(f"{EXPERIMENT_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{EXPERIMENT_COMMAND_MODULE}.ExperimentManager")
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


class TestCLIAnalyzeNLP:
    """CLI analyze --nlp 명령 테스트."""

    def test_analyze_help_shows_nlp_option(self):
        """analyze 명령 help에 --nlp 옵션 표시."""
        result = runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "--nlp" in strip_ansi(result.stdout)

    @patch(f"{ANALYZE_COMMAND_MODULE}.build_storage_adapter")
    def test_analyze_run_not_found(self, mock_storage_cls, tmp_path):
        """존재하지 않는 run ID 테스트."""
        mock_storage = MagicMock()
        mock_storage.get_run.side_effect = KeyError("Run not found")
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            ["analyze", "nonexistent-run", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 1
        assert "찾을 수 없습니다" in result.stdout

    @patch(f"{ANALYZE_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.StatisticalAnalysisAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.MemoryCacheAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.AnalysisService")
    def test_analyze_without_nlp(
        self, mock_service_cls, mock_cache_cls, mock_stat_cls, mock_storage_cls, tmp_path
    ):
        """--nlp 없이 analyze 실행."""
        from datetime import datetime

        from evalvault.domain.entities.analysis import AnalysisBundle, StatisticalAnalysis

        # Mock run
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.results = [MagicMock()]

        mock_storage = MagicMock()
        mock_storage.get_run.return_value = mock_run
        mock_storage_cls.return_value = mock_storage

        # Mock analysis service
        mock_bundle = AnalysisBundle(
            run_id="run-123",
            statistical=StatisticalAnalysis(
                run_id="run-123",
                overall_pass_rate=0.8,
                created_at=datetime.now(),
            ),
        )
        mock_service = MagicMock()
        mock_service.analyze_run.return_value = mock_bundle
        mock_service_cls.return_value = mock_service

        result = runner.invoke(
            app,
            ["analyze", "run-123", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        # NLP adapter should not be created
        mock_service.analyze_run.assert_called_once()
        call_kwargs = mock_service.analyze_run.call_args[1]
        assert call_kwargs["include_nlp"] is False

    @patch(f"{ANALYZE_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.NLPAnalysisAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.Settings")
    @patch(f"{ANALYZE_COMMAND_MODULE}.StatisticalAnalysisAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.MemoryCacheAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.AnalysisService")
    def test_analyze_with_nlp(
        self,
        mock_service_cls,
        mock_cache_cls,
        mock_stat_cls,
        mock_settings_cls,
        mock_get_llm,
        mock_nlp_cls,
        mock_storage_cls,
        tmp_path,
    ):
        """--nlp 옵션으로 analyze 실행."""
        from datetime import datetime

        from evalvault.domain.entities.analysis import (
            AnalysisBundle,
            NLPAnalysis,
            QuestionType,
            QuestionTypeStats,
            StatisticalAnalysis,
            TextStats,
        )

        # Mock settings
        mock_settings = MagicMock()
        mock_settings.evalvault_profile = None
        mock_settings_cls.return_value = mock_settings

        # Mock run
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.results = [MagicMock()]

        mock_storage = MagicMock()
        mock_storage.get_run.return_value = mock_run
        mock_storage_cls.return_value = mock_storage

        # Mock NLP adapter
        mock_nlp = MagicMock()
        mock_nlp_cls.return_value = mock_nlp

        # Mock analysis service with NLP results
        mock_bundle = AnalysisBundle(
            run_id="run-123",
            statistical=StatisticalAnalysis(
                run_id="run-123",
                overall_pass_rate=0.8,
                created_at=datetime.now(),
            ),
            nlp=NLPAnalysis(
                run_id="run-123",
                question_stats=TextStats(
                    char_count=100,
                    word_count=20,
                    sentence_count=2,
                    avg_word_length=4.5,
                    unique_word_ratio=0.9,
                ),
                question_types=[
                    QuestionTypeStats(
                        question_type=QuestionType.FACTUAL,
                        count=5,
                        percentage=1.0,
                    )
                ],
            ),
        )
        mock_service = MagicMock()
        mock_service.analyze_run.return_value = mock_bundle
        mock_service_cls.return_value = mock_service

        result = runner.invoke(
            app,
            ["analyze", "run-123", "--nlp", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        # NLP adapter should be created
        mock_nlp_cls.assert_called_once()
        mock_service.analyze_run.assert_called_once()
        call_kwargs = mock_service.analyze_run.call_args[1]
        assert call_kwargs["include_nlp"] is True

    @patch(f"{ANALYZE_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.NLPAnalysisAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.get_llm_adapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.Settings")
    @patch(f"{ANALYZE_COMMAND_MODULE}.apply_profile")
    @patch(f"{ANALYZE_COMMAND_MODULE}.StatisticalAnalysisAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.MemoryCacheAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.AnalysisService")
    def test_analyze_with_nlp_and_profile(
        self,
        mock_service_cls,
        mock_cache_cls,
        mock_stat_cls,
        mock_apply_profile,
        mock_settings_cls,
        mock_get_llm,
        mock_nlp_cls,
        mock_storage_cls,
        tmp_path,
    ):
        """--nlp --profile 옵션으로 analyze 실행."""
        from datetime import datetime

        from evalvault.domain.entities.analysis import AnalysisBundle, StatisticalAnalysis

        # Mock settings
        mock_settings = MagicMock()
        mock_settings.evalvault_profile = None
        mock_settings_cls.return_value = mock_settings
        mock_apply_profile.return_value = mock_settings

        # Mock run
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.results = [MagicMock()]

        mock_storage = MagicMock()
        mock_storage.get_run.return_value = mock_run
        mock_storage_cls.return_value = mock_storage

        # Mock analysis service
        mock_bundle = AnalysisBundle(
            run_id="run-123",
            statistical=StatisticalAnalysis(
                run_id="run-123",
                overall_pass_rate=0.8,
                created_at=datetime.now(),
            ),
        )
        mock_service = MagicMock()
        mock_service.analyze_run.return_value = mock_bundle
        mock_service_cls.return_value = mock_service

        result = runner.invoke(
            app,
            ["analyze", "run-123", "--nlp", "--profile", "dev", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        mock_apply_profile.assert_called_once_with(mock_settings, "dev")


class TestCLIGate:
    """CLI gate 명령 테스트."""

    def test_gate_help(self):
        """gate 명령 help 테스트."""
        result = runner.invoke(app, ["gate", "--help"])
        assert result.exit_code == 0
        assert "threshold" in result.stdout.lower()
        assert "baseline" in result.stdout.lower()
        assert "format" in result.stdout.lower()

    @patch(f"{GATE_COMMAND_MODULE}.build_storage_adapter")
    def test_gate_run_not_found(self, mock_storage_cls, tmp_path):
        """존재하지 않는 run ID 테스트."""
        mock_storage = MagicMock()
        mock_storage.get_run.side_effect = KeyError("Run not found")
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            ["gate", "nonexistent-run", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 3
        assert "not found" in result.stdout.lower()

    @patch(f"{GATE_COMMAND_MODULE}.build_storage_adapter")
    def test_gate_pass(self, mock_storage_cls, tmp_path):
        """모든 메트릭 통과 테스트."""
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.metrics_evaluated = ["faithfulness", "context_precision"]
        mock_run.thresholds = {"faithfulness": 0.7, "context_precision": 0.7}
        mock_run.get_avg_score.side_effect = lambda m: 0.85 if m == "faithfulness" else 0.80
        mock_run.pass_rate = 0.9

        mock_storage = MagicMock()
        mock_storage.get_run.return_value = mock_run
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            ["gate", "run-123", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        assert "PASSED" in result.stdout or "passed" in result.stdout.lower()

    @patch(f"{GATE_COMMAND_MODULE}.build_storage_adapter")
    def test_gate_fail(self, mock_storage_cls, tmp_path):
        """메트릭 미달 테스트."""
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.metrics_evaluated = ["faithfulness"]
        mock_run.thresholds = {"faithfulness": 0.8}
        mock_run.get_avg_score.return_value = 0.65
        mock_run.pass_rate = 0.5

        mock_storage = MagicMock()
        mock_storage.get_run.return_value = mock_run
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            ["gate", "run-123", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 1
        assert "FAILED" in result.stdout or "failed" in result.stdout.lower()

    @patch(f"{GATE_COMMAND_MODULE}.build_storage_adapter")
    def test_gate_custom_threshold(self, mock_storage_cls, tmp_path):
        """커스텀 임계값 테스트."""
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.metrics_evaluated = ["faithfulness"]
        mock_run.thresholds = {"faithfulness": 0.7}
        mock_run.get_avg_score.return_value = 0.75
        mock_run.pass_rate = 0.7

        mock_storage = MagicMock()
        mock_storage.get_run.return_value = mock_run
        mock_storage_cls.return_value = mock_storage

        # 0.8 임계값 사용 시 실패해야 함
        result = runner.invoke(
            app,
            ["gate", "run-123", "-t", "faithfulness:0.8", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 1

    @patch(f"{GATE_COMMAND_MODULE}.build_storage_adapter")
    def test_gate_json_output(self, mock_storage_cls, tmp_path):
        """JSON 출력 테스트."""
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.metrics_evaluated = ["faithfulness"]
        mock_run.thresholds = {"faithfulness": 0.7}
        mock_run.get_avg_score.return_value = 0.85
        mock_run.pass_rate = 0.9

        mock_storage = MagicMock()
        mock_storage.get_run.return_value = mock_run
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            ["gate", "run-123", "--format", "json", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "passed"
        assert data["all_thresholds_passed"] is True

    @patch(f"{GATE_COMMAND_MODULE}.build_storage_adapter")
    def test_gate_github_actions_output(self, mock_storage_cls, tmp_path):
        """GitHub Actions 출력 테스트."""
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.metrics_evaluated = ["faithfulness"]
        mock_run.thresholds = {"faithfulness": 0.7}
        mock_run.get_avg_score.return_value = 0.85
        mock_run.pass_rate = 0.9

        mock_storage = MagicMock()
        mock_storage.get_run.return_value = mock_run
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            ["gate", "run-123", "--format", "github-actions", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        assert "::set-output" in result.stdout

    @patch(f"{GATE_COMMAND_MODULE}.build_storage_adapter")
    def test_gate_with_baseline(self, mock_storage_cls, tmp_path):
        """베이스라인 비교 테스트."""
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.metrics_evaluated = ["faithfulness"]
        mock_run.thresholds = {"faithfulness": 0.7}
        mock_run.get_avg_score.return_value = 0.85
        mock_run.pass_rate = 0.9

        mock_baseline = MagicMock()
        mock_baseline.run_id = "baseline-123"
        mock_baseline.metrics_evaluated = ["faithfulness"]
        mock_baseline.get_avg_score.return_value = 0.80

        mock_storage = MagicMock()
        mock_storage.get_run.side_effect = [mock_run, mock_baseline]
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            ["gate", "run-123", "--baseline", "baseline-123", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        assert "Baseline" in result.stdout or "baseline" in result.stdout.lower()

    @patch(f"{GATE_COMMAND_MODULE}.build_storage_adapter")
    def test_gate_regression_detected(self, mock_storage_cls, tmp_path):
        """회귀 감지 테스트."""
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.metrics_evaluated = ["faithfulness"]
        mock_run.thresholds = {"faithfulness": 0.7}
        mock_run.get_avg_score.return_value = 0.72  # 임계값은 통과
        mock_run.pass_rate = 0.7

        mock_baseline = MagicMock()
        mock_baseline.run_id = "baseline-123"
        mock_baseline.metrics_evaluated = ["faithfulness"]
        mock_baseline.get_avg_score.return_value = 0.85  # 베이스라인보다 0.13 하락

        mock_storage = MagicMock()
        mock_storage.get_run.side_effect = [mock_run, mock_baseline]
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            [
                "gate",
                "run-123",
                "--baseline",
                "baseline-123",
                "--fail-on-regression",
                "0.05",
                "--db",
                str(tmp_path / "test.db"),
            ],
        )
        assert result.exit_code == 2  # Regression detected
        assert "regression" in result.stdout.lower()

    @patch(f"{GATE_COMMAND_MODULE}.build_storage_adapter")
    def test_gate_baseline_not_found(self, mock_storage_cls, tmp_path):
        """베이스라인 미발견 테스트."""
        mock_run = MagicMock()
        mock_run.run_id = "run-123"

        mock_storage = MagicMock()
        mock_storage.get_run.side_effect = [mock_run, KeyError("Baseline not found")]
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            ["gate", "run-123", "--baseline", "nonexistent", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 3

    @patch(f"{GATE_COMMAND_MODULE}.build_storage_adapter")
    def test_gate_invalid_threshold_format(self, mock_storage_cls, tmp_path):
        """잘못된 임계값 형식 테스트."""
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.metrics_evaluated = ["faithfulness"]
        mock_run.thresholds = {"faithfulness": 0.7}

        mock_storage = MagicMock()
        mock_storage.get_run.return_value = mock_run
        mock_storage_cls.return_value = mock_storage

        result = runner.invoke(
            app,
            ["gate", "run-123", "-t", "invalid-format", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 1
        assert "Invalid threshold format" in result.stdout


class TestCLIAnalyzePlaybook:
    """CLI analyze --playbook 명령 테스트."""

    def test_analyze_help_shows_playbook_option(self):
        """analyze 명령 help에 --playbook 옵션 표시."""
        result = runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0
        stdout = strip_ansi(result.stdout)
        assert "--playbook" in stdout
        assert "--enable-llm" in stdout

    @patch(f"{ANALYZE_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.StatisticalAnalysisAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.MemoryCacheAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.AnalysisService")
    @patch(f"{ANALYZE_COMMAND_MODULE}._perform_playbook_analysis")
    def test_analyze_with_playbook(
        self,
        mock_playbook_analysis,
        mock_service_cls,
        mock_cache_cls,
        mock_stat_cls,
        mock_storage_cls,
        tmp_path,
    ):
        """--playbook 옵션으로 analyze 실행."""
        from datetime import datetime

        from evalvault.domain.entities.analysis import AnalysisBundle, StatisticalAnalysis
        from evalvault.domain.entities.improvement import ImprovementReport

        # Mock run
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.results = [MagicMock()]

        mock_storage = MagicMock()
        mock_storage.get_run.return_value = mock_run
        mock_storage_cls.return_value = mock_storage

        # Mock analysis service
        mock_bundle = AnalysisBundle(
            run_id="run-123",
            statistical=StatisticalAnalysis(
                run_id="run-123",
                overall_pass_rate=0.8,
                created_at=datetime.now(),
            ),
        )
        mock_service = MagicMock()
        mock_service.analyze_run.return_value = mock_bundle
        mock_service_cls.return_value = mock_service

        # Mock playbook analysis
        mock_report = ImprovementReport(run_id="run-123")
        mock_playbook_analysis.return_value = mock_report

        result = runner.invoke(
            app,
            ["analyze", "run-123", "--playbook", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        mock_playbook_analysis.assert_called_once()
        call_args = mock_playbook_analysis.call_args[0]
        assert call_args[0] == mock_run  # run
        assert call_args[1] is False  # enable_llm

    @patch(f"{ANALYZE_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.StatisticalAnalysisAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.MemoryCacheAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.AnalysisService")
    @patch(f"{ANALYZE_COMMAND_MODULE}._perform_playbook_analysis")
    def test_analyze_with_playbook_and_llm(
        self,
        mock_playbook_analysis,
        mock_service_cls,
        mock_cache_cls,
        mock_stat_cls,
        mock_storage_cls,
        tmp_path,
    ):
        """--playbook --enable-llm 옵션으로 analyze 실행."""
        from datetime import datetime

        from evalvault.domain.entities.analysis import AnalysisBundle, StatisticalAnalysis
        from evalvault.domain.entities.improvement import ImprovementReport

        # Mock run
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.results = [MagicMock()]

        mock_storage = MagicMock()
        mock_storage.get_run.return_value = mock_run
        mock_storage_cls.return_value = mock_storage

        # Mock analysis service
        mock_bundle = AnalysisBundle(
            run_id="run-123",
            statistical=StatisticalAnalysis(
                run_id="run-123",
                overall_pass_rate=0.8,
                created_at=datetime.now(),
            ),
        )
        mock_service = MagicMock()
        mock_service.analyze_run.return_value = mock_bundle
        mock_service_cls.return_value = mock_service

        # Mock playbook analysis
        mock_report = ImprovementReport(run_id="run-123")
        mock_playbook_analysis.return_value = mock_report

        result = runner.invoke(
            app,
            ["analyze", "run-123", "--playbook", "--enable-llm", "--db", str(tmp_path / "test.db")],
        )
        assert result.exit_code == 0
        mock_playbook_analysis.assert_called_once()
        call_args = mock_playbook_analysis.call_args[0]
        assert call_args[1] is True  # enable_llm

    @patch(f"{ANALYZE_COMMAND_MODULE}.build_storage_adapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.StatisticalAnalysisAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.MemoryCacheAdapter")
    @patch(f"{ANALYZE_COMMAND_MODULE}.AnalysisService")
    def test_analyze_without_playbook(
        self,
        mock_service_cls,
        mock_cache_cls,
        mock_stat_cls,
        mock_storage_cls,
        tmp_path,
    ):
        """--playbook 없이 analyze 실행 시 플레이북 분석 안함."""
        from datetime import datetime

        from evalvault.domain.entities.analysis import AnalysisBundle, StatisticalAnalysis

        # Mock run
        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.results = [MagicMock()]

        mock_storage = MagicMock()
        mock_storage.get_run.return_value = mock_run
        mock_storage_cls.return_value = mock_storage

        # Mock analysis service
        mock_bundle = AnalysisBundle(
            run_id="run-123",
            statistical=StatisticalAnalysis(
                run_id="run-123",
                overall_pass_rate=0.8,
                created_at=datetime.now(),
            ),
        )
        mock_service = MagicMock()
        mock_service.analyze_run.return_value = mock_bundle
        mock_service_cls.return_value = mock_service

        with patch(f"{ANALYZE_COMMAND_MODULE}._perform_playbook_analysis") as mock_playbook:
            result = runner.invoke(
                app,
                ["analyze", "run-123", "--db", str(tmp_path / "test.db")],
            )
            assert result.exit_code == 0
            mock_playbook.assert_not_called()


class TestPipelineCommands:
    """Pipeline 서브커맨드 테스트."""

    @patch("evalvault.adapters.outbound.analysis.SummaryReportModule")
    @patch("evalvault.adapters.outbound.analysis.StatisticalAnalyzerModule")
    @patch("evalvault.adapters.outbound.analysis.DataLoaderModule")
    @patch(f"{PIPELINE_COMMAND_MODULE}.build_storage_adapter")
    @patch("evalvault.domain.services.pipeline_orchestrator.AnalysisPipelineService")
    def test_pipeline_analyze_saves_statistical_analysis(
        self,
        mock_service_cls,
        mock_storage_cls,
        mock_data_loader_cls,
        mock_stat_module_cls,
        mock_summary_module_cls,
        tmp_path,
    ):
        """pipeline analyze 실행 시 통계 분석을 저장한다."""
        from evalvault.domain.entities.analysis import StatisticalAnalysis
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            NodeExecutionStatus,
            NodeResult,
            PipelineResult,
        )

        mock_storage = MagicMock()
        mock_storage.save_analysis.return_value = "analysis-123"
        mock_storage_cls.return_value = mock_storage

        mock_data_loader_cls.return_value = MagicMock(module_id="data_loader")
        mock_stat_module_cls.return_value = MagicMock(module_id="statistical_analyzer")
        mock_summary_module_cls.return_value = MagicMock(module_id="summary_report")

        pipeline_result = PipelineResult(
            pipeline_id="pipe-1",
            intent=AnalysisIntent.GENERATE_SUMMARY,
        )
        stats_output = {"analysis": StatisticalAnalysis(run_id="run-77")}
        pipeline_result.add_node_result(
            NodeResult(
                node_id="statistical_analyzer",
                status=NodeExecutionStatus.COMPLETED,
                output=stats_output,
            )
        )
        pipeline_result.mark_complete(
            final_output={"summary_report": {"report": "OK"}}, total_duration_ms=12
        )

        mock_service = MagicMock()
        mock_service.get_intent.return_value = AnalysisIntent.GENERATE_SUMMARY
        mock_service.analyze.return_value = pipeline_result
        mock_service_cls.return_value = mock_service

        result = runner.invoke(
            app,
            [
                "pipeline",
                "analyze",
                "요약해줘",
                "--db",
                str(tmp_path / "pipeline.db"),
                "--run",
                "run-77",
            ],
        )

        assert result.exit_code == 0
        mock_service.register_module.assert_any_call(mock_data_loader_cls.return_value)
        mock_storage.save_analysis.assert_called_once()


class TestPerformPlaybookAnalysis:
    """_perform_playbook_analysis 함수 테스트."""

    def test_perform_playbook_analysis_creates_report(self):
        """플레이북 분석이 리포트를 생성하는지 테스트."""
        from evalvault.adapters.inbound.cli import _perform_playbook_analysis
        from evalvault.domain.entities.improvement import ImprovementReport

        mock_run = MagicMock()
        mock_run.run_id = "run-123"
        mock_run.results = []
        mock_run.metrics_evaluated = ["faithfulness"]
        mock_run.thresholds = {"faithfulness": 0.7}
        mock_run.get_avg_score.return_value = 0.6

        # Call the function - it should complete without error
        result = _perform_playbook_analysis(mock_run, enable_llm=False, profile=None)

        assert isinstance(result, ImprovementReport)
        assert result.run_id == "run-123"


class TestDisplayImprovementReport:
    """_display_improvement_report 함수 테스트."""

    def test_display_improvement_report_empty(self, capsys):
        """빈 리포트 표시."""
        from evalvault.adapters.inbound.cli import _display_improvement_report
        from evalvault.domain.entities.improvement import ImprovementReport

        report = ImprovementReport(
            run_id="run-123",
            total_test_cases=10,
            metric_scores={"faithfulness": 0.85},
            metric_gaps={},
            guides=[],
        )

        _display_improvement_report(report)
        # No exception means success


class TestCLIPhoenixUtilities:
    """Phoenix helper CLI tests."""

    @pytest.fixture
    def fake_dataset(self):
        class FakeDataset:
            def __init__(self):
                self.id = "ds_fake"
                self.name = "insurance-ko"
                self.version_id = "v1"
                self.description = "desc"
                self.examples = [
                    {
                        "example_id": "ex-1",
                        "input": {"question": "무엇인가?", "contexts": ["context A"]},
                        "output": {"answer": "답변"},
                        "metadata": {"topic": "faq"},
                    },
                    {
                        "example_id": "ex-2",
                        "input": {"question": "두번째", "contexts": ["context B"]},
                        "output": {"answer": "다른 답변"},
                        "metadata": {"topic": "notice"},
                    },
                ]

        return FakeDataset()

    @pytest.mark.skipif(not HAS_SKLEARN, reason=SKLEARN_SKIP_REASON)
    @pytest.mark.requires_openai
    @patch("evalvault.adapters.inbound.cli.commands.phoenix._import_phoenix_client")
    def test_phoenix_export_embeddings_csv(self, mock_client_factory, fake_dataset, tmp_path):
        mock_client = MagicMock()
        mock_client.datasets.get_dataset.return_value = fake_dataset

        class FakeClient:
            def __init__(self, *args, **kwargs):
                self.datasets = mock_client.datasets

        mock_client_factory.return_value = FakeClient

        output = tmp_path / "embeddings.csv"
        result = runner.invoke(
            app,
            [
                "phoenix",
                "export-embeddings",
                "--dataset",
                fake_dataset.id,
                "--output",
                str(output),
                "--format",
                "csv",
            ],
        )

        assert result.exit_code == 0
        assert output.exists()
        rows = output.read_text(encoding="utf-8").splitlines()
        assert len(rows) > 1  # header + rows

    def test_phoenix_prompt_link_updates_manifest(self, tmp_path):
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("prompt content", encoding="utf-8")
        manifest = tmp_path / "prompt_manifest.json"

        result = runner.invoke(
            app,
            [
                "phoenix",
                "prompt-link",
                str(prompt_file),
                "--prompt-id",
                "prompt-1",
                "--experiment-id",
                "exp-42",
                "--notes",
                "baseline",
                "--manifest",
                str(manifest),
            ],
        )

        assert result.exit_code == 0
        data = json.loads(manifest.read_text(encoding="utf-8"))
        normalized = prompt_file.resolve().as_posix()
        assert normalized in data["prompts"]
        entry = data["prompts"][normalized]
        assert entry["phoenix_prompt_id"] == "prompt-1"
        assert entry["phoenix_experiment_id"] == "exp-42"
        assert entry["notes"] == "baseline"

    def test_phoenix_prompt_diff_outputs_json(self, tmp_path):
        prompt_file = tmp_path / "prompt.txt"
        manifest = tmp_path / "prompt_manifest.json"
        prompt_file.write_text("v1", encoding="utf-8")

        # Link initial version
        link_result = runner.invoke(
            app,
            [
                "phoenix",
                "prompt-link",
                str(prompt_file),
                "--prompt-id",
                "prompt-1",
                "--manifest",
                str(manifest),
            ],
        )
        assert link_result.exit_code == 0

        # Modify prompt to trigger diff
        prompt_file.write_text("v2 updated", encoding="utf-8")

        diff_result = runner.invoke(
            app,
            [
                "phoenix",
                "prompt-diff",
                str(prompt_file),
                "--manifest",
                str(manifest),
                "--format",
                "json",
            ],
        )

        assert diff_result.exit_code == 0
        payload = json.loads(diff_result.stdout.strip())
        assert payload[0]["status"] == "modified"
        assert payload[0]["diff"]

    def test_display_improvement_report_with_guides(self, capsys):
        """가이드가 있는 리포트 표시."""
        from evalvault.adapters.inbound.cli import _display_improvement_report
        from evalvault.domain.entities.improvement import (
            EvidenceSource,
            ImprovementAction,
            ImprovementEvidence,
            ImprovementPriority,
            ImprovementReport,
            PatternEvidence,
            PatternType,
            RAGComponent,
            RAGImprovementGuide,
        )

        # Create proper evidence structure
        pattern_evidence = PatternEvidence(
            pattern_type=PatternType.HALLUCINATION,
            affected_count=5,
            total_count=20,
        )

        evidence = ImprovementEvidence(
            target_metric="faithfulness",
            detected_patterns=[pattern_evidence],
            total_failures=5,
            avg_score_failures=0.45,
            avg_score_passes=0.85,
            analysis_methods=[EvidenceSource.RULE_BASED],
        )

        guide = RAGImprovementGuide(
            component=RAGComponent.GENERATOR,
            target_metrics=["faithfulness"],
            priority=ImprovementPriority.P1_HIGH,
            evidence=evidence,
            actions=[
                ImprovementAction(
                    title="Temperature 감소",
                    description="LLM의 창의성을 낮춤",
                    expected_improvement=0.08,
                    effort=EffortLevel.LOW,
                )
            ],
            verification_command="evalvault run data.csv --metrics faithfulness",
        )

        report = ImprovementReport(
            run_id="run-123",
            total_test_cases=20,
            metric_scores={"faithfulness": 0.65},
            metric_gaps={"faithfulness": 0.05},
            guides=[guide],
            analysis_methods_used=[EvidenceSource.RULE_BASED],
        )

        _display_improvement_report(report)
        # No exception means success


class TestRunHelperFunctions:
    """run.py 헬퍼 함수 테스트."""

    def test_resolve_thresholds_prefers_dataset_values(self):
        dataset = Dataset(
            name="demo",
            version="1.0.0",
            test_cases=[],
            thresholds={"faithfulness": 0.9},
        )
        resolved = run_command_module._resolve_thresholds(
            ["faithfulness", "answer_relevancy"],
            dataset,
        )
        assert resolved["faithfulness"] == 0.9
        assert resolved["answer_relevancy"] == 0.7

    def test_resolve_thresholds_applies_profile(self):
        dataset = Dataset(
            name="demo",
            version="1.0.0",
            test_cases=[],
            thresholds={"summary_score": 0.2},
        )
        resolved = run_command_module._resolve_thresholds(
            ["summary_score", "summary_faithfulness"],
            dataset,
            profile="summary",
        )
        assert (
            resolved["summary_score"]
            == run_command_module.run_helpers.SUMMARY_RECOMMENDED_THRESHOLDS["summary_score"]
        )

    def test_resolve_thresholds_rejects_unknown_profile(self):
        dataset = Dataset(
            name="demo",
            version="1.0.0",
            test_cases=[],
        )
        with pytest.raises(ValueError, match="Unknown threshold profile"):
            run_command_module._resolve_thresholds(
                ["faithfulness"],
                dataset,
                profile="invalid",
            )

    def test_merge_evaluation_runs_accumulates_tokens_and_cost(self):
        run_a = EvaluationRun(
            dataset_name="demo",
            dataset_version="1",
            model_name="mock",
            metrics_evaluated=["faithfulness"],
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-1",
                    metrics=[MetricScore(name="faithfulness", score=0.8, threshold=0.7)],
                )
            ],
            total_tokens=10,
            total_cost_usd=0.3,
        )
        run_b = EvaluationRun(
            dataset_name="demo",
            dataset_version="1",
            model_name="mock",
            metrics_evaluated=["faithfulness"],
            thresholds={"faithfulness": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-2",
                    metrics=[MetricScore(name="faithfulness", score=0.6, threshold=0.7)],
                )
            ],
            total_tokens=5,
            total_cost_usd=0.2,
        )

        merged = run_command_module._merge_evaluation_runs(
            None,
            run_a,
            dataset_name="demo",
            dataset_version="1",
            metrics=["faithfulness"],
            thresholds={"faithfulness": 0.7},
        )
        merged = run_command_module._merge_evaluation_runs(
            merged,
            run_b,
            dataset_name="demo",
            dataset_version="1",
            metrics=["faithfulness"],
            thresholds={"faithfulness": 0.7},
        )

        assert merged.total_test_cases == 2
        assert merged.total_tokens == 15
        assert merged.total_cost_usd == pytest.approx(0.5)
        assert merged.thresholds["faithfulness"] == 0.7

    @pytest.mark.asyncio
    async def test_evaluate_streaming_run_merges_chunks(self, tmp_path):
        dataset_file = tmp_path / "cases.csv"
        dataset_file.write_text(
            'id,question,answer,contexts\n1,"Q1","A1","[\\"ctx1\\"]"\n2,"Q2","A2","[\\"ctx2\\"]"\n',
            encoding="utf-8",
        )

        template = Dataset(
            name="stream-ds",
            version="stream",
            test_cases=[],
            metadata={"source": "tmp"},
            source_file=str(dataset_file),
            thresholds={},
        )

        chunk_run_1 = EvaluationRun(
            dataset_name="stream-ds",
            dataset_version="stream",
            model_name="mock",
            metrics_evaluated=["faithfulness"],
            thresholds={"faithfulness": 0.6},
            results=[
                TestCaseResult(
                    test_case_id="tc-1",
                    metrics=[MetricScore(name="faithfulness", score=0.5, threshold=0.6)],
                )
            ],
            total_tokens=10,
            total_cost_usd=0.1,
        )
        chunk_run_2 = EvaluationRun(
            dataset_name="stream-ds",
            dataset_version="stream",
            model_name="mock",
            metrics_evaluated=["faithfulness"],
            thresholds={"faithfulness": 0.6},
            results=[
                TestCaseResult(
                    test_case_id="tc-2",
                    metrics=[MetricScore(name="faithfulness", score=0.7, threshold=0.6)],
                )
            ],
            total_tokens=12,
            total_cost_usd=0.2,
        )

        evaluator = MagicMock()
        evaluator.evaluate = AsyncMock(side_effect=[chunk_run_1, chunk_run_2])
        llm_adapter = MagicMock()

        result = await run_command_module._evaluate_streaming_run(
            dataset_path=dataset_file,
            dataset_template=template,
            metrics=["faithfulness"],
            thresholds={"faithfulness": 0.6},
            evaluator=evaluator,
            llm=llm_adapter,
            chunk_size=1,
            parallel=False,
            batch_size=5,
        )

        assert evaluator.evaluate.await_count == 2
        assert result.dataset_name == "stream-ds"
        assert result.total_test_cases == 2
        assert result.total_tokens == 22
        assert result.total_cost_usd == pytest.approx(0.3)
        assert result.thresholds["faithfulness"] == 0.6

    def test_build_streaming_dataset_template_for_json(self, tmp_path):
        dataset_file = tmp_path / "dataset.json"
        dataset_file.write_text(
            json.dumps(
                {
                    "name": "insurance-ko",
                    "version": "1.2.3",
                    "description": "desc",
                    "thresholds": {"faithfulness": 0.9},
                    "test_cases": [],
                }
            ),
            encoding="utf-8",
        )

        ds = run_command_module._build_streaming_dataset_template(dataset_file)
        assert ds.name == "insurance-ko"
        assert ds.version == "1.2.3"
        assert ds.thresholds["faithfulness"] == 0.9
        assert ds.metadata.get("description") == "desc"

    def test_build_streaming_dataset_template_for_csv(self, tmp_path):
        dataset_file = tmp_path / "dataset.csv"
        dataset_file.write_text(
            "id,question,answer,contexts,threshold_faithfulness\ntc-001,hi,ok,[],0.85\n",
            encoding="utf-8",
        )

        ds = run_command_module._build_streaming_dataset_template(dataset_file)
        assert ds.name == dataset_file.stem
        assert ds.version == "stream"
        assert ds.thresholds["faithfulness"] == 0.85

    def test_is_oss_open_model(self):
        assert run_command_module._is_oss_open_model("gpt-oss-safeguard:20b")
        assert not run_command_module._is_oss_open_model("gpt-4o")
        assert not run_command_module._is_oss_open_model(None)
