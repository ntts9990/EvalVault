"""Token tracking clients shared by LLM adapters."""

from __future__ import annotations

from typing import Any

from openai import AsyncAzureOpenAI, AsyncOpenAI

from evalvault.adapters.outbound.llm.base import TokenUsage


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

        class TrackingCompletions:
            def __init__(inner_self, completions: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._completions = completions
                inner_self._tracker = tracker

            async def create(inner_self, **kwargs: Any) -> Any:  # noqa: N805
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
        **kwargs: Any,
    ):
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
                if think_level is not None:
                    extra_body = kwargs.get("extra_body", {})
                    options = extra_body.get("options", {})
                    options["think_level"] = think_level
                    extra_body["options"] = options
                    kwargs["extra_body"] = extra_body

                response = await inner_self._completions.create(**kwargs)

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


class TokenTrackingAsyncAzureOpenAI(AsyncAzureOpenAI):
    """Azure OpenAI client with token tracking."""

    def __init__(self, usage_tracker: TokenUsage, **kwargs: Any):
        super().__init__(**kwargs)
        self._usage_tracker = usage_tracker
        self._original_chat = self.chat
        self.chat = self._create_tracking_chat()

    def _create_tracking_chat(self) -> Any:
        """Create a chat wrapper that tracks token usage."""

        class TrackingCompletions:
            def __init__(inner_self, completions: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._completions = completions
                inner_self._tracker = tracker

            async def create(inner_self, **kwargs: Any) -> Any:  # noqa: N805
                response = await inner_self._completions.create(**kwargs)
                if hasattr(response, "usage") and response.usage:
                    inner_self._tracker.add(
                        prompt=response.usage.prompt_tokens or 0,
                        completion=response.usage.completion_tokens or 0,
                        total=response.usage.total_tokens or 0,
                    )
                return response

        class TrackingChat:
            def __init__(inner_self, chat: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._chat = chat
                inner_self.completions = TrackingCompletions(chat.completions, tracker)

        return TrackingChat(self._original_chat, self._usage_tracker)
