"""OpenAI LLM adapter for Ragas evaluation."""

from typing import Any

from evalvault.adapters.outbound.llm.base import (
    BaseLLMAdapter,
    create_openai_embeddings_with_legacy,
)
from evalvault.adapters.outbound.llm.instructor_factory import create_instructor_llm
from evalvault.adapters.outbound.llm.token_aware_chat import TokenTrackingAsyncOpenAI
from evalvault.config.phoenix_support import instrumentation_span, set_span_attributes
from evalvault.config.settings import Settings
from evalvault.ports.outbound.llm_port import GenerationOptions

_DEFAULT_MAX_COMPLETION_TOKENS = 8192
_GPT5_MAX_COMPLETION_TOKENS = 16384


def _max_completion_tokens_for_model(model_name: str) -> int:
    """Choose a safe max_completion_tokens for the given model."""
    if model_name.startswith("gpt-5"):
        return _GPT5_MAX_COMPLETION_TOKENS
    return _DEFAULT_MAX_COMPLETION_TOKENS


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI LLM adapter using Ragas native interface.

    This adapter uses Ragas's llm_factory and embedding_factory to provide
    a consistent interface for Ragas metrics evaluation without deprecation warnings.
    """

    provider_name = "openai"

    def __init__(self, settings: Settings):
        """Initialize OpenAI adapter.

        Args:
            settings: Application settings containing OpenAI configuration
        """
        self._settings = settings
        super().__init__(model_name=settings.openai_model)
        self._embedding_model_name = settings.openai_embedding_model

        client_kwargs: dict[str, Any] = {}
        if settings.openai_api_key:
            client_kwargs["api_key"] = settings.openai_api_key
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url

        # Create token-tracking async OpenAI client
        self._client = TokenTrackingAsyncOpenAI(
            usage_tracker=self._token_usage,
            **client_kwargs,
        )

        # Ragas requires high token limit for reasoning models
        ragas_llm = create_instructor_llm(
            "openai", self._model_name, self._client, max_completion_tokens=16384
        )
        self._set_ragas_llm(ragas_llm)

        embeddings = create_openai_embeddings_with_legacy(
            model=self._embedding_model_name,
            client=self._client,
        )
        self._set_ragas_embeddings(embeddings)

    def get_embedding_model_name(self) -> str:
        """Get the embedding model name being used.

        Returns:
            Embedding model identifier (e.g., 'text-embedding-3-small')
        """
        return self._embedding_model_name

    async def agenerate_text(
        self,
        prompt: str,
        *,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate text from a prompt (async).

        Uses the OpenAI chat completions API directly for simple text generation.

        Args:
            prompt: The prompt to generate text from

        Returns:
            Generated text string
        """
        attrs = {
            "llm.provider": "openai",
            "llm.model": self._model_name,
            "llm.mode": "async",
        }
        max_tokens = options.max_tokens if options and options.max_tokens is not None else None
        api_kwargs = {
            "model": self._model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": max_tokens
            or _max_completion_tokens_for_model(self._model_name),
        }
        if options and options.temperature is not None:
            api_kwargs["temperature"] = options.temperature
        if options and options.top_p is not None:
            api_kwargs["top_p"] = options.top_p
        if options and options.n is not None:
            api_kwargs["n"] = options.n
        if options and options.seed is not None:
            api_kwargs["seed"] = options.seed
        with instrumentation_span("llm.generate_text", attrs) as span:
            response = await self._client.chat.completions.create(**api_kwargs)
            content = response.choices[0].message.content or ""
            if span:
                set_span_attributes(span, {"llm.response.length": len(content)})
        return content

    def generate_text(
        self,
        prompt: str,
        *,
        json_mode: bool = False,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate text from a prompt (sync).

        Uses sync OpenAI client directly.

        Args:
            prompt: The prompt to generate text from
            json_mode: If True, force JSON response format

        Returns:
            Generated text string
        """
        from openai import OpenAI

        # 동기 클라이언트 생성
        client_kwargs = {}
        if self._settings.openai_api_key:
            client_kwargs["api_key"] = self._settings.openai_api_key
        if self._settings.openai_base_url:
            client_kwargs["base_url"] = self._settings.openai_base_url

        sync_client = OpenAI(**client_kwargs)

        # API 호출 파라미터
        max_tokens = options.max_tokens if options and options.max_tokens is not None else None
        api_kwargs: dict = {
            "model": self._model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": max_tokens
            or _max_completion_tokens_for_model(self._model_name),
        }
        if options and options.temperature is not None:
            api_kwargs["temperature"] = options.temperature
        if options and options.top_p is not None:
            api_kwargs["top_p"] = options.top_p
        if options and options.n is not None:
            api_kwargs["n"] = options.n
        if options and options.seed is not None:
            api_kwargs["seed"] = options.seed

        # JSON 모드 설정
        if json_mode:
            api_kwargs["response_format"] = {"type": "json_object"}

        attrs = {
            "llm.provider": "openai",
            "llm.model": self._model_name,
            "llm.mode": "sync",
        }
        with instrumentation_span("llm.generate_text", attrs) as span:
            response = sync_client.chat.completions.create(**api_kwargs)
            content = response.choices[0].message.content or ""
            if span:
                set_span_attributes(span, {"llm.response.length": len(content)})
        return content
