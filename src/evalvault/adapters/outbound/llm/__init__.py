"""LLM adapters."""

from evalvault.adapters.outbound.llm.anthropic_adapter import AnthropicAdapter
from evalvault.adapters.outbound.llm.azure_adapter import AzureOpenAIAdapter
from evalvault.adapters.outbound.llm.base import BaseLLMAdapter, LLMConfigurationError
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


__all__ = [
    "BaseLLMAdapter",
    "LLMConfigurationError",
    "OpenAIAdapter",
    "AzureOpenAIAdapter",
    "AnthropicAdapter",
    "LLMRelationAugmenter",
    "OllamaAdapter",
    "get_llm_adapter",
]
