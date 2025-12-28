"""Tests for Anthropic Claude LLM adapter."""

import threading
from unittest.mock import MagicMock, patch

import pytest

from evalvault.adapters.outbound.llm.anthropic_adapter import AnthropicAdapter, TokenUsage
from evalvault.config.settings import Settings


class TestTokenUsage:
    """TokenUsage 클래스 테스트."""

    def test_initial_values(self):
        """초기값이 0인지 테스트."""
        usage = TokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_add_tokens(self):
        """토큰 추가가 올바르게 동작하는지 테스트."""
        usage = TokenUsage()
        usage.add(10, 5, 15)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 15

    def test_add_tokens_multiple_times(self):
        """토큰을 여러 번 추가했을 때 누적되는지 테스트."""
        usage = TokenUsage()
        usage.add(10, 5, 15)
        usage.add(20, 10, 30)
        assert usage.prompt_tokens == 30
        assert usage.completion_tokens == 15
        assert usage.total_tokens == 45

    def test_reset(self):
        """리셋이 올바르게 동작하는지 테스트."""
        usage = TokenUsage()
        usage.add(10, 5, 15)
        usage.reset()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_get_and_reset(self):
        """get_and_reset이 값을 반환하고 리셋하는지 테스트."""
        usage = TokenUsage()
        usage.add(10, 5, 15)
        result = usage.get_and_reset()
        assert result == (10, 5, 15)
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_thread_safety(self):
        """스레드 안전성 테스트."""
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
        """Anthropic 설정 fixture (OpenAI embeddings 포함)."""
        return Settings(
            anthropic_api_key="test-anthropic-key",
            anthropic_model="claude-3-5-sonnet-20241022",
            openai_api_key="test-openai-key",  # for embeddings fallback
            openai_embedding_model="text-embedding-3-small",
        )

    @pytest.fixture
    def anthropic_settings_no_openai(self):
        """Anthropic 설정 fixture (OpenAI embeddings 없음)."""
        return Settings(
            anthropic_api_key="test-anthropic-key",
            anthropic_model="claude-3-5-sonnet-20241022",
            openai_api_key=None,  # Explicitly set to None to override .env
        )

    @pytest.fixture
    def mock_ragas_llm_factory(self):
        """Mock Ragas llm_factory and Anthropic client."""
        with (
            patch("evalvault.adapters.outbound.llm.anthropic_adapter.llm_factory") as mock_llm,
            patch("anthropic.AsyncAnthropic") as mock_anthropic,
        ):
            mock_instance = MagicMock()
            mock_instance.generate = MagicMock()
            mock_instance.agenerate = MagicMock()
            mock_llm.return_value = mock_instance
            mock_anthropic.return_value = MagicMock()
            yield mock_llm

    @pytest.fixture
    def mock_ragas_embeddings(self):
        """Mock Ragas OpenAI embeddings and AsyncOpenAI client."""
        with (
            patch(
                "evalvault.adapters.outbound.llm.anthropic_adapter.OpenAIEmbeddingsWithLegacy"
            ) as mock_emb,
            patch("evalvault.adapters.outbound.llm.anthropic_adapter.AsyncOpenAI") as mock_client,
        ):
            mock_instance = MagicMock()
            mock_emb.return_value = mock_instance
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            yield mock_emb

    def test_init_validates_api_key(self):
        """API key가 없으면 에러를 발생시키는지 테스트."""
        settings = Settings()  # No Anthropic key
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            AnthropicAdapter(settings)

    def test_init_with_valid_settings(
        self, anthropic_settings, mock_ragas_llm_factory, mock_ragas_embeddings
    ):
        """유효한 설정으로 초기화가 잘 되는지 테스트."""
        adapter = AnthropicAdapter(anthropic_settings)
        assert adapter is not None
        assert adapter.get_model_name() == "claude-3-5-sonnet-20241022"

    def test_get_model_name(
        self, anthropic_settings, mock_ragas_llm_factory, mock_ragas_embeddings
    ):
        """get_model_name이 올바른 모델명을 반환하는지 테스트."""
        adapter = AnthropicAdapter(anthropic_settings)
        assert adapter.get_model_name() == "claude-3-5-sonnet-20241022"

    def test_as_ragas_llm(self, anthropic_settings, mock_ragas_llm_factory, mock_ragas_embeddings):
        """as_ragas_llm이 Ragas LLM 인스턴스를 반환하는지 테스트."""
        adapter = AnthropicAdapter(anthropic_settings)
        ragas_llm = adapter.as_ragas_llm()
        assert ragas_llm is not None
        # Verify llm_factory was called with correct parameters (Ragas 0.4.x API)
        mock_ragas_llm_factory.assert_called_once()
        call_kwargs = mock_ragas_llm_factory.call_args[1]
        assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert call_kwargs["provider"] == "anthropic"
        assert "client" in call_kwargs  # client is required in Ragas 0.4.x
        assert "max_tokens" in call_kwargs

    def test_as_ragas_embeddings_with_openai_fallback(
        self, anthropic_settings, mock_ragas_llm_factory, mock_ragas_embeddings
    ):
        """OpenAI fallback embeddings가 올바르게 생성되는지 테스트."""
        adapter = AnthropicAdapter(anthropic_settings)
        embeddings = adapter.as_ragas_embeddings()
        assert embeddings is not None
        # Verify OpenAI embeddings was created (with client parameter)
        assert mock_ragas_embeddings.call_count == 1
        call_kwargs = mock_ragas_embeddings.call_args[1]
        assert call_kwargs["model"] == "text-embedding-3-small"
        assert "client" in call_kwargs

    def test_as_ragas_embeddings_raises_without_openai(
        self, anthropic_settings_no_openai, mock_ragas_llm_factory
    ):
        """OpenAI key가 없으면 embeddings 접근 시 에러를 발생시키는지 테스트."""
        adapter = AnthropicAdapter(anthropic_settings_no_openai)
        with pytest.raises(ValueError, match="Embeddings not available"):
            adapter.as_ragas_embeddings()

    def test_token_usage_tracking(
        self, anthropic_settings, mock_ragas_llm_factory, mock_ragas_embeddings
    ):
        """토큰 사용량 추적이 올바르게 동작하는지 테스트."""
        adapter = AnthropicAdapter(anthropic_settings)
        adapter._token_usage.add(100, 50, 150)
        assert adapter.get_token_usage() == (100, 50, 150)

    def test_initial_token_usage(
        self, anthropic_settings, mock_ragas_llm_factory, mock_ragas_embeddings
    ):
        """초기 토큰 사용량이 0인지 테스트."""
        adapter = AnthropicAdapter(anthropic_settings)
        assert adapter.get_token_usage() == (0, 0, 0)

    def test_reset_token_usage(
        self, anthropic_settings, mock_ragas_llm_factory, mock_ragas_embeddings
    ):
        """토큰 사용량 리셋이 동작하는지 테스트."""
        adapter = AnthropicAdapter(anthropic_settings)
        adapter._token_usage.add(100, 50, 150)
        adapter.reset_token_usage()
        assert adapter.get_token_usage() == (0, 0, 0)

    def test_get_and_reset_token_usage(
        self, anthropic_settings, mock_ragas_llm_factory, mock_ragas_embeddings
    ):
        """get_and_reset_token_usage가 값을 반환하고 리셋하는지 테스트."""
        adapter = AnthropicAdapter(anthropic_settings)
        adapter._token_usage.add(100, 50, 150)

        # Get and reset
        result = adapter.get_and_reset_token_usage()
        assert result == (100, 50, 150)

        # Verify reset happened
        assert adapter.get_token_usage() == (0, 0, 0)

    def test_llm_port_compliance(
        self, anthropic_settings, mock_ragas_llm_factory, mock_ragas_embeddings
    ):
        """LLMPort 인터페이스를 올바르게 구현했는지 테스트."""
        adapter = AnthropicAdapter(anthropic_settings)

        # Check required methods exist
        assert hasattr(adapter, "get_model_name")
        assert hasattr(adapter, "as_ragas_llm")
        assert hasattr(adapter, "as_ragas_embeddings")
        assert callable(adapter.get_model_name)
        assert callable(adapter.as_ragas_llm)
        assert callable(adapter.as_ragas_embeddings)

        # Check optional methods exist
        assert hasattr(adapter, "get_token_usage")
        assert hasattr(adapter, "reset_token_usage")
        assert hasattr(adapter, "get_and_reset_token_usage")

    def test_different_claude_models(self, mock_ragas_llm_factory, mock_ragas_embeddings):
        """다양한 Claude 모델을 지원하는지 테스트."""
        models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307",
        ]

        for model in models:
            settings = Settings(
                anthropic_api_key="test-key",
                anthropic_model=model,
                openai_api_key="test-openai-key",
            )
            adapter = AnthropicAdapter(settings)
            assert adapter.get_model_name() == model
            mock_ragas_llm_factory.reset_mock()
            mock_ragas_embeddings.reset_mock()

    def test_embeddings_error_message_is_clear(
        self, anthropic_settings_no_openai, mock_ragas_llm_factory
    ):
        """Embeddings 에러 메시지가 명확한지 테스트."""
        adapter = AnthropicAdapter(anthropic_settings_no_openai)

        with pytest.raises(ValueError) as exc_info:
            adapter.as_ragas_embeddings()

        error_message = str(exc_info.value)
        assert "Embeddings not available" in error_message
        assert "Anthropic doesn't provide embeddings" in error_message
        assert "OPENAI_API_KEY" in error_message

    def test_thinking_config_disabled_by_default(
        self, anthropic_settings, mock_ragas_llm_factory, mock_ragas_embeddings
    ):
        """기본적으로 extended thinking이 비활성화되어 있는지 테스트."""
        adapter = AnthropicAdapter(anthropic_settings)
        config = adapter.get_thinking_config()

        assert config.enabled is False
        assert config.budget_tokens is None
        assert config.think_level is None
        assert adapter.supports_thinking() is False
        assert adapter.get_thinking_budget() is None

    def test_thinking_config_enabled_with_budget(
        self, mock_ragas_llm_factory, mock_ragas_embeddings
    ):
        """anthropic_thinking_budget 설정 시 extended thinking이 활성화되는지 테스트."""
        settings = Settings(
            anthropic_api_key="test-key",
            anthropic_model="claude-3-5-sonnet-20241022",
            anthropic_thinking_budget=10000,
            openai_api_key="test-openai-key",
        )
        adapter = AnthropicAdapter(settings)
        config = adapter.get_thinking_config()

        assert config.enabled is True
        assert config.budget_tokens == 10000
        assert config.think_level is None
        assert adapter.supports_thinking() is True
        assert adapter.get_thinking_budget() == 10000

    def test_thinking_config_to_anthropic_param(
        self, mock_ragas_llm_factory, mock_ragas_embeddings
    ):
        """ThinkingConfig가 Anthropic API 파라미터로 변환되는지 테스트."""
        settings = Settings(
            anthropic_api_key="test-key",
            anthropic_model="claude-3-5-sonnet-20241022",
            anthropic_thinking_budget=15000,
            openai_api_key="test-openai-key",
        )
        adapter = AnthropicAdapter(settings)
        config = adapter.get_thinking_config()

        anthropic_param = config.to_anthropic_param()
        assert anthropic_param is not None
        assert anthropic_param["type"] == "enabled"
        assert anthropic_param["budget_tokens"] == 15000

    def test_thinking_config_disabled_returns_none_param(
        self, anthropic_settings, mock_ragas_llm_factory, mock_ragas_embeddings
    ):
        """Extended thinking 비활성화 시 to_anthropic_param이 None 반환하는지 테스트."""
        adapter = AnthropicAdapter(anthropic_settings)
        config = adapter.get_thinking_config()

        assert config.to_anthropic_param() is None
