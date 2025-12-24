"""Anthropic Claude LLM adapter for Ragas evaluation."""

import threading
from dataclasses import dataclass, field

from openai import AsyncOpenAI
from ragas.embeddings import OpenAIEmbeddings as RagasOpenAIEmbeddings
from ragas.llms import llm_factory

from evalvault.config.settings import Settings
from evalvault.ports.outbound.llm_port import LLMPort


@dataclass
class TokenUsage:
    """Thread-safe token usage tracker."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add(self, prompt: int, completion: int, total: int) -> None:
        """Add token counts (thread-safe)."""
        with self._lock:
            self.prompt_tokens += prompt
            self.completion_tokens += completion
            self.total_tokens += total

    def reset(self) -> None:
        """Reset all counters."""
        with self._lock:
            self.prompt_tokens = 0
            self.completion_tokens = 0
            self.total_tokens = 0

    def get_and_reset(self) -> tuple[int, int, int]:
        """Get current counts and reset (atomic operation)."""
        with self._lock:
            result = (self.prompt_tokens, self.completion_tokens, self.total_tokens)
            self.prompt_tokens = 0
            self.completion_tokens = 0
            self.total_tokens = 0
            return result


class AnthropicAdapter(LLMPort):
    """Anthropic Claude 어댑터.

    Ragas에서 Anthropic을 사용하기 위해 ragas.llms.llm_factory를 활용합니다.
    Embeddings는 Anthropic이 제공하지 않으므로 OpenAI Embeddings를 fallback으로 사용합니다.

    Example:
        >>> settings = Settings(
        ...     anthropic_api_key="sk-ant-...",
        ...     anthropic_model="claude-3-5-sonnet-20241022",
        ...     openai_api_key="sk-...",  # for embeddings
        ... )
        >>> adapter = AnthropicAdapter(settings)
        >>> llm = adapter.as_ragas_llm()
        >>> embeddings = adapter.as_ragas_embeddings()
    """

    def __init__(self, settings: Settings):
        """Initialize Anthropic adapter.

        Args:
            settings: Application settings containing Anthropic configuration

        Raises:
            ValueError: If ANTHROPIC_API_KEY is not provided
        """
        self._settings = settings
        self._token_usage = TokenUsage()

        # Validate Anthropic settings
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic")

        # Create Ragas LLM using llm_factory
        self._ragas_llm = llm_factory(
            model=settings.anthropic_model,
            provider="anthropic",
            api_key=settings.anthropic_api_key,
        )

        # Anthropic doesn't provide embeddings, use OpenAI as fallback
        self._ragas_embeddings = None
        if settings.openai_api_key:
            openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            self._ragas_embeddings = RagasOpenAIEmbeddings(
                model=settings.openai_embedding_model,
                client=openai_client,
            )

    def get_model_name(self) -> str:
        """Get the model name being used.

        Returns:
            Model identifier (e.g., 'claude-3-5-sonnet-20241022')
        """
        return self._settings.anthropic_model

    def as_ragas_llm(self):
        """Return the Ragas LLM instance.

        Returns the Ragas-native LLM created via llm_factory for use
        with Ragas metrics evaluation.

        Returns:
            Ragas LLM instance configured with Anthropic settings
        """
        return self._ragas_llm

    def as_ragas_embeddings(self):
        """Return the Ragas embeddings instance.

        Anthropic doesn't provide embeddings, so this returns OpenAI embeddings
        configured in the settings. OpenAI API key must be set for this to work.

        Returns:
            Ragas embeddings instance (OpenAI fallback)

        Raises:
            ValueError: If OpenAI API key is not provided for embeddings
        """
        if self._ragas_embeddings is None:
            raise ValueError(
                "Embeddings not available. Anthropic doesn't provide embeddings. "
                "Set OPENAI_API_KEY to use OpenAI embeddings as fallback."
            )
        return self._ragas_embeddings

    def get_token_usage(self) -> tuple[int, int, int]:
        """Get current token usage counts.

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
