"""OpenAI LLM adapter for Ragas evaluation."""

from typing import Any

from ragas.embeddings import OpenAIEmbeddings as RagasOpenAIEmbeddings

from evalvault.adapters.outbound.llm.base import BaseLLMAdapter
from evalvault.adapters.outbound.llm.instructor_factory import create_instructor_llm
from evalvault.adapters.outbound.llm.token_aware_chat import TokenTrackingAsyncOpenAI
from evalvault.config.settings import Settings


class OpenAIEmbeddingsWithLegacy(RagasOpenAIEmbeddings):
    """OpenAI embeddings with legacy LangChain-style methods.

    Ragas AnswerRelevancy metric expects embed_query/embed_documents methods
    but the modern RagasOpenAIEmbeddings only has embed_text/embed_texts.
    This wrapper adds the legacy methods for compatibility.
    """

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

        ragas_llm = create_instructor_llm("openai", self._model_name, self._client)
        self._set_ragas_llm(ragas_llm)

        embeddings = OpenAIEmbeddingsWithLegacy(
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

    async def agenerate_text(self, prompt: str) -> str:
        """Generate text from a prompt (async).

        Uses the OpenAI chat completions API directly for simple text generation.

        Args:
            prompt: The prompt to generate text from

        Returns:
            Generated text string
        """
        response = await self._client.chat.completions.create(
            model=self._model_name,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=8192,  # 긴 보고서를 위해 증가
        )
        return response.choices[0].message.content or ""

    def generate_text(self, prompt: str, *, json_mode: bool = False) -> str:
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
        api_kwargs: dict = {
            "model": self._model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": 8192,  # 긴 보고서를 위해 증가
        }

        # JSON 모드 설정
        if json_mode:
            api_kwargs["response_format"] = {"type": "json_object"}

        response = sync_client.chat.completions.create(**api_kwargs)
        return response.choices[0].message.content or ""
