"""Anthropic Claude LLM adapter for Ragas evaluation."""

from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from evalvault.adapters.outbound.llm.base import (
    BaseLLMAdapter,
    TokenUsage,
    create_openai_embeddings_with_legacy,
)
from evalvault.adapters.outbound.llm.instructor_factory import create_instructor_llm
from evalvault.config.phoenix_support import instrumentation_span, set_span_attributes
from evalvault.config.settings import Settings
from evalvault.ports.outbound.llm_port import GenerationOptions, ThinkingConfig

try:  # Optional dependency
    from anthropic import AsyncAnthropic
except ImportError:  # pragma: no cover - handled at runtime
    AsyncAnthropic = None  # type: ignore[arg-type]


class ThinkingTokenTrackingAsyncAnthropic:
    """AsyncAnthropic wrapper with token tracking and extended thinking support."""

    def __init__(
        self,
        usage_tracker: TokenUsage,
        thinking_budget: int | None = None,
        **kwargs: Any,
    ):
        if AsyncAnthropic is None:
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
            def __init__(inner_self, messages: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._messages = messages
                inner_self._tracker = tracker

            async def create(inner_self, **kwargs: Any) -> Any:  # noqa: N805
                if thinking_budget is not None and "thinking" not in kwargs:
                    kwargs["thinking"] = {
                        "type": "enabled",
                        "budget_tokens": thinking_budget,
                    }

                attrs = {
                    "llm.provider": "anthropic",
                    "llm.model": kwargs.get("model"),
                    "llm.thinking.enabled": thinking_budget is not None,
                }
                with instrumentation_span("llm.messages", attrs) as span:
                    response = await inner_self._messages.create(**kwargs)

                    if hasattr(response, "usage") and response.usage:
                        prompt_tokens = response.usage.input_tokens or 0
                        completion_tokens = response.usage.output_tokens or 0
                        inner_self._tracker.add(
                            prompt=prompt_tokens,
                            completion=completion_tokens,
                            total=prompt_tokens + completion_tokens,
                        )
                        set_span_attributes(
                            span,
                            {
                                "llm.usage.prompt_tokens": prompt_tokens,
                                "llm.usage.completion_tokens": completion_tokens,
                                "llm.usage.total_tokens": prompt_tokens + completion_tokens,
                            },
                        )
                return response

        return ThinkingTrackingMessages(original_messages, self._usage_tracker)


class AnthropicAdapter(BaseLLMAdapter):
    """Anthropic Claude 어댑터."""

    provider_name = "anthropic"

    def __init__(self, settings: Settings):
        """Initialize Anthropic adapter."""
        self._settings = settings
        self._thinking_budget = settings.anthropic_thinking_budget
        thinking_config = ThinkingConfig(
            enabled=self._thinking_budget is not None,
            budget_tokens=self._thinking_budget,
            think_level=None,
        )
        super().__init__(
            model_name=settings.anthropic_model,
            thinking_config=thinking_config,
        )

        # Validate Anthropic settings using common helper
        self._validate_required_settings(
            {
                "ANTHROPIC_API_KEY": (settings.anthropic_api_key, None),
            }
        )

        self._anthropic_client = ThinkingTokenTrackingAsyncAnthropic(
            usage_tracker=self._token_usage,
            thinking_budget=self._thinking_budget,
            api_key=settings.anthropic_api_key,
        )

        ragas_llm = create_instructor_llm(
            "anthropic", settings.anthropic_model, self._anthropic_client._client
        )
        self._set_ragas_llm(ragas_llm)

        # Anthropic doesn't provide embeddings, use OpenAI as fallback
        if settings.openai_api_key:
            openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            embeddings = create_openai_embeddings_with_legacy(
                model=settings.openai_embedding_model,
                client=openai_client,
            )
            self._set_ragas_embeddings(embeddings)

    def as_ragas_embeddings(self):
        """Return the Ragas embeddings instance."""
        if self._ragas_embeddings is None:
            raise ValueError(
                "Embeddings not available. Anthropic doesn't provide embeddings. "
                "Set OPENAI_API_KEY to use OpenAI embeddings as fallback."
            )
        return super().as_ragas_embeddings()

    def get_thinking_budget(self) -> int | None:
        """Get the extended thinking token budget."""
        return self._thinking_budget

    async def agenerate_text(
        self,
        prompt: str,
        *,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate text from a prompt (async).

        Uses the Anthropic messages API for simple text generation.

        Args:
            prompt: The prompt to generate text from

        Returns:
            Generated text string
        """
        max_tokens = options.max_tokens if options and options.max_tokens is not None else 8192
        api_kwargs: dict[str, Any] = {}
        if options and options.temperature is not None:
            api_kwargs["temperature"] = options.temperature
        if options and options.top_p is not None:
            api_kwargs["top_p"] = options.top_p
        response = await self._anthropic_client.messages.create(
            model=self._model_name,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **api_kwargs,
        )
        # Extract text from response content blocks
        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        return "".join(text_parts)

    def generate_text(
        self,
        prompt: str,
        *,
        json_mode: bool = False,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate text from a prompt (sync).

        Args:
            prompt: The prompt to generate text from
            json_mode: If True, force JSON response format

        Returns:
            Generated text string
        """
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            try:
                import nest_asyncio

                nest_asyncio.apply()
                return loop.run_until_complete(self.agenerate_text(prompt, options=options))
            except ImportError:
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self.agenerate_text(prompt, options=options)
                    )
                    return future.result()
        else:
            return asyncio.run(self.agenerate_text(prompt, options=options))
