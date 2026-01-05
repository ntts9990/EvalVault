"""Token tracking clients shared by LLM adapters."""

from __future__ import annotations

from typing import Any

from openai import AsyncAzureOpenAI, AsyncOpenAI

from evalvault.adapters.outbound.llm.base import TokenUsage
from evalvault.config.phoenix_support import instrumentation_span, set_span_attributes


def _build_llm_span_attrs(provider: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Extract common LLM span attributes."""

    model = kwargs.get("model")
    attrs = {
        "llm.provider": provider,
        "llm.model": model,
        "llm.max_completion_tokens": kwargs.get("max_completion_tokens")
        or kwargs.get("max_tokens"),
        "llm.temperature": kwargs.get("temperature"),
    }
    return {k: v for k, v in attrs.items() if v is not None}


def _record_usage_attributes(span: Any, prompt: int, completion: int) -> None:
    """Attach token usage info to a span."""

    if span is None:
        return
    set_span_attributes(
        span,
        {
            "llm.usage.prompt_tokens": prompt,
            "llm.usage.completion_tokens": completion,
            "llm.usage.total_tokens": prompt + completion,
        },
    )


class TokenTrackingAsyncOpenAI(AsyncOpenAI):
    """AsyncOpenAI wrapper that tracks token usage from responses."""

    def __init__(
        self,
        usage_tracker: TokenUsage,
        *,
        provider_name: str = "openai",
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._usage_tracker = usage_tracker
        self._original_chat = self.chat
        self._provider_name = provider_name

        # Wrap chat.completions.create to capture usage
        self.chat = self._create_tracking_chat()

    def _create_tracking_chat(self) -> Any:
        """Create a chat wrapper that tracks token usage."""

        provider_name = self._provider_name

        class TrackingCompletions:
            def __init__(inner_self, completions: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._completions = completions
                inner_self._tracker = tracker

            async def create(inner_self, **kwargs: Any) -> Any:  # noqa: N805
                # Force high token limit for reasoning models
                if "max_completion_tokens" not in kwargs or kwargs["max_completion_tokens"] < 4096:
                    kwargs["max_completion_tokens"] = 16384

                # Remove max_tokens if present to avoid conflicts with reasoning models
                if "max_tokens" in kwargs:
                    del kwargs["max_tokens"]

                span_attrs = _build_llm_span_attrs(provider_name, kwargs)
                with instrumentation_span("llm.chat_completion", span_attrs) as span:
                    response = await inner_self._completions.create(**kwargs)
                    # Extract usage from response
                    if hasattr(response, "usage") and response.usage:
                        prompt_tokens = response.usage.prompt_tokens or 0
                        completion_tokens = response.usage.completion_tokens or 0
                        total_tokens = response.usage.total_tokens or 0
                        inner_self._tracker.add(
                            prompt=prompt_tokens,
                            completion=completion_tokens,
                            total=total_tokens,
                        )
                        _record_usage_attributes(span, prompt_tokens, completion_tokens)
                return response

        class TrackingChat:
            def __init__(inner_self, chat: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._chat = chat
                inner_self.completions = TrackingCompletions(chat.completions, tracker)

        return TrackingChat(self._original_chat, self._usage_tracker)


class ThinkingTokenTrackingAsyncOpenAI(TokenTrackingAsyncOpenAI):
    """TokenTrackingAsyncOpenAI extended with thinking parameter injection."""

    def __init__(
        self,
        usage_tracker: TokenUsage,
        think_level: str | None = None,
        provider_name: str = "openai",
        **kwargs: Any,
    ):
        self._think_level = think_level
        super().__init__(usage_tracker=usage_tracker, provider_name=provider_name, **kwargs)

    def _create_tracking_chat(self) -> Any:
        """Create a chat wrapper that tracks token usage and injects thinking params."""
        think_level = self._think_level
        provider_name = self._provider_name

        class ThinkingTrackingCompletions:
            def __init__(inner_self, completions: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._completions = completions
                inner_self._tracker = tracker

            async def create(inner_self, **kwargs: Any) -> Any:  # noqa: N805
                # Ensure 충분한 출력 토큰 확보 (Ollama는 max_tokens를 사용)
                if provider_name == "ollama":
                    if "max_tokens" not in kwargs or kwargs["max_tokens"] < 4096:
                        kwargs["max_tokens"] = 16384
                else:
                    if (
                        "max_completion_tokens" not in kwargs
                        or kwargs["max_completion_tokens"] < 4096
                    ):
                        kwargs["max_completion_tokens"] = 16384
                    if "max_tokens" in kwargs:
                        del kwargs["max_tokens"]

                if think_level is not None:
                    extra_body = kwargs.get("extra_body", {})
                    options = extra_body.get("options", {})
                    options["think_level"] = think_level
                    extra_body["options"] = options
                    kwargs["extra_body"] = extra_body

                span_attrs = _build_llm_span_attrs(provider_name, kwargs)
                with instrumentation_span("llm.chat_completion", span_attrs) as span:
                    response = await inner_self._completions.create(**kwargs)

                    if hasattr(response, "usage") and response.usage:
                        prompt_tokens = response.usage.prompt_tokens or 0
                        completion_tokens = response.usage.completion_tokens or 0
                        total_tokens = response.usage.total_tokens or 0
                        inner_self._tracker.add(
                            prompt=prompt_tokens,
                            completion=completion_tokens,
                            total=total_tokens,
                        )
                        _record_usage_attributes(span, prompt_tokens, completion_tokens)
                return response

        class ThinkingTrackingChat:
            def __init__(inner_self, chat: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._chat = chat
                inner_self.completions = ThinkingTrackingCompletions(chat.completions, tracker)

        return ThinkingTrackingChat(self._original_chat, self._usage_tracker)


class TokenTrackingAsyncAzureOpenAI(AsyncAzureOpenAI):
    """Azure OpenAI client with token tracking."""

    def __init__(self, usage_tracker: TokenUsage, **kwargs: Any):
        super().__init__(**kwargs)
        self._usage_tracker = usage_tracker
        self._original_chat = self.chat
        self._provider_name = "azure-openai"
        self.chat = self._create_tracking_chat()

    def _create_tracking_chat(self) -> Any:
        """Create a chat wrapper that tracks token usage."""

        class TrackingCompletions:
            def __init__(inner_self, completions: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._completions = completions
                inner_self._tracker = tracker

            async def create(inner_self, **kwargs: Any) -> Any:  # noqa: N805
                span_attrs = _build_llm_span_attrs("azure-openai", kwargs)
                with instrumentation_span("llm.chat_completion", span_attrs) as span:
                    response = await inner_self._completions.create(**kwargs)
                    if hasattr(response, "usage") and response.usage:
                        prompt_tokens = response.usage.prompt_tokens or 0
                        completion_tokens = response.usage.completion_tokens or 0
                        total_tokens = response.usage.total_tokens or 0
                        inner_self._tracker.add(
                            prompt=prompt_tokens,
                            completion=completion_tokens,
                            total=total_tokens,
                        )
                        _record_usage_attributes(span, prompt_tokens, completion_tokens)
                return response

        class TrackingChat:
            def __init__(inner_self, chat: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._chat = chat
                inner_self.completions = TrackingCompletions(chat.completions, tracker)

        return TrackingChat(self._original_chat, self._usage_tracker)
