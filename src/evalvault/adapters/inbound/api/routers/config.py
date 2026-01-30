"""API Router for System Configuration."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from evalvault.adapters.inbound.api.main import AdapterDep
from evalvault.config.settings import get_settings

router = APIRouter()


@router.get("/")
def get_config():
    """Get current system configuration."""
    settings = get_settings()
    # Return all settings but exclude sensitive keys
    return settings.model_dump(
        exclude={
            "openai_api_key",
            "anthropic_api_key",
            "azure_api_key",
            "vllm_api_key",
            "langfuse_secret_key",
            "phoenix_api_token",
            "postgres_password",
            "postgres_connection_string",
            "api_auth_tokens",
            "knowledge_read_tokens",
            "knowledge_write_tokens",
        }
    )


class ConfigUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evalvault_profile: str | None = None
    cors_origins: str | None = None
    evalvault_db_path: str | None = None
    evalvault_memory_db_path: str | None = None
    llm_provider: Literal["ollama", "openai", "vllm"] | None = None
    faithfulness_fallback_provider: Literal["ollama", "openai", "vllm"] | None = None
    faithfulness_fallback_model: str | None = None
    openai_model: str | None = None
    openai_embedding_model: str | None = None
    openai_base_url: str | None = None
    ollama_model: str | None = None
    ollama_embedding_model: str | None = None
    ollama_base_url: str | None = None
    ollama_timeout: int | None = None
    ollama_think_level: str | None = None
    ollama_tool_models: str | None = None
    vllm_model: str | None = None
    vllm_embedding_model: str | None = None
    vllm_base_url: str | None = None
    vllm_embedding_base_url: str | None = None
    vllm_timeout: int | None = None
    azure_endpoint: str | None = None
    azure_deployment: str | None = None
    azure_embedding_deployment: str | None = None
    azure_api_version: str | None = None
    anthropic_model: str | None = None
    anthropic_thinking_budget: int | None = None
    langfuse_host: str | None = None
    mlflow_tracking_uri: str | None = None
    mlflow_experiment_name: str | None = None
    phoenix_endpoint: str | None = None
    phoenix_enabled: bool | None = None
    phoenix_sample_rate: float | None = None
    phoenix_project_name: str | None = None
    phoenix_annotations_enabled: bool | None = None
    tracker_provider: str | None = None
    postgres_host: str | None = None
    postgres_port: int | None = None
    postgres_database: str | None = None
    postgres_user: str | None = None


@router.patch("/")
def update_config(
    payload: ConfigUpdateRequest,
    adapter: AdapterDep,
):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return get_config()

    settings = adapter.apply_settings_patch(updates)
    return settings.model_dump(
        exclude={
            "openai_api_key",
            "anthropic_api_key",
            "azure_api_key",
            "vllm_api_key",
            "langfuse_secret_key",
            "phoenix_api_token",
            "postgres_password",
            "postgres_connection_string",
            "api_auth_tokens",
            "knowledge_read_tokens",
            "knowledge_write_tokens",
        }
    )


@router.get("/profiles")
def list_profiles():
    """List available model profiles for selection."""
    from evalvault.config.model_config import get_model_config

    try:
        model_config = get_model_config()
    except FileNotFoundError:
        return []

    profiles = []
    for name, profile in model_config.profiles.items():
        profiles.append(
            {
                "name": name,
                "description": profile.description,
                "llm_provider": profile.llm.provider,
                "llm_model": profile.llm.model,
                "embedding_provider": profile.embedding.provider,
                "embedding_model": profile.embedding.model,
            }
        )
    return profiles
