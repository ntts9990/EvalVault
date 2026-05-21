from __future__ import annotations

from evalvault.config.settings import Settings
from evalvault.ports.outbound.llm_factory_port import LLMFactoryPort
from evalvault.ports.outbound.llm_port import LLMPort


class SettingsLLMFactory(LLMFactoryPort):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_faithfulness_fallback(
        self,
        active_provider: str | None,
        active_model: str | None,
    ) -> LLMPort | None:
        provider, model = _resolve_faithfulness_fallback_config(
            settings=self._settings,
            active_provider=active_provider,
            active_model=active_model,
        )
        if not provider or not model:
            return None
        return create_llm_adapter_for_model(provider, model, self._settings)


def create_llm_adapter_for_model(
    provider: str,
    model_name: str,
    base_settings: Settings,
) -> LLMPort:
    provider = provider.lower()

    if provider == "openai":
        derived = base_settings.model_copy(
            update={"llm_provider": "openai", "openai_model": model_name}
        )
        from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter

        return OpenAIAdapter(derived)
    if provider == "ollama":
        derived = base_settings.model_copy(
            update={"llm_provider": "ollama", "ollama_model": model_name}
        )
        from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter

        return OllamaAdapter(derived)
    if provider == "vllm":
        derived = base_settings.model_copy(
            update={"llm_provider": "vllm", "vllm_model": model_name}
        )
        from evalvault.adapters.outbound.llm.vllm_adapter import VLLMAdapter

        return VLLMAdapter(derived)
    if provider == "azure":
        derived = base_settings.model_copy(
            update={"llm_provider": "azure", "azure_deployment": model_name}
        )
        from evalvault.adapters.outbound.llm.azure_adapter import AzureOpenAIAdapter

        return AzureOpenAIAdapter(derived)
    if provider == "anthropic":
        derived = base_settings.model_copy(
            update={"llm_provider": "anthropic", "anthropic_model": model_name}
        )
        from evalvault.adapters.outbound.llm.anthropic_adapter import AnthropicAdapter

        return AnthropicAdapter(derived)

    raise ValueError(
        f"Unsupported LLM provider: '{provider}'. Supported: openai, ollama, vllm, azure, anthropic"
    )


def _resolve_faithfulness_fallback_config(
    *,
    settings: Settings,
    active_provider: str | None,
    active_model: str | None,
) -> tuple[str | None, str | None]:
    provider = (
        settings.faithfulness_fallback_provider.strip().lower()
        if settings.faithfulness_fallback_provider
        else None
    )
    model = settings.faithfulness_fallback_model
    normalized_active = active_provider.strip().lower() if active_provider else None
    default_provider = normalized_active or settings.llm_provider.lower()

    if not provider and model:
        provider = default_provider
    if provider and not model:
        model = _default_faithfulness_fallback_model(provider, settings)
    if not provider and not model:
        provider = default_provider
        model = _default_faithfulness_fallback_model(default_provider, settings)

    if not provider or not model:
        return None, None
    return provider, model


def _default_faithfulness_fallback_model(provider: str, settings: Settings) -> str | None:
    if provider == "ollama":
        return "qwen3:8b"
    if provider == "vllm":
        return "gpt-oss-120b"
    if provider == "openai":
        return settings.default_fallback_model
    return None
