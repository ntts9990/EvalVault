"""Azure OpenAI LLM adapter for Ragas evaluation."""

import threading
from dataclasses import dataclass, field

from openai import AsyncAzureOpenAI
from ragas.embeddings.base import embedding_factory
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


class AzureOpenAIAdapter(LLMPort):
    """Azure OpenAI Service adapter for Ragas evaluation.

    This adapter uses Azure OpenAI Service for enterprise environments,
    providing the same LLMPort interface as the standard OpenAI adapter.
    """

    def __init__(self, settings: Settings):
        """Initialize Azure OpenAI adapter.

        Args:
            settings: Application settings containing Azure OpenAI configuration

        Raises:
            ValueError: If required Azure settings are missing
        """
        self._settings = settings
        self._token_usage = TokenUsage()

        # Validate Azure settings
        if not settings.azure_endpoint:
            raise ValueError("AZURE_ENDPOINT is required for Azure OpenAI")
        if not settings.azure_api_key:
            raise ValueError("AZURE_API_KEY is required for Azure OpenAI")
        if not settings.azure_deployment:
            raise ValueError("AZURE_DEPLOYMENT is required for Azure OpenAI")

        # Create Azure OpenAI client
        self._client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_endpoint,
            api_key=settings.azure_api_key,
            api_version=settings.azure_api_version,
        )

        # Create Ragas LLM using llm_factory
        self._ragas_llm = llm_factory(
            model=settings.azure_deployment,
            provider="azure_openai",
            azure_endpoint=settings.azure_endpoint,
            api_key=settings.azure_api_key,
            api_version=settings.azure_api_version,
        )

        # Create Ragas embeddings if configured
        # Use embedding_factory with Azure client and deployment name as model
        if settings.azure_embedding_deployment:
            self._ragas_embeddings = embedding_factory(
                provider="openai",
                model=settings.azure_embedding_deployment,
                client=self._client,
            )
        else:
            self._ragas_embeddings = None

    def get_model_name(self) -> str:
        """Get the model name being used.

        Returns:
            Model identifier with 'azure/' prefix (e.g., 'azure/gpt-4')
        """
        return f"azure/{self._settings.azure_deployment}"

    def as_ragas_llm(self):
        """Return the Ragas LLM instance.

        Returns the Ragas-native LLM created via llm_factory for use
        with Ragas metrics evaluation.

        Returns:
            Ragas LLM instance configured with Azure OpenAI settings
        """
        return self._ragas_llm

    def as_ragas_embeddings(self):
        """Return the Ragas embeddings instance.

        Returns the Ragas-native embeddings for Azure OpenAI
        for use with Ragas metrics like answer_relevancy.

        Returns:
            Ragas embeddings instance configured with Azure OpenAI settings

        Raises:
            ValueError: If azure_embedding_deployment is not configured
        """
        if self._ragas_embeddings is None:
            raise ValueError("Azure embedding deployment not configured")
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
