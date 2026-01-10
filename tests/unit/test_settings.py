"""Unit tests for settings configuration."""

from pathlib import Path

from evalvault.config.model_config import reset_model_config
from evalvault.config.settings import Settings, get_settings, reset_settings


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


def test_settings_resolves_db_path_from_repo_root(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.delenv("EVALVAULT_DB_PATH", raising=False)
    monkeypatch.delenv("EVALVAULT_MEMORY_DB_PATH", raising=False)
    monkeypatch.chdir(repo_root / "docs")

    settings = Settings()

    expected_db = (repo_root / "data/db/evalvault.db").resolve()
    expected_memory_db = (repo_root / "data/db/evalvault_memory.db").resolve()

    assert settings.evalvault_db_path == str(expected_db)
    assert settings.evalvault_memory_db_path == str(expected_memory_db)


def test_settings_resolves_db_path_from_cwd_when_no_repo(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("EVALVAULT_DB_PATH", raising=False)
    monkeypatch.delenv("EVALVAULT_MEMORY_DB_PATH", raising=False)
    monkeypatch.chdir(tmp_path)

    settings = Settings()

    expected_db = (tmp_path / "data/db/evalvault.db").resolve()
    expected_memory_db = (tmp_path / "data/db/evalvault_memory.db").resolve()

    assert settings.evalvault_db_path == str(expected_db)
    assert settings.evalvault_memory_db_path == str(expected_memory_db)
