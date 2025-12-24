"""Tests for Azure OpenAI LLM adapter."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from evalvault.adapters.outbound.llm.azure_adapter import AzureOpenAIAdapter, TokenUsage
from evalvault.config.settings import Settings


class TestTokenUsage:
    """TokenUsage 유틸리티 테스트."""

    def test_add_tokens(self):
        """토큰 추가가 올바르게 동작하는지 테스트."""
        usage = TokenUsage()
        usage.add(10, 5, 15)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 15

    def test_add_tokens_multiple_times(self):
        """여러 번 토큰을 추가했을 때 누적되는지 테스트."""
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


class TestAzureOpenAIAdapter:
    """Azure OpenAI 어댑터 테스트."""

    @pytest.fixture
    def azure_settings(self):
        """Azure OpenAI 설정 픽스처."""
        return Settings(
            azure_api_key="test-key",
            azure_endpoint="https://test.openai.azure.com",
            azure_deployment="gpt-4",
            azure_embedding_deployment="text-embedding-ada-002",
            azure_api_version="2024-02-15-preview",
        )

    @pytest.fixture
    def mock_azure_client(self):
        """Mock Azure OpenAI client."""
        with patch("evalvault.adapters.outbound.llm.azure_adapter.AsyncAzureOpenAI") as mock:
            yield mock

    @pytest.fixture
    def mock_ragas_llm(self):
        """Mock Ragas LLM factory."""
        with patch("evalvault.adapters.outbound.llm.azure_adapter.llm_factory") as mock:
            mock_instance = MagicMock()
            mock_instance.generate = MagicMock()
            mock_instance.agenerate = AsyncMock()
            mock.return_value = mock_instance
            yield mock

    @pytest.fixture
    def mock_ragas_embeddings(self):
        """Mock Ragas embedding factory."""
        with patch("evalvault.adapters.outbound.llm.azure_adapter.embedding_factory") as mock:
            yield mock

    def test_init_validates_endpoint(self, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """AZURE_ENDPOINT가 없으면 ValueError가 발생하는지 테스트."""
        settings = Settings()  # No Azure config
        with pytest.raises(ValueError, match="AZURE_ENDPOINT"):
            AzureOpenAIAdapter(settings)

    def test_init_validates_api_key(self, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """AZURE_API_KEY가 없으면 ValueError가 발생하는지 테스트."""
        settings = Settings(azure_endpoint="https://test.openai.azure.com")
        with pytest.raises(ValueError, match="AZURE_API_KEY"):
            AzureOpenAIAdapter(settings)

    def test_init_validates_deployment(self, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """AZURE_DEPLOYMENT가 없으면 ValueError가 발생하는지 테스트."""
        settings = Settings(
            azure_endpoint="https://test.openai.azure.com",
            azure_api_key="test-key",
        )
        with pytest.raises(ValueError, match="AZURE_DEPLOYMENT"):
            AzureOpenAIAdapter(settings)

    def test_get_model_name(self, azure_settings, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """get_model_name이 올바른 모델명을 반환하는지 테스트."""
        adapter = AzureOpenAIAdapter(azure_settings)
        assert adapter.get_model_name() == "azure/gpt-4"

    def test_as_ragas_llm(self, azure_settings, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """as_ragas_llm이 Ragas LLM 인스턴스를 반환하는지 테스트."""
        adapter = AzureOpenAIAdapter(azure_settings)
        ragas_llm = adapter.as_ragas_llm()
        assert ragas_llm is not None
        assert hasattr(ragas_llm, "generate")
        assert hasattr(ragas_llm, "agenerate")

    def test_as_ragas_embeddings(self, azure_settings, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """as_ragas_embeddings이 Ragas 임베딩 인스턴스를 반환하는지 테스트."""
        adapter = AzureOpenAIAdapter(azure_settings)
        embeddings = adapter.as_ragas_embeddings()
        assert embeddings is not None

    def test_as_ragas_embeddings_without_deployment(self, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """임베딩 배포가 없을 때 ValueError가 발생하는지 테스트."""
        settings = Settings(
            azure_api_key="test-key",
            azure_endpoint="https://test.openai.azure.com",
            azure_deployment="gpt-4",
            # No azure_embedding_deployment
        )
        adapter = AzureOpenAIAdapter(settings)
        with pytest.raises(ValueError, match="Azure embedding deployment not configured"):
            adapter.as_ragas_embeddings()

    def test_token_usage_tracking(self, azure_settings, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """토큰 사용량 추적이 올바르게 동작하는지 테스트."""
        adapter = AzureOpenAIAdapter(azure_settings)

        # Simulate token usage
        adapter._token_usage.add(100, 50, 150)

        usage = adapter.get_token_usage()
        assert usage == (100, 50, 150)

    def test_reset_token_usage(self, azure_settings, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """토큰 사용량 리셋이 동작하는지 테스트."""
        adapter = AzureOpenAIAdapter(azure_settings)
        adapter._token_usage.add(100, 50, 150)
        adapter.reset_token_usage()
        assert adapter.get_token_usage() == (0, 0, 0)

    def test_get_and_reset_token_usage(self, azure_settings, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """get_and_reset_token_usage가 값을 반환하고 리셋하는지 테스트."""
        adapter = AzureOpenAIAdapter(azure_settings)
        adapter._token_usage.add(100, 50, 150)

        usage = adapter.get_and_reset_token_usage()
        assert usage == (100, 50, 150)
        assert adapter.get_token_usage() == (0, 0, 0)

    def test_llm_port_compliance(self, azure_settings, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """LLMPort 인터페이스를 올바르게 구현했는지 테스트."""
        adapter = AzureOpenAIAdapter(azure_settings)
        assert hasattr(adapter, "get_model_name")
        assert hasattr(adapter, "as_ragas_llm")
        assert callable(adapter.get_model_name)
        assert callable(adapter.as_ragas_llm)

    def test_azure_client_creation(self, azure_settings, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """Azure OpenAI 클라이언트가 올바른 설정으로 생성되는지 테스트."""
        adapter = AzureOpenAIAdapter(azure_settings)

        # Verify AsyncAzureOpenAI was called with correct parameters
        mock_azure_client.assert_called_once_with(
            azure_endpoint="https://test.openai.azure.com",
            api_key="test-key",
            api_version="2024-02-15-preview",
        )

    def test_ragas_llm_factory_call(self, azure_settings, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """Ragas llm_factory가 올바른 파라미터로 호출되는지 테스트."""
        adapter = AzureOpenAIAdapter(azure_settings)

        # Verify llm_factory was called with correct parameters
        mock_ragas_llm.assert_called_once_with(
            model="gpt-4",
            provider="azure_openai",
            azure_endpoint="https://test.openai.azure.com",
            api_key="test-key",
            api_version="2024-02-15-preview",
        )

    def test_ragas_embeddings_creation(self, azure_settings, mock_azure_client, mock_ragas_llm, mock_ragas_embeddings):
        """Ragas Azure 임베딩이 올바른 파라미터로 생성되는지 테스트."""
        adapter = AzureOpenAIAdapter(azure_settings)

        # Verify embedding_factory was called with correct parameters
        # Note: client is the AsyncAzureOpenAI instance, we can't easily check it
        # So we just check that it was called with the right provider and model
        assert mock_ragas_embeddings.called
        call_kwargs = mock_ragas_embeddings.call_args.kwargs
        assert call_kwargs["provider"] == "openai"
        assert call_kwargs["model"] == "text-embedding-ada-002"
        assert "client" in call_kwargs
