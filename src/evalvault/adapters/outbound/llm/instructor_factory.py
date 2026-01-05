"""Helpers to construct InstructorLLM instances regardless of ragas version."""

from __future__ import annotations

from typing import Any

import instructor
from ragas.llms.base import InstructorLLM


def create_instructor_llm(
    provider: str,
    model: str,
    client: Any,
    mode: instructor.Mode | None = None,
    **model_args: Any,
) -> InstructorLLM:
    """Create an InstructorLLM for the given provider using a patched client."""
    provider_name = provider.lower()

    if provider_name in {"openai", "azure", "ollama", "vllm"}:
        resolved_mode = mode or (
            instructor.Mode.JSON if provider_name in {"ollama", "vllm"} else instructor.Mode.TOOLS
        )
        patched_client = instructor.from_openai(client, mode=resolved_mode)
        provider_id = "openai"
    elif provider_name == "anthropic":
        patched_client = instructor.from_anthropic(client)
        provider_id = "anthropic"
    elif provider_name == "litellm":
        patched_client = instructor.from_litellm(client)
        provider_id = "litellm"
    else:  # pragma: no cover - future providers
        raise ValueError(
            f"Unsupported instructor provider '{provider}'. "
            "Supported providers: openai, anthropic, litellm."
        )

    return InstructorLLM(client=patched_client, model=model, provider=provider_id, **model_args)
