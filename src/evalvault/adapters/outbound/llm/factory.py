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
        base_settings.llm_provider = "openai"
        base_settings.openai_model = model_name
        from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter

        return OpenAIAdapter(base_settings)
    if provider == "ollama":
        base_settings.llm_provider = "ollama"
        base_settings.ollama_model = model_name
        from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter

        return OllamaAdapter(base_settings)
    if provider == "vllm":
        base_settings.llm_provider = "vllm"
        base_settings.vllm_model = model_name
        from evalvault.adapters.outbound.llm.vllm_adapter import VLLMAdapter

        return VLLMAdapter(base_settings)
    if provider == "azure":
        base_settings.llm_provider = "azure"
        base_settings.azure_deployment = model_name
        from evalvault.adapters.outbound.llm.azure_adapter import AzureOpenAIAdapter

        return AzureOpenAIAdapter(base_settings)
    if provider == "anthropic":
        base_settings.llm_provider = "anthropic"
        base_settings.anthropic_model = model_name
        from evalvault.adapters.outbound.llm.anthropic_adapter import AnthropicAdapter

        return AnthropicAdapter(base_settings)

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
        model = _default_faithfulness_fallback_model(provider)
    if not provider and not model:
        provider = default_provider
        model = _default_faithfulness_fallback_model(default_provider)

    if not provider or not model:
        return None, None
    return provider, model


def _default_faithfulness_fallback_model(provider: str) -> str | None:
    if provider == "ollama":
        return "qwen3:8b"
    if provider == "vllm":
        return "gpt-oss-120b"
    return None
