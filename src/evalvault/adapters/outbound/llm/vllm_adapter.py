"""vLLM LLM adapter for OpenAI-compatible serving."""

from typing import Any

from openai import AsyncOpenAI, OpenAI

from evalvault.adapters.outbound.llm.base import (
    BaseLLMAdapter,
    create_openai_embeddings_with_legacy,
)
from evalvault.adapters.outbound.llm.instructor_factory import create_instructor_llm
from evalvault.adapters.outbound.llm.token_aware_chat import TokenTrackingAsyncOpenAI
from evalvault.config.phoenix_support import instrumentation_span, set_span_attributes
from evalvault.config.settings import Settings


class VLLMAdapter(BaseLLMAdapter):
    """vLLM adapter using OpenAI-compatible API."""

    provider_name = "vllm"

    def __init__(self, settings: Settings):
        self._settings = settings
        super().__init__(model_name=settings.vllm_model)
        self._embedding_model_name = settings.vllm_embedding_model

        base_url = settings.vllm_base_url
        api_key = settings.vllm_api_key or "local"

        client_kwargs: dict[str, Any] = {
            "base_url": base_url,
            "api_key": api_key,
            "timeout": settings.vllm_timeout,
        }

        self._client = TokenTrackingAsyncOpenAI(
            usage_tracker=self._token_usage,
            provider_name="vllm",
            **client_kwargs,
        )

        ragas_llm = create_instructor_llm(
            "vllm",
            self._model_name,
            self._client,
            max_completion_tokens=16384,
        )
        self._set_ragas_llm(ragas_llm)

        embed_base_url = settings.vllm_embedding_base_url or settings.vllm_base_url
        embedding_client = AsyncOpenAI(
            base_url=embed_base_url,
            api_key=api_key,
            timeout=settings.vllm_timeout,
        )
        embeddings = create_openai_embeddings_with_legacy(
            model=self._embedding_model_name,
            client=embedding_client,
        )
        self._set_ragas_embeddings(embeddings)

    def get_embedding_model_name(self) -> str:
        """Get the embedding model name being used."""
        return self._embedding_model_name

    async def agenerate_text(self, prompt: str) -> str:
        """Generate text from a prompt (async)."""
        attrs = {
            "llm.provider": "vllm",
            "llm.model": self._model_name,
            "llm.mode": "async",
        }
        with instrumentation_span("llm.generate_text", attrs) as span:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=8192,
            )
            content = response.choices[0].message.content or ""
            if span:
                set_span_attributes(span, {"llm.response.length": len(content)})
        return content

    def generate_text(self, prompt: str, *, json_mode: bool = False) -> str:
        """Generate text from a prompt (sync)."""
        sync_client = OpenAI(
            base_url=self._settings.vllm_base_url,
            api_key=self._settings.vllm_api_key or "local",
            timeout=self._settings.vllm_timeout,
        )

        api_kwargs: dict = {
            "model": self._model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": 8192,
        }
        if json_mode:
            api_kwargs["response_format"] = {"type": "json_object"}

        attrs = {
            "llm.provider": "vllm",
            "llm.model": self._model_name,
            "llm.mode": "sync",
        }
        with instrumentation_span("llm.generate_text", attrs) as span:
            response = sync_client.chat.completions.create(**api_kwargs)
            content = response.choices[0].message.content or ""
            if span:
                set_span_attributes(span, {"llm.response.length": len(content)})
        return content
