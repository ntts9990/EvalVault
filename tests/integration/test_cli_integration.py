"""CLI integration tests for --profile option.

프로필 기반 모델 설정 테스트:
- dev: gemma3:1b (Ollama)
- prod: gpt-oss-safeguard:20b (Ollama)
- openai: gpt-5-mini (OpenAI)
"""

import json
import os
from importlib.metadata import version as get_version
from pathlib import Path

import pytest
from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app
from evalvault.config.model_config import reset_model_config
from evalvault.config.settings import Settings, apply_profile, reset_settings

runner = CliRunner()


class TestCLIProfileIntegration:
    """CLI 프로필 통합 테스트."""

    @pytest.fixture(autouse=True)
    def reset_caches(self):
        """각 테스트 전 캐시 초기화."""
        reset_settings()
        reset_model_config()
        yield
        reset_settings()
        reset_model_config()

    def test_config_shows_profile_info(self):
        """config 명령이 프로필 정보를 표시하는지 테스트."""
        result = runner.invoke(app, ["config"])

        assert result.exit_code == 0
        # Profile section should be present
        assert "Profiles" in result.stdout or "Profile" in result.stdout

    def test_config_shows_available_profiles(self):
        """config 명령이 사용 가능한 프로필을 표시하는지 테스트."""
        result = runner.invoke(app, ["config"])

        assert result.exit_code == 0
        # At least one of the default profiles should be shown
        output_lower = result.stdout.lower()
        assert any(p in output_lower for p in ["dev", "prod", "openai"])

    def test_run_help_shows_profile_option(self):
        """run --help가 --profile 옵션을 표시하는지 테스트."""
        result = runner.invoke(app, ["run", "--help"])

        assert result.exit_code == 0
        assert "--profile" in result.stdout or "-p" in result.stdout

    def test_metrics_command_still_works(self):
        """metrics 명령이 여전히 작동하는지 테스트."""
        result = runner.invoke(app, ["metrics"])

        assert result.exit_code == 0
        assert "faithfulness" in result.stdout.lower()
        assert "answer_relevancy" in result.stdout.lower()

    def test_version_command_still_works(self):
        """--version이 여전히 작동하는지 테스트."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        expected_version = get_version("evalvault")
        assert expected_version in result.stdout

    @pytest.mark.skipif(
        bool(os.environ.get("CI")),
        reason="CI 환경에서는 Ollama 서버가 없습니다.",
    )
    def test_run_with_retriever_populates_contexts(self, tmp_path: Path):
        dataset_path = tmp_path / "dataset.json"
        dataset_path.write_text(
            json.dumps(
                {
                    "name": "retriever-demo",
                    "version": "1.0.0",
                    "test_cases": [
                        {
                            "id": "tc-1",
                            "question": "보험료는 얼마인가요?",
                            "answer": "보험료는 15만원입니다.",
                            "contexts": [],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        docs_path = tmp_path / "docs.json"
        docs_path.write_text(
            json.dumps(
                {
                    "documents": [
                        {"doc_id": "doc-1", "content": "보험료는 월 15만원입니다."},
                        {"doc_id": "doc-2", "content": "보장금액은 1억원입니다."},
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            [
                "run",
                str(dataset_path),
                "--profile",
                "dev",
                "--metrics",
                "faithfulness",
                "--retriever",
                "bm25",
                "--retriever-docs",
                str(docs_path),
                "--retriever-top-k",
                "1",
            ],
        )

        assert result.exit_code == 0
        assert "Applied bm25 retriever" in result.output


class TestApplyProfileIntegration:
    """apply_profile 함수 통합 테스트."""

    @pytest.fixture(autouse=True)
    def reset_caches(self):
        """각 테스트 전 캐시 초기화."""
        reset_settings()
        reset_model_config()
        yield
        reset_settings()
        reset_model_config()

    def test_apply_dev_profile(self):
        """dev 프로필 적용 테스트."""
        settings = Settings()
        settings = apply_profile(settings, "dev")

        assert settings.llm_provider == "ollama"
        assert settings.ollama_model == "gemma3:1b"
        assert settings.ollama_embedding_model == "qwen3-embedding:0.6b"

    def test_apply_prod_profile(self):
        """prod 프로필 적용 테스트."""
        settings = Settings()
        settings = apply_profile(settings, "prod")

        assert settings.llm_provider == "ollama"
        assert settings.ollama_model == "gpt-oss-safeguard:20b"
        assert settings.ollama_think_level == "medium"
        assert settings.ollama_embedding_model == "qwen3-embedding:8b"

    def test_apply_openai_profile(self):
        """openai 프로필 적용 테스트."""
        settings = Settings()
        settings = apply_profile(settings, "openai")

        assert settings.llm_provider == "openai"
        assert settings.openai_model == "gpt-5-mini"
        assert settings.openai_embedding_model == "text-embedding-3-small"

    def test_env_settings_preserved_after_profile(self):
        """프로필 적용 후 .env 인프라 설정이 유지되는지 테스트."""
        settings = Settings()
        original_base_url = settings.ollama_base_url
        original_timeout = settings.ollama_timeout

        settings = apply_profile(settings, "dev")

        # Infrastructure settings from .env should be preserved
        assert settings.ollama_base_url == original_base_url
        assert settings.ollama_timeout == original_timeout

    def test_profile_not_found_raises_error(self):
        """존재하지 않는 프로필은 ValueError를 발생."""
        settings = Settings()

        # apply_profile should raise ValueError for unknown profiles
        with pytest.raises(ValueError, match="Unknown profile"):
            apply_profile(settings, "nonexistent_profile_12345")
