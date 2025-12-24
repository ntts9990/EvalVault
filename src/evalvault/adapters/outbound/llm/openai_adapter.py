"""OpenAI LLM adapter for Ragas evaluation."""

import threading
from dataclasses import dataclass, field
from typing import Any

from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.embeddings import OpenAIEmbeddings as RagasOpenAIEmbeddings

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


class TokenTrackingAsyncOpenAI(AsyncOpenAI):
    """AsyncOpenAI wrapper that tracks token usage from responses."""

    def __init__(self, usage_tracker: TokenUsage, **kwargs: Any):
        super().__init__(**kwargs)
        self._usage_tracker = usage_tracker
        self._original_chat = self.chat

        # Wrap chat.completions.create to capture usage
        self.chat = self._create_tracking_chat()

    def _create_tracking_chat(self) -> Any:
        """Create a chat wrapper that tracks token usage."""
        original_completions = self._original_chat.completions

        class TrackingCompletions:
            def __init__(inner_self, completions: Any, tracker: TokenUsage):
                inner_self._completions = completions
                inner_self._tracker = tracker

            async def create(inner_self, **kwargs: Any) -> Any:
                response = await inner_self._completions.create(**kwargs)
                # Extract usage from response
                if hasattr(response, "usage") and response.usage:
                    inner_self._tracker.add(
                        prompt=response.usage.prompt_tokens or 0,
                        completion=response.usage.completion_tokens or 0,
                        total=response.usage.total_tokens or 0,
                    )
                return response

        class TrackingChat:
            def __init__(inner_self, chat: Any, tracker: TokenUsage):
                inner_self._chat = chat
                inner_self.completions = TrackingCompletions(chat.completions, tracker)

        return TrackingChat(self._original_chat, self._usage_tracker)


class OpenAIAdapter(LLMPort):
    """OpenAI LLM adapter using Ragas native interface.

    This adapter uses Ragas's llm_factory and embedding_factory to provide
    a consistent interface for Ragas metrics evaluation without deprecation warnings.
    """

    def __init__(self, settings: Settings):
        """Initialize OpenAI adapter.

        Args:
            settings: Application settings containing OpenAI configuration
        """
        self._settings = settings
        self._model_name = settings.openai_model
        self._embedding_model_name = settings.openai_embedding_model

        # Token usage tracker
        self._token_usage = TokenUsage()

        # Build OpenAI client kwargs
        client_kwargs = {}
        if settings.openai_api_key:
            client_kwargs["api_key"] = settings.openai_api_key
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url

        # Create token-tracking async OpenAI client
        self._client = TokenTrackingAsyncOpenAI(
            usage_tracker=self._token_usage,
            **client_kwargs,
        )

        # Create Ragas LLM using llm_factory with tracking client
        # gpt-5-nano/mini: 400K context, 128K max output tokens
        self._ragas_llm = llm_factory(
            model=self._model_name,
            provider="openai",
            client=self._client,
            max_tokens=32768,  # gpt-5 series supports up to 128K output tokens
        )

        # Create Ragas embeddings using OpenAIEmbeddings with tracking client
        self._ragas_embeddings = RagasOpenAIEmbeddings(
            model=self._embedding_model_name,
            client=self._client,
        )

    def get_model_name(self) -> str:
        """Get the model name being used.

        Returns:
            Model identifier (e.g., 'gpt-4o-mini')
        """
        return self._model_name

    def as_ragas_llm(self):
        """Return the Ragas LLM instance.

        Returns the Ragas-native LLM created via llm_factory for use
        with Ragas metrics evaluation.

        Returns:
            Ragas LLM instance configured with settings
        """
        return self._ragas_llm

    def as_ragas_embeddings(self):
        """Return the Ragas embeddings instance.

        Returns the Ragas-native embeddings created via embedding_factory
        for use with Ragas metrics like answer_relevancy.

        Returns:
            Ragas embeddings instance configured with settings
        """
        return self._ragas_embeddings

    def get_embedding_model_name(self) -> str:
        """Get the embedding model name being used.

        Returns:
            Embedding model identifier (e.g., 'text-embedding-3-small')
        """
        return self._embedding_model_name

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
