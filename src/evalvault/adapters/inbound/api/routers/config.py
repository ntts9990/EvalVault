"""API Router for System Configuration."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

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
        }
    )


class ConfigUpdateRequest(BaseModel):
    llm_provider: Literal["ollama", "openai", "vllm"] | None = None
    openai_model: str | None = None
    ollama_model: str | None = None
    vllm_model: str | None = None


@router.patch("/")
def update_config(
    payload: ConfigUpdateRequest,
    adapter: AdapterDep,
):
    """Update runtime configuration (non-secret fields only)."""
    updates = payload.model_dump(exclude_none=True)
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
        }
    )
