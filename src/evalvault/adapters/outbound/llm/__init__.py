from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from evalvault.adapters.outbound.llm.base import (
    BaseLLMAdapter,
    LLMConfigurationError,
    create_openai_embeddings_with_legacy,
)
from evalvault.adapters.outbound.llm.factory import (
    SettingsLLMFactory,
    create_llm_adapter_for_model,
)
from evalvault.adapters.outbound.llm.llm_relation_augmenter import LLMRelationAugmenter
from evalvault.config.settings import Settings
from evalvault.ports.outbound.llm_port import LLMPort

if TYPE_CHECKING:
    from evalvault.adapters.outbound.llm.anthropic_adapter import AnthropicAdapter
    from evalvault.adapters.outbound.llm.azure_adapter import AzureOpenAIAdapter
    from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter
    from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter
    from evalvault.adapters.outbound.llm.vllm_adapter import VLLMAdapter


_LAZY_IMPORTS: dict[str, str] = {
    "OpenAIAdapter": "evalvault.adapters.outbound.llm.openai_adapter:OpenAIAdapter",
    "AzureOpenAIAdapter": "evalvault.adapters.outbound.llm.azure_adapter:AzureOpenAIAdapter",
    "AnthropicAdapter": "evalvault.adapters.outbound.llm.anthropic_adapter:AnthropicAdapter",
    "OllamaAdapter": "evalvault.adapters.outbound.llm.ollama_adapter:OllamaAdapter",
    "VLLMAdapter": "evalvault.adapters.outbound.llm.vllm_adapter:VLLMAdapter",
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_path, attr_name = target.split(":", 1)
    module = import_module(module_path)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def get_llm_adapter(settings: Settings) -> LLMPort:
    provider = settings.llm_provider.lower()

    if provider == "openai":
        from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter

        return OpenAIAdapter(settings)
    if provider == "ollama":
        from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter

        return OllamaAdapter(settings)
    if provider == "vllm":
        from evalvault.adapters.outbound.llm.vllm_adapter import VLLMAdapter

        return VLLMAdapter(settings)
    if provider == "azure":
        from evalvault.adapters.outbound.llm.azure_adapter import AzureOpenAIAdapter

        return AzureOpenAIAdapter(settings)
    if provider == "anthropic":
        from evalvault.adapters.outbound.llm.anthropic_adapter import AnthropicAdapter

        return AnthropicAdapter(settings)

    raise ValueError(
        f"Unsupported LLM provider: '{provider}'. Supported: openai, ollama, vllm, azure, anthropic"
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
    "VLLMAdapter",
    "SettingsLLMFactory",
    "get_llm_adapter",
    "create_llm_adapter_for_model",
]
