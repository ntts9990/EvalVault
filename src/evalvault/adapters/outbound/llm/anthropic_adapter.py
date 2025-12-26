"""Anthropic Claude LLM adapter for Ragas evaluation."""

import threading
from dataclasses import dataclass, field
from typing import Any

from openai import AsyncOpenAI
from ragas.llms import llm_factory

from evalvault.adapters.outbound.llm.openai_adapter import OpenAIEmbeddingsWithLegacy
from evalvault.config.settings import Settings
from evalvault.ports.outbound.llm_port import LLMPort, ThinkingConfig


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


class ThinkingTokenTrackingAsyncAnthropic:
    """AsyncAnthropic wrapper with token tracking and extended thinking support.

    Wraps anthropic.AsyncAnthropic to:
    - Track token usage from responses
    - Inject extended thinking parameters for reasoning models
    - Maintain compatibility with Ragas llm_factory
    """

    def __init__(
        self,
        usage_tracker: TokenUsage,
        thinking_budget: int | None = None,
        **kwargs: Any,
    ):
        """Initialize thinking-aware Anthropic client.

        Args:
            usage_tracker: Token usage tracker
            thinking_budget: Token budget for extended thinking (None to disable)
            **kwargs: Additional arguments passed to AsyncAnthropic
        """
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError(
                "anthropic package is required for Anthropic adapter. "
                "Install with: uv pip install 'evalvault[anthropic]'"
            )

        self._client = AsyncAnthropic(**kwargs)
        self._usage_tracker = usage_tracker
        self._thinking_budget = thinking_budget
        self.messages = self._create_tracking_messages()

    def _create_tracking_messages(self) -> Any:
        """Create a messages wrapper that tracks usage and injects thinking params."""
        original_messages = self._client.messages
        thinking_budget = self._thinking_budget

        class ThinkingTrackingMessages:
            def __init__(inner_self, messages: Any, tracker: TokenUsage):
                inner_self._messages = messages
                inner_self._tracker = tracker

            async def create(inner_self, **kwargs: Any) -> Any:
                # Inject extended thinking parameters if configured
                if thinking_budget is not None and "thinking" not in kwargs:
                    kwargs["thinking"] = {
                        "type": "enabled",
                        "budget_tokens": thinking_budget,
                    }

                response = await inner_self._messages.create(**kwargs)

                # Extract usage from Anthropic response
                if hasattr(response, "usage") and response.usage:
                    inner_self._tracker.add(
                        prompt=response.usage.input_tokens or 0,
                        completion=response.usage.output_tokens or 0,
                        total=(response.usage.input_tokens or 0)
                        + (response.usage.output_tokens or 0),
                    )
                return response

        return ThinkingTrackingMessages(original_messages, self._usage_tracker)


class AnthropicAdapter(LLMPort):
    """Anthropic Claude 어댑터.

    Ragas에서 Anthropic을 사용하기 위해 ragas.llms.llm_factory를 활용합니다.
    Embeddings는 Anthropic이 제공하지 않으므로 OpenAI Embeddings를 fallback으로 사용합니다.

    Extended Thinking:
        anthropic_thinking_budget 설정으로 extended thinking을 활성화할 수 있습니다.
        이 기능은 Claude 3.5 Sonnet (20241022) 이상에서 지원됩니다.

    Example:
        >>> settings = Settings(
        ...     anthropic_api_key="sk-ant-...",
        ...     anthropic_model="claude-3-5-sonnet-20241022",
        ...     anthropic_thinking_budget=10000,  # Enable extended thinking
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
        self._thinking_budget = settings.anthropic_thinking_budget

        # Validate Anthropic settings
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic")

        # Create token-tracking Anthropic client with thinking support
        self._client = ThinkingTokenTrackingAsyncAnthropic(
            usage_tracker=self._token_usage,
            thinking_budget=self._thinking_budget,
            api_key=settings.anthropic_api_key,
        )

        # Create Ragas LLM using llm_factory with client (Ragas 0.4.x API)
        self._ragas_llm = llm_factory(
            model=settings.anthropic_model,
            provider="anthropic",
            client=self._client._client,  # Pass the actual AsyncAnthropic client
            max_tokens=8192,  # Claude default
        )

        # Anthropic doesn't provide embeddings, use OpenAI as fallback
        self._ragas_embeddings = None
        if settings.openai_api_key:
            openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            self._ragas_embeddings = OpenAIEmbeddingsWithLegacy(
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

    def get_thinking_config(self) -> ThinkingConfig:
        """Get thinking/reasoning configuration for this adapter.

        Returns:
            ThinkingConfig with Anthropic extended thinking settings
        """
        return ThinkingConfig(
            enabled=self._thinking_budget is not None,
            budget_tokens=self._thinking_budget,
            think_level=None,  # Not used for Anthropic
        )

    def get_thinking_budget(self) -> int | None:
        """Get the extended thinking token budget.

        Returns:
            Token budget for extended thinking, or None if disabled
        """
        return self._thinking_budget
