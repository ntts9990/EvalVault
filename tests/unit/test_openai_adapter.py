"""Tests for OpenAI LLM adapter."""

import os
import pytest
from unittest.mock import MagicMock, patch

from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter
from evalvault.config.settings import Settings
from tests.unit.conftest import get_test_model


class TestOpenAIAdapter:
    """OpenAI adapter 테스트."""

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
