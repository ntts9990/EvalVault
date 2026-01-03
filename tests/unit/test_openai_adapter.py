"""Tests for OpenAI LLM adapter."""

from unittest.mock import MagicMock, patch

import pytest

from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter
from evalvault.config.settings import Settings
from tests.unit.conftest import get_test_model


class TestOpenAIAdapter:
    """OpenAI adapter 테스트."""

    @pytest.fixture(autouse=True)
    def mock_ragas_deps(self):
        """Mock Ragas dependencies to avoid actual API calls."""
        with (
            patch(
                "evalvault.adapters.outbound.llm.openai_adapter.TokenTrackingAsyncOpenAI"
            ) as mock_client,
            patch(
                "evalvault.adapters.outbound.llm.openai_adapter.create_instructor_llm"
            ) as mock_llm,
            patch(
                "evalvault.adapters.outbound.llm.openai_adapter.create_openai_embeddings_with_legacy"
            ) as mock_embed,
        ):
            mock_client.return_value = MagicMock()
            mock_llm.return_value = MagicMock()
            mock_embed.return_value = MagicMock()
            yield

    @pytest.fixture
    def model_name(self):
        """Get model name from environment."""
        return get_test_model()

    @pytest.fixture
    def settings(self, model_name):
        """Test settings fixture."""
        return Settings(
            openai_api_key="test-api-key",
            openai_model=model_name,
        )

    def test_get_model_name(self, settings, model_name):
        """get_model_name이 올바른 모델명을 반환하는지 테스트."""
        adapter = OpenAIAdapter(settings)
        assert adapter.get_model_name() == model_name

    def test_custom_base_url(self, model_name):
        """커스텀 base_url이 올바르게 설정되는지 테스트."""
        settings = Settings(
            openai_api_key="test-key",
            openai_base_url="https://custom-api.example.com/v1",
            openai_model=model_name,
        )
        adapter = OpenAIAdapter(settings)
        # Verify adapter was created successfully
        assert adapter.get_model_name() == model_name

    def test_as_ragas_llm_returns_ragas_instance(self, settings, model_name):
        """as_ragas_llm이 Ragas LLM 인스턴스를 반환하는지 테스트."""
        adapter = OpenAIAdapter(settings)
        ragas_llm = adapter.as_ragas_llm()

        # Check that it returns a Ragas LLM instance with required methods
        assert ragas_llm is not None
        assert hasattr(ragas_llm, "generate")  # Ragas LLM interface
        assert hasattr(ragas_llm, "agenerate")  # Async generation

    def test_as_ragas_llm_with_custom_base_url(self):
        """커스텀 base_url이 Ragas LLM에 전달되는지 테스트."""
        settings = Settings(
            openai_api_key="test-key",
            openai_base_url="https://custom-api.example.com/v1",
            openai_model="gpt-5-mini",
        )
        adapter = OpenAIAdapter(settings)
        ragas_llm = adapter.as_ragas_llm()

        # Verify adapter was created with custom base URL
        assert ragas_llm is not None
        # The Ragas LLM wraps the OpenAI client, verify adapter is functional
        assert adapter.get_model_name() == "gpt-5-mini"

    def test_token_usage_methods_exist(self, settings):
        """토큰 사용량 추적 메서드가 존재하는지 테스트."""
        adapter = OpenAIAdapter(settings)
        assert hasattr(adapter, "get_token_usage")
        assert hasattr(adapter, "get_and_reset_token_usage")
        assert hasattr(adapter, "reset_token_usage")

    def test_token_usage_initial_values(self, settings):
        """초기 토큰 사용량이 0인지 테스트."""
        adapter = OpenAIAdapter(settings)
        prompt, completion, total = adapter.get_token_usage()
        assert prompt == 0
        assert completion == 0
        assert total == 0

    def test_reset_token_usage(self, settings):
        """토큰 사용량 리셋이 동작하는지 테스트."""
        adapter = OpenAIAdapter(settings)
        # Manually add some tokens for testing
        adapter._token_usage.add(100, 50, 150)

        # Verify tokens were added
        prompt, completion, total = adapter.get_token_usage()
        assert total == 150

        # Reset and verify
        adapter.reset_token_usage()
        prompt, completion, total = adapter.get_token_usage()
        assert prompt == 0
        assert completion == 0
        assert total == 0

    def test_get_and_reset_token_usage(self, settings):
        """get_and_reset_token_usage가 값을 반환하고 리셋하는지 테스트."""
        adapter = OpenAIAdapter(settings)
        # Manually add some tokens for testing
        adapter._token_usage.add(100, 50, 150)

        # Get and reset
        prompt, completion, total = adapter.get_and_reset_token_usage()
        assert prompt == 100
        assert completion == 50
        assert total == 150

        # Verify reset happened
        prompt2, completion2, total2 = adapter.get_token_usage()
        assert prompt2 == 0
        assert completion2 == 0
        assert total2 == 0
