"""OpenAI LLM adapter for Ragas evaluation."""

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from evalvault.config.settings import Settings
from evalvault.ports.outbound.llm_port import LLMPort


class OpenAIAdapter(LLMPort):
    """OpenAI LLM adapter using LangChain.

    This adapter wraps LangChain's ChatOpenAI and OpenAIEmbeddings to provide
    a consistent interface for Ragas metrics evaluation.
    """

    def __init__(self, settings: Settings):
        """Initialize OpenAI adapter.

        Args:
            settings: Application settings containing OpenAI configuration
        """
        self._settings = settings
        self._model_name = settings.openai_model
        self._embedding_model_name = settings.openai_embedding_model

        # Build kwargs for ChatOpenAI
        llm_kwargs = {
            "model": self._model_name,
            "temperature": 0.0,  # Deterministic for evaluation
        }

        # Build kwargs for OpenAIEmbeddings
        embedding_kwargs = {
            "model": self._embedding_model_name,
        }

        # Add API key if provided
        if settings.openai_api_key:
            llm_kwargs["api_key"] = settings.openai_api_key
            embedding_kwargs["api_key"] = settings.openai_api_key

        # Add custom base URL if provided
        if settings.openai_base_url:
            llm_kwargs["openai_api_base"] = settings.openai_base_url
            embedding_kwargs["openai_api_base"] = settings.openai_base_url

        self._llm = ChatOpenAI(**llm_kwargs)
        self._embeddings = OpenAIEmbeddings(**embedding_kwargs)

    def get_model_name(self) -> str:
        """Get the model name being used.

        Returns:
            Model identifier (e.g., 'gpt-4o-mini')
        """
        return self._model_name

    def as_ragas_llm(self) -> ChatOpenAI:
        """Return the LangChain ChatOpenAI instance for Ragas.

        Ragas metrics expect LangChain LLM instances.

        Returns:
            ChatOpenAI instance configured with settings
        """
        return self._llm

    def as_ragas_embeddings(self) -> OpenAIEmbeddings:
        """Return the LangChain OpenAIEmbeddings instance for Ragas.

        Ragas metrics like answer_relevancy require embeddings.

        Returns:
            OpenAIEmbeddings instance configured with settings
        """
        return self._embeddings

    def get_embedding_model_name(self) -> str:
        """Get the embedding model name being used.

        Returns:
            Embedding model identifier (e.g., 'text-embedding-3-small')
        """
        return self._embedding_model_name
