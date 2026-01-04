"""Tests for Anthropic Claude LLM adapter."""

import threading
from unittest.mock import MagicMock, patch

import pytest

from evalvault.adapters.outbound.llm.anthropic_adapter import AnthropicAdapter
from evalvault.adapters.outbound.llm.base import TokenUsage
from evalvault.config.settings import Settings

pytest.importorskip("anthropic")


class TestTokenUsage:
    """TokenUsage 클래스 테스트."""

    def test_initial_values(self):
        usage = TokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_add_tokens(self):
        usage = TokenUsage()
        usage.add(10, 5, 15)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 15

    def test_add_tokens_multiple_times(self):
        usage = TokenUsage()
        usage.add(10, 5, 15)
        usage.add(20, 10, 30)
        assert usage.prompt_tokens == 30
        assert usage.completion_tokens == 15
        assert usage.total_tokens == 45

    def test_reset(self):
        usage = TokenUsage()
        usage.add(10, 5, 15)
        usage.reset()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_get_and_reset(self):
        usage = TokenUsage()
        usage.add(10, 5, 15)
        assert usage.get_and_reset() == (10, 5, 15)
        assert (usage.prompt_tokens, usage.completion_tokens, usage.total_tokens) == (0, 0, 0)

    def test_thread_safety(self):
        usage = TokenUsage()

        def add_tokens():
            for _ in range(100):
                usage.add(1, 1, 2)

        threads = [threading.Thread(target=add_tokens) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert usage.total_tokens == 2000


class TestAnthropicAdapter:
    """AnthropicAdapter 테스트."""

    @pytest.fixture
    def anthropic_settings(self):
        return Settings(
            anthropic_api_key="test-anthropic-key",
            anthropic_model="claude-3-5-sonnet-20241022",
            openai_api_key="test-openai-key",
            openai_embedding_model="text-embedding-3-small",
        )

    @pytest.fixture
    def anthropic_settings_no_openai(self):
        return Settings(
            anthropic_api_key="test-anthropic-key",
            anthropic_model="claude-3-5-sonnet-20241022",
            openai_api_key=None,
        )

    @pytest.fixture
    def mock_components(self):
        with (
            patch(
                "evalvault.adapters.outbound.llm.anthropic_adapter.ThinkingTokenTrackingAsyncAnthropic"
            ) as mock_client,
            patch(
                "evalvault.adapters.outbound.llm.anthropic_adapter.create_instructor_llm"
            ) as mock_llm_factory,
            patch(
                "evalvault.adapters.outbound.llm.anthropic_adapter.create_openai_embeddings_with_legacy"
            ) as mock_embeddings,
            patch("evalvault.adapters.outbound.llm.anthropic_adapter.AsyncOpenAI") as mock_openai,
        ):
            mock_client_instance = MagicMock()
            mock_client_instance._client = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_llm_factory.return_value = MagicMock()
            mock_embeddings.return_value = MagicMock()
            mock_openai.return_value = MagicMock()
            yield {
                "client": mock_client,
                "llm_factory": mock_llm_factory,
                "embeddings": mock_embeddings,
                "openai_client": mock_openai,
            }

    def test_init_validates_api_key(self):
        settings = Settings(anthropic_api_key=None)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            AnthropicAdapter(settings)

    def test_init_with_valid_settings(self, anthropic_settings, mock_components):
        adapter = AnthropicAdapter(anthropic_settings)
        assert adapter.get_model_name() == "claude-3-5-sonnet-20241022"

    def test_as_ragas_llm(self, anthropic_settings, mock_components):
        adapter = AnthropicAdapter(anthropic_settings)
        assert adapter.as_ragas_llm() == mock_components["llm_factory"].return_value
        mock_components["llm_factory"].assert_called_once_with(
            "anthropic",
            "claude-3-5-sonnet-20241022",
            mock_components["client"].return_value._client,
        )

    def test_as_ragas_embeddings_with_openai_fallback(self, anthropic_settings, mock_components):
        adapter = AnthropicAdapter(anthropic_settings)
        assert adapter.as_ragas_embeddings() == mock_components["embeddings"].return_value

    def test_as_ragas_embeddings_raises_without_openai(
        self, anthropic_settings_no_openai, mock_components
    ):
        adapter = AnthropicAdapter(anthropic_settings_no_openai)
        with pytest.raises(ValueError, match="Embeddings not available"):
            adapter.as_ragas_embeddings()

    def test_token_usage_tracking(self, anthropic_settings, mock_components):
        adapter = AnthropicAdapter(anthropic_settings)
        adapter._token_usage.add(100, 50, 150)
        assert adapter.get_token_usage() == (100, 50, 150)

    def test_reset_token_usage(self, anthropic_settings, mock_components):
        adapter = AnthropicAdapter(anthropic_settings)
        adapter._token_usage.add(100, 50, 150)
        adapter.reset_token_usage()
        assert adapter.get_token_usage() == (0, 0, 0)

    def test_get_and_reset_token_usage(self, anthropic_settings, mock_components):
        adapter = AnthropicAdapter(anthropic_settings)
        adapter._token_usage.add(100, 50, 150)
        assert adapter.get_and_reset_token_usage() == (100, 50, 150)
        assert adapter.get_token_usage() == (0, 0, 0)

    def test_different_models(self, mock_components):
        models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307",
        ]
        for model in models:
            settings = Settings(
                anthropic_api_key="test-key",
                anthropic_model=model,
                openai_api_key="openai-key",
            )
            adapter = AnthropicAdapter(settings)
            assert adapter.get_model_name() == model
            mock_components["llm_factory"].reset_mock()

    def test_embeddings_error_message_is_clear(self, anthropic_settings_no_openai, mock_components):
        adapter = AnthropicAdapter(anthropic_settings_no_openai)
        with pytest.raises(ValueError) as exc_info:
            adapter.as_ragas_embeddings()
        assert "Embeddings not available" in str(exc_info.value)

    def test_thinking_config_disabled_by_default(self, anthropic_settings, mock_components):
        adapter = AnthropicAdapter(anthropic_settings)
        config = adapter.get_thinking_config()
        assert not config.enabled
        assert adapter.get_thinking_budget() is None

    def test_thinking_config_enabled_with_budget(self, mock_components):
        settings = Settings(
            anthropic_api_key="test-key",
            anthropic_model="claude-3-5-sonnet-20241022",
            anthropic_thinking_budget=10000,
            openai_api_key="openai-key",
        )
        adapter = AnthropicAdapter(settings)
        config = adapter.get_thinking_config()
        assert config.enabled
        assert adapter.get_thinking_budget() == 10000
