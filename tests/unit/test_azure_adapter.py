"""Tests for Azure OpenAI LLM adapter."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from evalvault.adapters.outbound.llm.azure_adapter import AzureOpenAIAdapter
from evalvault.adapters.outbound.llm.base import TokenUsage
from evalvault.config.settings import Settings


class TestTokenUsage:
    """TokenUsage 유틸리티 테스트."""

    def test_add_tokens(self):
        usage = TokenUsage()
        usage.add(10, 5, 15)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 15

    def test_reset(self):
        usage = TokenUsage()
        usage.add(10, 5, 15)
        usage.reset()
        assert (usage.prompt_tokens, usage.completion_tokens, usage.total_tokens) == (0, 0, 0)

    def test_get_and_reset(self):
        usage = TokenUsage()
        usage.add(10, 5, 15)
        assert usage.get_and_reset() == (10, 5, 15)
        assert (usage.prompt_tokens, usage.completion_tokens, usage.total_tokens) == (0, 0, 0)


class TestAzureOpenAIAdapter:
    """Azure OpenAI 어댑터 테스트."""

    @pytest.fixture
    def azure_settings(self):
        return Settings(
            azure_api_key="test-key",
            azure_endpoint="https://test.openai.azure.com",
            azure_deployment="gpt-4",
            azure_embedding_deployment="text-embedding-ada-002",
            azure_api_version="2024-02-15-preview",
        )

    @pytest.fixture
    def mock_azure_client(self):
        with patch(
            "evalvault.adapters.outbound.llm.azure_adapter.TokenTrackingAsyncAzureOpenAI"
        ) as mock:
            yield mock

    @pytest.fixture
    def mock_instructor_llm(self):
        with patch("evalvault.adapters.outbound.llm.azure_adapter.create_instructor_llm") as mock:
            mock_instance = MagicMock()
            mock_instance.generate = MagicMock()
            mock_instance.agenerate = AsyncMock()
            mock.return_value = mock_instance
            yield mock

    @pytest.fixture
    def mock_embeddings(self):
        with patch("evalvault.adapters.outbound.llm.azure_adapter.embedding_factory") as mock:
            yield mock

    def test_init_validates_endpoint(self, mock_azure_client, mock_instructor_llm, mock_embeddings):
        settings = Settings()
        with pytest.raises(ValueError, match="AZURE_ENDPOINT"):
            AzureOpenAIAdapter(settings)

    def test_init_validates_api_key(self, mock_azure_client, mock_instructor_llm, mock_embeddings):
        settings = Settings(azure_endpoint="https://test.openai.azure.com")
        with pytest.raises(ValueError, match="AZURE_API_KEY"):
            AzureOpenAIAdapter(settings)

    def test_init_validates_deployment(
        self, mock_azure_client, mock_instructor_llm, mock_embeddings
    ):
        settings = Settings(
            azure_endpoint="https://test.openai.azure.com",
            azure_api_key="test-key",
        )
        with pytest.raises(ValueError, match="AZURE_DEPLOYMENT"):
            AzureOpenAIAdapter(settings)

    def test_get_model_name(
        self, azure_settings, mock_azure_client, mock_instructor_llm, mock_embeddings
    ):
        adapter = AzureOpenAIAdapter(azure_settings)
        assert adapter.get_model_name() == "azure/gpt-4"

    def test_as_ragas_llm(
        self, azure_settings, mock_azure_client, mock_instructor_llm, mock_embeddings
    ):
        adapter = AzureOpenAIAdapter(azure_settings)
        assert adapter.as_ragas_llm() == mock_instructor_llm.return_value

    def test_as_ragas_embeddings(
        self, azure_settings, mock_azure_client, mock_instructor_llm, mock_embeddings
    ):
        adapter = AzureOpenAIAdapter(azure_settings)
        assert adapter.as_ragas_embeddings() == mock_embeddings.return_value

    def test_as_ragas_embeddings_without_deployment(
        self, mock_azure_client, mock_instructor_llm, mock_embeddings
    ):
        settings = Settings(
            azure_api_key="test-key",
            azure_endpoint="https://test.openai.azure.com",
            azure_deployment="gpt-4",
        )
        adapter = AzureOpenAIAdapter(settings)
        with pytest.raises(ValueError, match="Azure embedding deployment not configured"):
            adapter.as_ragas_embeddings()

    def test_token_usage_tracking(
        self, azure_settings, mock_azure_client, mock_instructor_llm, mock_embeddings
    ):
        adapter = AzureOpenAIAdapter(azure_settings)
        adapter._token_usage.add(100, 50, 150)
        assert adapter.get_token_usage() == (100, 50, 150)

    def test_reset_token_usage(
        self, azure_settings, mock_azure_client, mock_instructor_llm, mock_embeddings
    ):
        adapter = AzureOpenAIAdapter(azure_settings)
        adapter._token_usage.add(100, 50, 150)
        adapter.reset_token_usage()
        assert adapter.get_token_usage() == (0, 0, 0)

    def test_get_and_reset_token_usage(
        self, azure_settings, mock_azure_client, mock_instructor_llm, mock_embeddings
    ):
        adapter = AzureOpenAIAdapter(azure_settings)
        adapter._token_usage.add(100, 50, 150)
        assert adapter.get_and_reset_token_usage() == (100, 50, 150)
        assert adapter.get_token_usage() == (0, 0, 0)

    def test_azure_client_creation(
        self, azure_settings, mock_azure_client, mock_instructor_llm, mock_embeddings
    ):
        AzureOpenAIAdapter(azure_settings)
        from unittest.mock import ANY

        mock_azure_client.assert_called_once_with(
            usage_tracker=ANY,
            azure_endpoint="https://test.openai.azure.com",
            api_key="test-key",
            api_version="2024-02-15-preview",
        )

    def test_instructor_factory_call(
        self, azure_settings, mock_azure_client, mock_instructor_llm, mock_embeddings
    ):
        AzureOpenAIAdapter(azure_settings)
        mock_instructor_llm.assert_called_once_with(
            "openai",
            "gpt-4",
            mock_azure_client.return_value,
        )
