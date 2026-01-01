"""Azure OpenAI LLM adapter for Ragas evaluation."""

from openai import AsyncAzureOpenAI
from ragas.embeddings.base import embedding_factory
from ragas.llms import llm_factory

from evalvault.adapters.outbound.llm.base import BaseLLMAdapter
from evalvault.config.settings import Settings


class AzureOpenAIAdapter(BaseLLMAdapter):
    """Azure OpenAI Service adapter for Ragas evaluation.

    This adapter uses Azure OpenAI Service for enterprise environments,
    providing the same LLMPort interface as the standard OpenAI adapter.
    """

    def __init__(self, settings: Settings):
        """Initialize Azure OpenAI adapter.

        Args:
            settings: Application settings containing Azure OpenAI configuration

        Raises:
            ValueError: If required Azure settings are missing
        """
        self._settings = settings
        super().__init__(model_name=f"azure/{settings.azure_deployment}")

        # Validate Azure settings
        if not settings.azure_endpoint:
            raise ValueError("AZURE_ENDPOINT is required for Azure OpenAI")
        if not settings.azure_api_key:
            raise ValueError("AZURE_API_KEY is required for Azure OpenAI")
        if not settings.azure_deployment:
            raise ValueError("AZURE_DEPLOYMENT is required for Azure OpenAI")

        # Create Azure OpenAI client
        self._client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_endpoint,
            api_key=settings.azure_api_key,
            api_version=settings.azure_api_version,
        )

        # Create Ragas LLM using llm_factory
        ragas_llm = llm_factory(
            model=settings.azure_deployment,
            provider="azure_openai",
            azure_endpoint=settings.azure_endpoint,
            api_key=settings.azure_api_key,
            api_version=settings.azure_api_version,
        )
        self._set_ragas_llm(ragas_llm)

        # Create Ragas embeddings if configured
        # Use embedding_factory with Azure client and deployment name as model
        if settings.azure_embedding_deployment:
            embeddings = embedding_factory(
                provider="openai",
                model=settings.azure_embedding_deployment,
                client=self._client,
            )
            self._set_ragas_embeddings(embeddings)

    def as_ragas_embeddings(self):
        """Return the Ragas embeddings instance.

        Returns the Ragas-native embeddings for Azure OpenAI
        for use with Ragas metrics like answer_relevancy.

        Returns:
            Ragas embeddings instance configured with Azure OpenAI settings

        Raises:
            ValueError: If azure_embedding_deployment is not configured
        """
        if self._ragas_embeddings is None:
            raise ValueError("Azure embedding deployment not configured")
        return super().as_ragas_embeddings()
