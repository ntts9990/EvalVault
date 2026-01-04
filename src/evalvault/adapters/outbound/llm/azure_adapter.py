"""Azure OpenAI LLM adapter for Ragas evaluation."""

from ragas.embeddings.base import BaseRagasEmbeddings, embedding_factory

from evalvault.adapters.outbound.llm.base import BaseLLMAdapter
from evalvault.adapters.outbound.llm.instructor_factory import create_instructor_llm
from evalvault.adapters.outbound.llm.token_aware_chat import TokenTrackingAsyncAzureOpenAI
from evalvault.config.settings import Settings


class AzureOpenAIAdapter(BaseLLMAdapter):
    """Azure OpenAI Service adapter for Ragas evaluation.

    This adapter uses Azure OpenAI Service for enterprise environments,
    providing the same LLMPort interface as the standard OpenAI adapter.
    """

    provider_name = "azure"

    def __init__(self, settings: Settings):
        """Initialize Azure OpenAI adapter.

        Args:
            settings: Application settings containing Azure OpenAI configuration

        Raises:
            LLMConfigurationError: If required Azure settings are missing
        """
        self._settings = settings
        super().__init__(model_name=f"azure/{settings.azure_deployment or 'unset'}")

        # Validate Azure settings using common helper
        self._validate_required_settings(
            {
                "AZURE_ENDPOINT": (settings.azure_endpoint, "Azure OpenAI endpoint URL"),
                "AZURE_API_KEY": (settings.azure_api_key, None),
                "AZURE_DEPLOYMENT": (settings.azure_deployment, "Azure OpenAI deployment name"),
            }
        )

        # Update model name after validation
        self._model_name = f"azure/{settings.azure_deployment}"

        # Create Azure OpenAI client
        self._client = TokenTrackingAsyncAzureOpenAI(
            usage_tracker=self._token_usage,
            azure_endpoint=settings.azure_endpoint,
            api_key=settings.azure_api_key,
            api_version=settings.azure_api_version,
        )

        ragas_llm = create_instructor_llm("openai", settings.azure_deployment, self._client)
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

    def as_ragas_embeddings(self) -> BaseRagasEmbeddings:
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
