"""OpenAI LLM adapter for Ragas evaluation."""

from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.embeddings import OpenAIEmbeddings as RagasOpenAIEmbeddings

from evalvault.config.settings import Settings
from evalvault.ports.outbound.llm_port import LLMPort


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

        # Build OpenAI client kwargs
        client_kwargs = {}
        if settings.openai_api_key:
            client_kwargs["api_key"] = settings.openai_api_key
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url

        # Create async OpenAI client for async evaluation
        self._client = AsyncOpenAI(**client_kwargs)

        # Create Ragas LLM using llm_factory with async client
        # gpt-5-nano/mini: 400K context, 128K max output tokens
        self._ragas_llm = llm_factory(
            model=self._model_name,
            provider="openai",
            client=self._client,
            max_tokens=32768,  # gpt-5 series supports up to 128K output tokens
        )

        # Create Ragas embeddings using OpenAIEmbeddings with async client
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
