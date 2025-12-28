"""Unit tests for OllamaAdapter.

모델명 참조:
  - 개발 LLM: gemma3:1b
  - 운영 LLM: gpt-oss-safeguard:20b
  - 개발 임베딩: qwen3-embedding:0.6b
  - 운영 임베딩: qwen3-embedding:8b
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from evalvault.adapters.outbound.llm import OllamaAdapter, get_llm_adapter
from evalvault.adapters.outbound.llm.ollama_adapter import ThinkingTokenTrackingAsyncOpenAI
from evalvault.config.settings import Settings


class TestOllamaAdapter:
    """OllamaAdapter 단위 테스트."""

    @pytest.fixture
    def dev_settings(self) -> Settings:
        """개발 환경 설정 (gemma3:1b)."""
        settings = Settings()
        settings.llm_provider = "ollama"
        settings.ollama_model = "gemma3:1b"
        settings.ollama_embedding_model = "qwen3-embedding:0.6b"
        settings.ollama_base_url = "http://localhost:11434"
        settings.ollama_timeout = 120
        return settings

    @pytest.fixture
    def prod_settings(self) -> Settings:
        """운영 환경 설정 (gpt-oss-safeguard:20b)."""
        settings = Settings()
        settings.llm_provider = "ollama"
        settings.ollama_model = "gpt-oss-safeguard:20b"
        settings.ollama_embedding_model = "qwen3-embedding:8b"
        settings.ollama_base_url = "http://localhost:11434"
        settings.ollama_timeout = 180
        settings.ollama_think_level = "medium"
        return settings

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    def test_adapter_initialization_dev(self, mock_embeddings, mock_llm_factory, dev_settings):
        """개발 환경 어댑터 초기화 테스트."""
        adapter = OllamaAdapter(dev_settings)

        assert adapter.get_model_name() == "ollama/gemma3:1b"
        assert adapter.get_embedding_model_name() == "qwen3-embedding:0.6b"
        assert adapter.get_base_url() == "http://localhost:11434"
        assert adapter.get_think_level() is None

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    def test_adapter_initialization_prod(self, mock_embeddings, mock_llm_factory, prod_settings):
        """운영 환경 어댑터 초기화 테스트."""
        adapter = OllamaAdapter(prod_settings)

        assert adapter.get_model_name() == "ollama/gpt-oss-safeguard:20b"
        assert adapter.get_embedding_model_name() == "qwen3-embedding:8b"
        assert adapter.get_think_level() == "medium"

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    def test_as_ragas_llm(self, mock_embeddings, mock_llm_factory, dev_settings):
        """Ragas LLM 반환 테스트."""
        mock_ragas_llm = MagicMock()
        mock_llm_factory.return_value = mock_ragas_llm

        adapter = OllamaAdapter(dev_settings)
        result = adapter.as_ragas_llm()

        assert result == mock_ragas_llm
        mock_llm_factory.assert_called_once()

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    def test_as_ragas_embeddings(self, mock_embeddings, mock_llm_factory, dev_settings):
        """Ragas 임베딩 반환 테스트."""
        mock_embedding_instance = MagicMock()
        mock_embeddings.return_value = mock_embedding_instance

        adapter = OllamaAdapter(dev_settings)
        result = adapter.as_ragas_embeddings()

        assert result == mock_embedding_instance

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    def test_token_usage_tracking(self, mock_embeddings, mock_llm_factory, dev_settings):
        """토큰 사용량 추적 테스트."""
        adapter = OllamaAdapter(dev_settings)

        # 초기값 확인
        assert adapter.get_token_usage() == (0, 0, 0)

        # 리셋 테스트
        adapter.reset_token_usage()
        assert adapter.get_token_usage() == (0, 0, 0)

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    def test_get_and_reset_token_usage(self, mock_embeddings, mock_llm_factory, dev_settings):
        """토큰 사용량 조회 및 리셋 테스트."""
        adapter = OllamaAdapter(dev_settings)

        # 수동으로 토큰 추가 (내부 상태 테스트)
        adapter._token_usage.add(100, 50, 150)

        result = adapter.get_and_reset_token_usage()
        assert result == (100, 50, 150)

        # 리셋 확인
        assert adapter.get_token_usage() == (0, 0, 0)

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    def test_thinking_client_initialization(self, mock_embeddings, mock_llm_factory, prod_settings):
        """ThinkingTokenTrackingAsyncOpenAI가 올바르게 초기화되는지 테스트."""
        adapter = OllamaAdapter(prod_settings)

        # 클라이언트가 ThinkingTokenTrackingAsyncOpenAI 인스턴스인지 확인
        assert isinstance(adapter._client, ThinkingTokenTrackingAsyncOpenAI)
        assert adapter._client._think_level == "medium"

    @pytest.mark.asyncio
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    async def test_thinking_parameter_injection(
        self, mock_embeddings, mock_llm_factory, prod_settings
    ):
        """Thinking 파라미터가 LLM 호출 시 주입되는지 테스트."""
        # Create adapter with thinking enabled
        adapter = OllamaAdapter(prod_settings)

        # Mock the underlying completions.create method
        mock_response = MagicMock()
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        # Create a spy on the completions.create method
        adapter._client.chat.completions._completions.create = AsyncMock(return_value=mock_response)

        # Call the method
        await adapter._client.chat.completions.create(
            model="gpt-oss-safeguard:20b", messages=[{"role": "user", "content": "test"}]
        )

        # Verify that extra_body was added with thinking parameters
        call_kwargs = adapter._client.chat.completions._completions.create.call_args[1]
        assert "extra_body" in call_kwargs
        assert "options" in call_kwargs["extra_body"]
        assert call_kwargs["extra_body"]["options"]["think_level"] == "medium"

    @pytest.mark.asyncio
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    async def test_no_thinking_parameter_when_none(
        self, mock_embeddings, mock_llm_factory, dev_settings
    ):
        """Thinking level이 None일 때 파라미터가 주입되지 않는지 테스트."""
        # Create adapter without thinking (dev_settings has think_level=None)
        adapter = OllamaAdapter(dev_settings)

        # Mock the underlying completions.create method
        mock_response = MagicMock()
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        # Create a spy on the completions.create method
        adapter._client.chat.completions._completions.create = AsyncMock(return_value=mock_response)

        # Call the method without extra_body
        await adapter._client.chat.completions.create(
            model="gemma3:1b", messages=[{"role": "user", "content": "test"}]
        )

        # Verify that no extra_body was added when think_level is None
        call_kwargs = adapter._client.chat.completions._completions.create.call_args[1]
        # extra_body should not contain think_level
        if "extra_body" in call_kwargs:
            # If extra_body exists, it should be empty or not contain think_level
            assert "options" not in call_kwargs["extra_body"] or "think_level" not in call_kwargs[
                "extra_body"
            ].get("options", {})

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    def test_thinking_config_disabled_by_default(
        self, mock_embeddings, mock_llm_factory, dev_settings
    ):
        """기본적으로 thinking이 비활성화되어 있는지 테스트."""
        adapter = OllamaAdapter(dev_settings)
        config = adapter.get_thinking_config()

        assert config.enabled is False
        assert config.budget_tokens is None
        assert config.think_level is None
        assert adapter.supports_thinking() is False

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    def test_thinking_config_enabled_with_think_level(
        self, mock_embeddings, mock_llm_factory, prod_settings
    ):
        """think_level 설정 시 thinking이 활성화되는지 테스트."""
        adapter = OllamaAdapter(prod_settings)
        config = adapter.get_thinking_config()

        assert config.enabled is True
        assert config.budget_tokens is None
        assert config.think_level == "medium"
        assert adapter.supports_thinking() is True

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    def test_thinking_config_to_ollama_options(
        self, mock_embeddings, mock_llm_factory, prod_settings
    ):
        """ThinkingConfig가 Ollama options으로 변환되는지 테스트."""
        adapter = OllamaAdapter(prod_settings)
        config = adapter.get_thinking_config()

        ollama_options = config.to_ollama_options()
        assert ollama_options is not None
        assert ollama_options["think_level"] == "medium"

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    def test_thinking_config_disabled_returns_none_options(
        self, mock_embeddings, mock_llm_factory, dev_settings
    ):
        """Thinking 비활성화 시 to_ollama_options이 None 반환하는지 테스트."""
        adapter = OllamaAdapter(dev_settings)
        config = adapter.get_thinking_config()

        assert config.to_ollama_options() is None


class TestGetLLMAdapter:
    """get_llm_adapter 팩토리 함수 테스트."""

    @patch("evalvault.adapters.outbound.llm.openai_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.openai_adapter.RagasOpenAIEmbeddings")
    def test_openai_provider(self, mock_embeddings, mock_llm_factory):
        """OpenAI 프로바이더 테스트."""
        settings = Settings()
        settings.llm_provider = "openai"
        settings.openai_api_key = "test-key"

        adapter = get_llm_adapter(settings)

        from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter

        assert isinstance(adapter, OpenAIAdapter)

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    def test_ollama_provider(self, mock_embeddings, mock_llm_factory):
        """Ollama 프로바이더 테스트."""
        settings = Settings()
        settings.llm_provider = "ollama"
        settings.ollama_model = "gemma3:1b"
        settings.ollama_embedding_model = "qwen3-embedding:0.6b"

        adapter = get_llm_adapter(settings)

        assert isinstance(adapter, OllamaAdapter)
        assert adapter.get_model_name() == "ollama/gemma3:1b"

    def test_unsupported_provider(self):
        """지원하지 않는 프로바이더 테스트."""
        settings = Settings()
        settings.llm_provider = "unsupported"

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            get_llm_adapter(settings)

    @patch("evalvault.adapters.outbound.llm.ollama_adapter.llm_factory")
    @patch("evalvault.adapters.outbound.llm.ollama_adapter.RagasOpenAIEmbeddings")
    def test_provider_case_insensitive(self, mock_embeddings, mock_llm_factory):
        """프로바이더 이름 대소문자 무시 테스트."""
        settings = Settings()
        settings.llm_provider = "OLLAMA"
        settings.ollama_model = "gemma3:1b"
        settings.ollama_embedding_model = "qwen3-embedding:0.6b"

        adapter = get_llm_adapter(settings)

        assert isinstance(adapter, OllamaAdapter)
