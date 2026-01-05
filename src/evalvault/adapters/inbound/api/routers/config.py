"""API Router for System Configuration."""

from __future__ import annotations

from fastapi import APIRouter

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
            "langfuse_secret_key",
            "phoenix_api_token",
            "postgres_password",
            "postgres_connection_string",
        }
    )
