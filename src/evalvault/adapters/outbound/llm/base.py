"""Shared helpers for LLM adapters."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from evalvault.ports.outbound.llm_port import LLMPort, ThinkingConfig

# Provider-specific help URLs
PROVIDER_HELP_URLS: dict[str, str] = {
    "openai": "https://platform.openai.com/api-keys",
    "azure": "https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub",
    "anthropic": "https://console.anthropic.com/settings/keys",
    "ollama": "https://ollama.com/download",
    "vllm": "https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html",
}


class LLMConfigurationError(ValueError):
    """LLM configuration error with user-friendly message.

    Provides clear error messages with actionable steps to fix configuration issues.
    """

    def __init__(
        self,
        setting_name: str,
        provider: str = "unknown",
        help_text: str | None = None,
    ):
        self.setting_name = setting_name
        self.provider = provider

        help_url = PROVIDER_HELP_URLS.get(provider, "")
        help_line = f"Get key: {help_url}" if help_url else ""
        extra_help = f"\n   {help_text}" if help_text else ""

        message = (
            f"{setting_name} is required for {provider.title()}\n"
            f"How to fix:\n"
            f"   1. Create .env file or set environment variable\n"
            f"   2. Add: {setting_name}=your-value{extra_help}\n"
            f"{help_line}"
        )
        super().__init__(message)


@dataclass
class TokenUsage:
    """Thread-safe token usage tracker shared by adapters."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add(self, prompt: int, completion: int, total: int | None = None) -> None:
        """Add token counts (thread-safe)."""
        with self._lock:
            self.prompt_tokens += prompt
            self.completion_tokens += completion
            self.total_tokens += total if total is not None else prompt + completion

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


class BaseLLMAdapter(LLMPort):
    """Common functionality for LLM adapters.

    Provides shared infrastructure for all LLM adapters:
    - Token usage tracking
    - Ragas LLM/Embeddings management
    - Thinking/reasoning configuration
    - Settings validation helpers
    """

    # Override in subclasses to specify the provider name
    provider_name: str = "unknown"

    def __init__(
        self,
        *,
        model_name: str,
        thinking_config: ThinkingConfig | None = None,
    ):
        self._model_name = model_name
        self._ragas_llm: Any | None = None
        self._ragas_embeddings: Any | None = None
        self._token_usage = TokenUsage()
        self._thinking_config = thinking_config or ThinkingConfig(enabled=False)

    # -- Settings validation helpers --------------------------------------------
    def _validate_required_settings(
        self,
        settings: dict[str, tuple[Any, str | None]],
    ) -> None:
        """Validate required settings and raise user-friendly errors.

        Args:
            settings: Dict mapping setting names to (value, help_text) tuples.
                      If value is falsy, raises LLMConfigurationError.

        Raises:
            LLMConfigurationError: If any required setting is missing

        Example:
            self._validate_required_settings({
                "AZURE_ENDPOINT": (settings.azure_endpoint, "Azure OpenAI endpoint URL"),
                "AZURE_API_KEY": (settings.azure_api_key, None),
            })
        """
        for setting_name, (value, help_text) in settings.items():
            if not value:
                raise LLMConfigurationError(
                    setting_name=setting_name,
                    provider=self.provider_name,
                    help_text=help_text,
                )

    # -- Helpers for subclasses -------------------------------------------------
    def _set_ragas_llm(self, llm: Any) -> None:
        self._ragas_llm = llm

    def _set_ragas_embeddings(self, embeddings: Any) -> None:
        self._ragas_embeddings = embeddings

    def _set_thinking_config(self, config: ThinkingConfig) -> None:
        self._thinking_config = config

    def _record_token_usage(self, prompt: int, completion: int, total: int | None = None) -> None:
        self._token_usage.add(prompt, completion, total)

    # -- LLMPort implementations ------------------------------------------------
    def get_model_name(self) -> str:
        return self._model_name

    def as_ragas_llm(self):
        if self._ragas_llm is None:
            raise ValueError("LLM not initialized. Call _set_ragas_llm() in the adapter.")
        return self._ragas_llm

    def as_ragas_embeddings(self):
        if self._ragas_embeddings is None:
            raise ValueError("Embeddings not configured for this adapter.")
        return self._ragas_embeddings

    def get_thinking_config(self) -> ThinkingConfig:
        return self._thinking_config

    def get_token_usage(self) -> tuple[int, int, int]:
        return (
            self._token_usage.prompt_tokens,
            self._token_usage.completion_tokens,
            self._token_usage.total_tokens,
        )

    def get_and_reset_token_usage(self) -> tuple[int, int, int]:
        return self._token_usage.get_and_reset()

    def reset_token_usage(self) -> None:
        self._token_usage.reset()


def create_openai_embeddings_with_legacy(
    model: str,
    client: Any,
) -> Any:
    """Create OpenAI embeddings with legacy LangChain-style methods.

    Ragas AnswerRelevancy metric expects embed_query/embed_documents methods
    but the modern RagasOpenAIEmbeddings only has embed_text/embed_texts.
    This factory creates a wrapper that adds the legacy methods for compatibility.

    Args:
        model: Embedding model name (e.g., 'text-embedding-3-small')
        client: AsyncOpenAI client instance

    Returns:
        OpenAIEmbeddings instance with legacy method compatibility
    """
    from ragas.embeddings import OpenAIEmbeddings as RagasOpenAIEmbeddings

    class OpenAIEmbeddingsWithLegacy(RagasOpenAIEmbeddings):
        """OpenAI embeddings with legacy LangChain-style methods."""

        def embed_query(self, text: str) -> list[float]:
            """Embed a single query text (LangChain-style method)."""
            return self.embed_text(text)

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            """Embed multiple documents (LangChain-style method)."""
            return self.embed_texts(texts)

        async def aembed_query(self, text: str) -> list[float]:
            """Async embed a single query text."""
            return await self.aembed_text(text)

        async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
            """Async embed multiple documents."""
            return await self.aembed_texts(texts)

    return OpenAIEmbeddingsWithLegacy(model=model, client=client)
