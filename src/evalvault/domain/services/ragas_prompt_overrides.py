"""Ragas prompt override parsing helpers."""

from __future__ import annotations

from typing import Any

import yaml


class PromptOverrideError(ValueError):
    """Raised when a prompt override payload is invalid."""


def normalize_ragas_prompt_overrides(raw: Any) -> dict[str, str]:
    """Normalize a raw mapping into metric -> prompt overrides."""

    if raw is None:
        return {}

    if isinstance(raw, str):
        raw = yaml.safe_load(raw) or {}

    if not isinstance(raw, dict):
        raise PromptOverrideError("ragas prompt overrides must be a mapping")

    payload = raw.get("metrics") if "metrics" in raw else raw
    if not isinstance(payload, dict):
        raise PromptOverrideError("ragas prompt overrides must be a mapping of metrics")

    overrides: dict[str, str] = {}
    for metric_name, prompt in payload.items():
        if prompt is None:
            continue
        if not isinstance(prompt, str):
            raise PromptOverrideError(f"prompt for metric '{metric_name}' must be a string")
        normalized = prompt.strip()
        if normalized:
            overrides[str(metric_name)] = normalized

    return overrides


def load_ragas_prompt_overrides(path: str) -> dict[str, str]:
    """Load overrides from a YAML file path."""

    with open(path, encoding="utf-8") as handle:
        content = handle.read()
    return normalize_ragas_prompt_overrides(content)
