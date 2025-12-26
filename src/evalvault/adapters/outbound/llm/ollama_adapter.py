"""Ollama LLM adapter for air-gapped (폐쇄망) environments.

Ollama의 OpenAI 호환 API를 사용하여 Ragas와 통합합니다.
기존 OpenAIAdapter 코드를 최대한 재사용합니다.

지원 모델:
  - 평가 LLM: gemma3:1b (개발), gpt-oss-safeguard:20b (운영)
  - 임베딩: qwen3-embedding:0.6b (개발), qwen3-embedding:8b (운영)
"""

from typing import Any

import httpx
from openai import AsyncOpenAI
from ragas.embeddings import OpenAIEmbeddings as RagasOpenAIEmbeddings
from ragas.llms import llm_factory

from evalvault.adapters.outbound.llm.openai_adapter import (
    TokenTrackingAsyncOpenAI,
    TokenUsage,
)
from evalvault.config.settings import Settings
from evalvault.ports.outbound.llm_port import LLMPort, ThinkingConfig


class ThinkingTokenTrackingAsyncOpenAI(TokenTrackingAsyncOpenAI):
    """TokenTrackingAsyncOpenAI extended with thinking parameter injection.

    Ollama의 thinking 기능을 지원하는 모델(gpt-oss-safeguard:20b 등)에
    think_level 파라미터를 자동으로 주입합니다.
    """

    def __init__(
        self,
        usage_tracker: TokenUsage,
        think_level: str | None = None,
        **kwargs: Any,
    ):
        """Initialize thinking-aware client.

        Args:
            usage_tracker: Token usage tracker
            think_level: Thinking level (e.g., 'medium') or None
            **kwargs: Additional arguments passed to AsyncOpenAI
        """
        # Set think_level BEFORE calling super().__init__()
        # because _create_tracking_chat() needs it during initialization
        self._think_level = think_level
        super().__init__(usage_tracker=usage_tracker, **kwargs)

    def _create_tracking_chat(self) -> Any:
        """Create a chat wrapper that tracks token usage and injects thinking params."""
        think_level = self._think_level

        class ThinkingTrackingCompletions:
            def __init__(inner_self, completions: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._completions = completions
                inner_self._tracker = tracker

            async def create(inner_self, **kwargs: Any) -> Any:  # noqa: N805
                # Inject thinking parameters if configured
                if think_level is not None:
                    # Ollama expects thinking params in extra_body.options
                    extra_body = kwargs.get("extra_body", {})
                    options = extra_body.get("options", {})
                    options["think_level"] = think_level
                    extra_body["options"] = options
                    kwargs["extra_body"] = extra_body

                # Call the original method and track usage
                response = await inner_self._completions.create(**kwargs)

                # Extract usage from response
                if hasattr(response, "usage") and response.usage:
                    inner_self._tracker.add(
                        prompt=response.usage.prompt_tokens or 0,
                        completion=response.usage.completion_tokens or 0,
                        total=response.usage.total_tokens or 0,
                    )
                return response

        class ThinkingTrackingChat:
            def __init__(inner_self, chat: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._chat = chat
                inner_self.completions = ThinkingTrackingCompletions(chat.completions, tracker)

        return ThinkingTrackingChat(self._original_chat, self._usage_tracker)


class OllamaAdapter(LLMPort):
    """Ollama LLM adapter using OpenAI-compatible API.

    폐쇄망 환경에서 로컬 Ollama 서버를 사용한 RAG 평가를 지원합니다.
    Ragas와의 호환성을 위해 OpenAI 호환 API를 사용합니다.

    Attributes:
        _model_name: 평가에 사용하는 LLM 모델명
        _embedding_model_name: 임베딩에 사용하는 모델명
        _base_url: Ollama 서버 URL
    """

    def __init__(self, settings: Settings):
        """Initialize Ollama adapter.

        Args:
            settings: Application settings containing Ollama configuration
        """
        self._settings = settings
        self._model_name = settings.ollama_model
        self._embedding_model_name = settings.ollama_embedding_model
        self._base_url = settings.ollama_base_url
        self._timeout = settings.ollama_timeout
        self._think_level = settings.ollama_think_level

        # Token usage tracker
        self._token_usage = TokenUsage()

        # Create HTTP client with custom timeout for Ollama
        http_client = httpx.AsyncClient(timeout=httpx.Timeout(self._timeout, connect=30.0))

        # Create OpenAI-compatible client pointing to Ollama
        # Ollama doesn't require a real API key
        # Use ThinkingTokenTrackingAsyncOpenAI to inject thinking parameters
        self._client = ThinkingTokenTrackingAsyncOpenAI(
            usage_tracker=self._token_usage,
            think_level=self._think_level,
            api_key="ollama",  # Dummy key for Ollama
            base_url=f"{self._base_url}/v1",
            http_client=http_client,
        )

        # Create Ragas LLM using OpenAI provider with Ollama backend
        self._ragas_llm = llm_factory(
            model=self._model_name,
            provider="openai",
            client=self._client,
        )

        # Create separate client for embeddings (non-tracking)
        self._embedding_client = AsyncOpenAI(
            api_key="ollama",
            base_url=f"{self._base_url}/v1",
            http_client=httpx.AsyncClient(timeout=httpx.Timeout(self._timeout, connect=30.0)),
        )

        # Create Ragas embeddings using OpenAI-compatible API
        self._ragas_embeddings = RagasOpenAIEmbeddings(
            model=self._embedding_model_name,
            client=self._embedding_client,
        )

    def get_model_name(self) -> str:
        """Get the model name being used.

        Returns:
            Model identifier with 'ollama/' prefix (e.g., 'ollama/gemma3:1b')
        """
        return f"ollama/{self._model_name}"

    def as_ragas_llm(self):
        """Return the Ragas LLM instance.

        Returns the Ragas-native LLM created via llm_factory for use
        with Ragas metrics evaluation.

        Returns:
            Ragas LLM instance configured with Ollama backend
        """
        return self._ragas_llm

    def as_ragas_embeddings(self):
        """Return the Ragas embeddings instance.

        Returns the Ragas-native embeddings for use with Ragas metrics
        like answer_relevancy and semantic_similarity.

        Returns:
            Ragas embeddings instance configured with Ollama backend
        """
        return self._ragas_embeddings

    def get_embedding_model_name(self) -> str:
        """Get the embedding model name being used.

        Returns:
            Embedding model identifier (e.g., 'qwen3-embedding:0.6b')
        """
        return self._embedding_model_name

    def get_token_usage(self) -> tuple[int, int, int]:
        """Get current token usage counts.

        Note: Ollama의 토큰 카운팅은 모델에 따라 정확하지 않을 수 있습니다.

        Returns:
            Tuple of (prompt_tokens, completion_tokens, total_tokens)
        """
        return (
            self._token_usage.prompt_tokens,
            self._token_usage.completion_tokens,
            self._token_usage.total_tokens,
        )

    def get_and_reset_token_usage(self) -> tuple[int, int, int]:
        """Get token usage and reset counters (atomic operation).

        Use this between test cases to get per-test-case token counts.

        Returns:
            Tuple of (prompt_tokens, completion_tokens, total_tokens)
        """
        return self._token_usage.get_and_reset()

    def reset_token_usage(self) -> None:
        """Reset token usage counters."""
        self._token_usage.reset()

    def get_base_url(self) -> str:
        """Get the Ollama server URL.

        Returns:
            Ollama server base URL
        """
        return self._base_url

    def get_think_level(self) -> str | None:
        """Get the thinking level for models that support it.

        Returns:
            Thinking level (e.g., 'medium') or None
        """
        return self._think_level

    def get_thinking_config(self) -> ThinkingConfig:
        """Get thinking/reasoning configuration for this adapter.

        Returns:
            ThinkingConfig with Ollama thinking settings
        """
        return ThinkingConfig(
            enabled=self._think_level is not None,
            budget_tokens=None,  # Not used for Ollama
            think_level=self._think_level,
        )
