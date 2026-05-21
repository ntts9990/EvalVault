"""Shared helpers for LLM adapters."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict
from pydantic import Field as PydanticField

from evalvault.ports.outbound.llm_port import LLMPort, ThinkingConfig

logger = logging.getLogger(__name__)

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


class RetryPolicy(BaseModel):
    """Retry + timeout policy for outbound LLM/embedding calls.

    Shared by all LLM adapters via :class:`BaseLLMAdapter`. Treat instances as
    immutable — mutate by ``model_copy(update=...)`` rather than in-place.

    Fields:
        max_attempts: Total attempts (including the first call). ``1`` disables retry.
        backoff_seconds: Delay before the first retry, in seconds.
        backoff_multiplier: Multiplier applied to the delay after each retry
            (exponential backoff). ``1.0`` gives constant backoff.
        timeout_seconds: Per-attempt timeout for async calls (seconds). ``0`` or
            negative disables the wrapper timeout (the SDK's own timeout, if any,
            still applies). Sync helpers ignore this field and rely on SDK timeouts.
    """

    model_config = ConfigDict(frozen=True)

    max_attempts: int = PydanticField(
        default=3,
        ge=1,
        description="Total attempts including the first call; 1 disables retry.",
    )
    backoff_seconds: float = PydanticField(
        default=1.0,
        ge=0.0,
        description="Initial delay before the first retry, in seconds.",
    )
    backoff_multiplier: float = PydanticField(
        default=2.0,
        ge=1.0,
        description="Exponential backoff multiplier applied between retries.",
    )
    timeout_seconds: float = PydanticField(
        default=120.0,
        ge=0.0,
        description=(
            "Per-attempt timeout for async calls (seconds). "
            "Zero or negative disables the wrapper timeout."
        ),
    )


async def retry_async[T](
    func: Callable[..., Awaitable[T]],
    *args: Any,
    policy: RetryPolicy,
    **kwargs: Any,
) -> T:
    """Run ``await func(*args, **kwargs)`` with retry + per-attempt timeout.

    Retries on any :class:`Exception` (excluding ``KeyboardInterrupt`` /
    ``SystemExit``). When ``policy.timeout_seconds`` > 0, each attempt is wrapped
    with :func:`asyncio.wait_for`. Delay between retries grows exponentially per
    ``policy.backoff_multiplier``.
    """
    last_exc: BaseException | None = None
    delay = policy.backoff_seconds
    for attempt in range(1, policy.max_attempts + 1):
        try:
            coro = func(*args, **kwargs)
            if policy.timeout_seconds and policy.timeout_seconds > 0:
                return await asyncio.wait_for(coro, timeout=policy.timeout_seconds)
            return await coro
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as exc:  # noqa: BLE001 — structural retry wrapper
            last_exc = exc
            if attempt >= policy.max_attempts:
                break
            logger.warning(
                "LLM call failed (attempt %d/%d), retrying in %.2fs: %s",
                attempt,
                policy.max_attempts,
                delay,
                exc,
            )
            if delay > 0:
                await asyncio.sleep(delay)
            delay *= policy.backoff_multiplier
    assert last_exc is not None  # for type-checkers; loop only exits via break
    raise last_exc


def retry_sync[T](
    func: Callable[..., T],
    *args: Any,
    policy: RetryPolicy,
    **kwargs: Any,
) -> T:
    """Run ``func(*args, **kwargs)`` with retry and exponential backoff.

    Per-attempt timeout is NOT enforced here (no cross-platform sync primitive);
    callers must rely on the underlying SDK's timeout setting.
    """
    last_exc: BaseException | None = None
    delay = policy.backoff_seconds
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as exc:  # noqa: BLE001 — structural retry wrapper
            last_exc = exc
            if attempt >= policy.max_attempts:
                break
            logger.warning(
                "LLM call failed (attempt %d/%d), retrying in %.2fs: %s",
                attempt,
                policy.max_attempts,
                delay,
                exc,
            )
            if delay > 0:
                time.sleep(delay)
            delay *= policy.backoff_multiplier
    assert last_exc is not None
    raise last_exc


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

    # Class-level default retry policy; subclasses may override or callers may
    # pass ``retry_policy`` to the constructor for per-adapter customisation.
    default_retry_policy: ClassVar[RetryPolicy] = RetryPolicy()

    def __init__(
        self,
        *,
        model_name: str,
        thinking_config: ThinkingConfig | None = None,
        retry_policy: RetryPolicy | None = None,
    ):
        self._model_name = model_name
        self._ragas_llm: Any | None = None
        self._ragas_embeddings: Any | None = None
        self._token_usage = TokenUsage()
        self._thinking_config = thinking_config or ThinkingConfig(enabled=False)
        self._retry_policy = retry_policy or self.default_retry_policy

    # -- Retry helpers ----------------------------------------------------------
    def get_retry_policy(self) -> RetryPolicy:
        """Return the active retry policy for this adapter."""
        return self._retry_policy

    async def _retry_async[T](
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Wrap ``await func(*args, **kwargs)`` with the adapter's retry policy."""
        return await retry_async(func, *args, policy=self._retry_policy, **kwargs)

    def _retry_sync[T](
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Wrap ``func(*args, **kwargs)`` with the adapter's retry policy."""
        return retry_sync(func, *args, policy=self._retry_policy, **kwargs)

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
