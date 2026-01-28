"""Unit tests for model configuration.

모델명 참조:
  - 개발 LLM: gemma3:1b
  - 운영 LLM: gpt-oss-safeguard:20b
  - 개발 임베딩: qwen3-embedding:0.6b
  - 운영 임베딩: qwen3-embedding:8b
  - OpenAI LLM: gpt-5-mini
  - OpenAI 임베딩: text-embedding-3-small
"""

from pathlib import Path

import pytest
import yaml

from evalvault.config.model_config import (
    EmbeddingConfig,
    LLMConfig,
    ModelConfig,
    ProfileConfig,
    load_model_config,
)


class TestModelConfig:
    """ModelConfig 단위 테스트."""

    @pytest.fixture
    def sample_config_data(self) -> dict:
        """샘플 설정 데이터.

        Note: 인프라 설정(base_url, timeout 등)은 .env에서 관리합니다.
        models.yaml은 모델 프로필만 정의합니다.
        """
        return {
            "profiles": {
                "dev": {
                    "description": "개발용",
                    "llm": {
                        "provider": "ollama",
                        "model": "gemma3:1b",
                    },
                    "embedding": {
                        "provider": "ollama",
                        "model": "qwen3-embedding:0.6b",
                    },
                },
                "prod": {
                    "description": "운영용",
                    "llm": {
                        "provider": "ollama",
                        "model": "gpt-oss-safeguard:20b",
                        "options": {"think_level": "medium"},
                    },
                    "embedding": {
                        "provider": "ollama",
                        "model": "qwen3-embedding:8b",
                    },
                },
                "openai": {
                    "description": "OpenAI",
                    "llm": {
                        "provider": "openai",
                        "model": "gpt-5-mini",
                    },
                    "embedding": {
                        "provider": "openai",
                        "model": "text-embedding-3-small",
                    },
                },
            },
        }

    @pytest.fixture
    def config_file(self, sample_config_data, tmp_path) -> Path:
        """임시 설정 파일 생성."""
        config_path = tmp_path / "models.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config_data, f)
        return config_path

    def test_load_config_from_file(self, config_file):
        """파일에서 설정 로드 테스트."""
        config = load_model_config(config_file)

        assert isinstance(config, ModelConfig)
        assert "dev" in config.profiles
        assert "prod" in config.profiles
        assert "openai" in config.profiles

    def test_get_profile_dev(self, config_file):
        """dev 프로필 조회 테스트."""
        config = load_model_config(config_file)
        profile = config.get_profile("dev")

        assert profile.llm.provider == "ollama"
        assert profile.llm.model == "gemma3:1b"
        assert profile.embedding.provider == "ollama"
        assert profile.embedding.model == "qwen3-embedding:0.6b"

    def test_get_profile_prod(self, config_file):
        """prod 프로필 조회 테스트."""
        config = load_model_config(config_file)
        profile = config.get_profile("prod")

        assert profile.llm.provider == "ollama"
        assert profile.llm.model == "gpt-oss-safeguard:20b"
        assert profile.llm.options == {"think_level": "medium"}
        assert profile.embedding.model == "qwen3-embedding:8b"

    def test_get_profile_openai(self, config_file):
        """openai 프로필 조회 테스트."""
        config = load_model_config(config_file)
        profile = config.get_profile("openai")

        assert profile.llm.provider == "openai"
        assert profile.llm.model == "gpt-5-mini"
        assert profile.embedding.model == "text-embedding-3-small"

    def test_get_profile_not_found(self, config_file):
        """존재하지 않는 프로필 조회 테스트."""
        config = load_model_config(config_file)

        with pytest.raises(KeyError, match="not found"):
            config.get_profile("nonexistent")

    def test_load_config_file_not_found(self):
        """설정 파일 없을 때 에러 테스트."""
        with pytest.raises(FileNotFoundError):
            load_model_config("/nonexistent/path/models.yaml")


class TestLLMConfig:
    """LLMConfig 단위 테스트."""

    def test_ollama_llm_config(self):
        """Ollama LLM 설정 생성 테스트."""
        config = LLMConfig(
            provider="ollama",
            model="gemma3:1b",
        )

        assert config.provider == "ollama"
        assert config.model == "gemma3:1b"
        assert config.options is None

    def test_ollama_llm_config_with_options(self):
        """옵션이 있는 Ollama LLM 설정 테스트."""
        config = LLMConfig(
            provider="ollama",
            model="gpt-oss-safeguard:20b",
            options={"think_level": "medium"},
        )

        assert config.model == "gpt-oss-safeguard:20b"
        assert config.options is not None
        assert config.options["think_level"] == "medium"

    def test_openai_llm_config(self):
        """OpenAI LLM 설정 테스트."""
        config = LLMConfig(
            provider="openai",
            model="gpt-5-mini",
        )

        assert config.provider == "openai"
        assert config.model == "gpt-5-mini"


class TestEmbeddingConfig:
    """EmbeddingConfig 단위 테스트."""

    def test_ollama_embedding_config(self):
        """Ollama 임베딩 설정 테스트."""
        config = EmbeddingConfig(
            provider="ollama",
            model="qwen3-embedding:0.6b",
        )

        assert config.provider == "ollama"
        assert config.model == "qwen3-embedding:0.6b"

    def test_openai_embedding_config(self):
        """OpenAI 임베딩 설정 테스트."""
        config = EmbeddingConfig(
            provider="openai",
            model="text-embedding-3-small",
        )

        assert config.provider == "openai"
        assert config.model == "text-embedding-3-small"


class TestProfileConfig:
    """ProfileConfig 단위 테스트."""

    def test_create_profile(self):
        """프로필 생성 테스트."""
        profile = ProfileConfig(
            description="테스트 프로필",
            llm=LLMConfig(provider="ollama", model="gemma3:1b"),
            embedding=EmbeddingConfig(provider="ollama", model="qwen3-embedding:0.6b"),
        )

        assert profile.description == "테스트 프로필"
        assert profile.llm.model == "gemma3:1b"
        assert profile.embedding.model == "qwen3-embedding:0.6b"
