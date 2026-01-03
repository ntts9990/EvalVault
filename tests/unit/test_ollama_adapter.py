"""Unit tests for OllamaAdapter."""

from unittest.mock import MagicMock, patch

import pytest

from evalvault.adapters.outbound.llm import OllamaAdapter, get_llm_adapter
from evalvault.config.settings import Settings


class TestOllamaAdapter:
    """OllamaAdapter 단위 테스트."""

    @pytest.fixture(autouse=True)
    def mock_components(self):
        with (
            patch(
                "evalvault.adapters.outbound.llm.ollama_adapter.ThinkingTokenTrackingAsyncOpenAI"
            ) as mock_client,
            patch(
                "evalvault.adapters.outbound.llm.ollama_adapter.create_instructor_llm"
            ) as mock_llm_factory,
            patch(
                "evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings"
            ) as mock_embeddings,
            patch("evalvault.adapters.outbound.llm.ollama_adapter.AsyncOpenAI") as mock_async,
        ):
            mock_client.return_value = MagicMock()
            mock_llm_factory.return_value = MagicMock()
            mock_embeddings.return_value = MagicMock()
            mock_async.return_value = MagicMock()
            yield {
                "client": mock_client,
                "llm_factory": mock_llm_factory,
                "embeddings": mock_embeddings,
                "async_client": mock_async,
            }

    @pytest.fixture
    def dev_settings(self) -> Settings:
        settings = Settings()
        settings.llm_provider = "ollama"
        settings.ollama_model = "gemma3:1b"
        settings.ollama_embedding_model = "qwen3-embedding:0.6b"
        settings.ollama_base_url = "http://localhost:11434"
        settings.ollama_timeout = 120
        return settings

    @pytest.fixture
    def prod_settings(self) -> Settings:
        settings = Settings()
        settings.llm_provider = "ollama"
        settings.ollama_model = "gpt-oss-safeguard:20b"
        settings.ollama_embedding_model = "qwen3-embedding:8b"
        settings.ollama_base_url = "http://localhost:11434"
        settings.ollama_timeout = 180
        settings.ollama_think_level = "medium"
        return settings

    def test_adapter_initialization_dev(self, mock_components, dev_settings):
        adapter = OllamaAdapter(dev_settings)

        assert adapter.get_model_name() == "ollama/gemma3:1b"
        assert adapter.get_embedding_model_name() == "qwen3-embedding:0.6b"
        assert adapter.get_base_url() == "http://localhost:11434"
        assert adapter.get_think_level() is None

    def test_adapter_initialization_prod(self, mock_components, prod_settings):
        adapter = OllamaAdapter(prod_settings)

        assert adapter.get_model_name() == "ollama/gpt-oss-safeguard:20b"
        assert adapter.get_embedding_model_name() == "qwen3-embedding:8b"
        assert adapter.get_think_level() == "medium"

    def test_as_ragas_llm(self, mock_components, dev_settings):
        mock_llm = MagicMock()
        mock_components["llm_factory"].return_value = mock_llm

        adapter = OllamaAdapter(dev_settings)
        assert adapter.as_ragas_llm() == mock_llm
        mock_components["llm_factory"].assert_called_once()

    def test_as_ragas_embeddings(self, mock_components, dev_settings):
        mock_embedding = MagicMock()
        mock_components["embeddings"].return_value = mock_embedding

        adapter = OllamaAdapter(dev_settings)
        assert adapter.as_ragas_embeddings() == mock_embedding

    def test_token_usage_tracking(self, mock_components, dev_settings):
        adapter = OllamaAdapter(dev_settings)
        assert adapter.get_token_usage() == (0, 0, 0)
        adapter.reset_token_usage()
        assert adapter.get_token_usage() == (0, 0, 0)

    def test_get_and_reset_token_usage(self, mock_components, dev_settings):
        adapter = OllamaAdapter(dev_settings)
        adapter._token_usage.add(100, 50, 150)
        assert adapter.get_and_reset_token_usage() == (100, 50, 150)
        assert adapter.get_token_usage() == (0, 0, 0)

    def test_think_level_passed_to_client(self, mock_components, prod_settings):
        OllamaAdapter(prod_settings)
        _, kwargs = mock_components["client"].call_args
        assert kwargs["think_level"] == "medium"

    def test_no_think_level_in_dev(self, mock_components, dev_settings):
        OllamaAdapter(dev_settings)
        _, kwargs = mock_components["client"].call_args
        assert kwargs.get("think_level") is None

    def test_thinking_config(self, mock_components, prod_settings):
        adapter = OllamaAdapter(prod_settings)
        config = adapter.get_thinking_config()
        assert config.enabled
        assert config.think_level == "medium"

    def test_thinking_config_disabled(self, mock_components, dev_settings):
        adapter = OllamaAdapter(dev_settings)
        config = adapter.get_thinking_config()
        assert not config.enabled
        assert config.to_ollama_options() is None


class TestGetLLMAdapter:
    """get_llm_adapter 팩토리 함수 테스트."""

    @patch("evalvault.adapters.outbound.llm.openai_adapter.TokenTrackingAsyncOpenAI")
    @patch("evalvault.adapters.outbound.llm.openai_adapter.create_instructor_llm")
    @patch("evalvault.adapters.outbound.llm.openai_adapter.create_openai_embeddings_with_legacy")
    def test_openai_provider(self, mock_embeddings, mock_llm_factory, mock_client):
        settings = Settings()
        settings.llm_provider = "openai"
        settings.openai_api_key = "test-key"

        adapter = get_llm_adapter(settings)

        from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter

        assert isinstance(adapter, OpenAIAdapter)

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.AsyncOpenAI")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.create_instructor_llm")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.ThinkingTokenTrackingAsyncOpenAI")
    def test_ollama_provider(self, mock_client, mock_llm_factory, mock_embeddings, mock_async):
        settings = Settings()
        settings.llm_provider = "ollama"
        settings.ollama_model = "gemma3:1b"
        settings.ollama_embedding_model = "qwen3-embedding:0.6b"

        adapter = get_llm_adapter(settings)

        assert isinstance(adapter, OllamaAdapter)
        assert adapter.get_model_name() == "ollama/gemma3:1b"

    def test_unsupported_provider(self):
        settings = Settings()
        settings.llm_provider = "unsupported"

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            get_llm_adapter(settings)

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.AsyncOpenAI")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.create_instructor_llm")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.ThinkingTokenTrackingAsyncOpenAI")
    def test_provider_case_insensitive(
        self, mock_client, mock_llm_factory, mock_embeddings, mock_async
    ):
        settings = Settings()
        settings.llm_provider = "OLLAMA"
        settings.ollama_model = "gemma3:1b"
        settings.ollama_embedding_model = "qwen3-embedding:0.6b"

        adapter = get_llm_adapter(settings)

        assert isinstance(adapter, OllamaAdapter)
