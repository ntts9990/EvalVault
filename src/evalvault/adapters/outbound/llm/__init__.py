"""LLM adapters."""

from evalvault.adapters.outbound.llm.anthropic_adapter import AnthropicAdapter
from evalvault.adapters.outbound.llm.azure_adapter import AzureOpenAIAdapter
from evalvault.adapters.outbound.llm.base import (
    BaseLLMAdapter,
    LLMConfigurationError,
    create_openai_embeddings_with_legacy,
)
from evalvault.adapters.outbound.llm.llm_relation_augmenter import LLMRelationAugmenter
from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter
from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter
from evalvault.config.settings import Settings
from evalvault.ports.outbound.llm_port import LLMPort


def get_llm_adapter(settings: Settings) -> LLMPort:
    """Factory function to create appropriate LLM adapter.

    프로바이더 설정에 따라 적절한 LLM 어댑터를 생성합니다.

    Args:
        settings: Application settings

    Returns:
        LLMPort implementation based on settings.llm_provider

    Raises:
        ValueError: Unsupported provider

    Examples:
        # OpenAI 사용
        settings.llm_provider = "openai"
        llm = get_llm_adapter(settings)

        # Ollama 사용 (폐쇄망)
        settings.llm_provider = "ollama"
        llm = get_llm_adapter(settings)
    """
    provider = settings.llm_provider.lower()

    if provider == "openai":
        return OpenAIAdapter(settings)
    elif provider == "ollama":
        return OllamaAdapter(settings)
    elif provider == "azure":
        return AzureOpenAIAdapter(settings)
    elif provider == "anthropic":
        return AnthropicAdapter(settings)
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider}'. Supported: openai, ollama, azure, anthropic"
        )


def create_llm_adapter_for_model(
    provider: str,
    model_name: str,
    base_settings: Settings,
) -> LLMPort:
    """Create LLM adapter for a specific model.

    Uses base_settings for infrastructure (API keys, URLs, timeouts)
    but overrides the provider and model name.

    Args:
        provider: LLM provider (openai, ollama, azure, anthropic)
        model_name: Model name (e.g., "gpt-5-nano", "gemma3:1b")
        base_settings: Base settings with API keys and infrastructure config

    Returns:
        LLMPort implementation for the specified model

    Raises:
        ValueError: Unsupported provider

    Examples:
        # Create adapter for a specific model
        llm = create_llm_adapter_for_model("ollama", "gemma3:1b", settings)
    """
    provider = provider.lower()

    if provider == "openai":
        # Override openai model
        base_settings.llm_provider = "openai"
        base_settings.openai_model = model_name
        return OpenAIAdapter(base_settings)
    elif provider == "ollama":
        # Override ollama model
        base_settings.llm_provider = "ollama"
        base_settings.ollama_model = model_name
        return OllamaAdapter(base_settings)
    elif provider == "azure":
        base_settings.llm_provider = "azure"
        base_settings.azure_deployment = model_name
        return AzureOpenAIAdapter(base_settings)
    elif provider == "anthropic":
        base_settings.llm_provider = "anthropic"
        base_settings.anthropic_model = model_name
        return AnthropicAdapter(base_settings)
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider}'. Supported: openai, ollama, azure, anthropic"
        )


__all__ = [
    "BaseLLMAdapter",
    "LLMConfigurationError",
    "create_openai_embeddings_with_legacy",
    "OpenAIAdapter",
    "AzureOpenAIAdapter",
    "AnthropicAdapter",
    "LLMRelationAugmenter",
    "OllamaAdapter",
    "get_llm_adapter",
    "create_llm_adapter_for_model",
]
