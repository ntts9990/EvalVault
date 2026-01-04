"""Unit tests for settings configuration."""

from evalvault.config.model_config import reset_model_config
from evalvault.config.settings import get_settings, reset_settings


def test_get_settings_applies_profile(monkeypatch) -> None:
    reset_settings()
    reset_model_config()

    monkeypatch.setenv("EVALVAULT_PROFILE", "dev")

    settings = get_settings()

    assert settings.evalvault_profile == "dev"
    assert settings.llm_provider == "ollama"
    assert settings.ollama_model == "gemma3:1b"
    assert settings.ollama_embedding_model == "qwen3-embedding:0.6b"


def test_get_settings_reads_env(monkeypatch) -> None:
    reset_settings()
    reset_model_config()

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    settings = get_settings()

    assert settings.openai_api_key == "sk-test-key"


def test_reset_settings_clears_cache(monkeypatch) -> None:
    reset_settings()
    reset_model_config()

    monkeypatch.delenv("EVALVAULT_PROFILE", raising=False)
    settings = get_settings()
    reset_settings()
    reset_model_config()
    settings_after_reset = get_settings()

    assert settings is not settings_after_reset
