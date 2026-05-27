"""Ragas prompt override parsing + application helpers."""

from __future__ import annotations

import logging
from typing import Any

import yaml

logger = logging.getLogger(__name__)


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


def apply_prompt_overrides(
    ragas_metrics: list[Any],
    prompt_overrides: dict[str, str],
) -> dict[str, str]:
    """Apply prompt overrides to Ragas metric instances."""

    statuses: dict[str, str] = {}
    for metric in ragas_metrics:
        metric_name = getattr(metric, "name", None)
        if not metric_name or metric_name not in prompt_overrides:
            continue
        prompt_text = prompt_overrides[metric_name]
        applied = override_metric_prompt(metric, prompt_text)
        if not applied and metric_name == "faithfulness":
            applied = override_faithfulness_prompt(metric, prompt_text)
        statuses[metric_name] = "applied" if applied else "unsupported"
        if not applied:
            logger.warning("Prompt override for metric '%s' could not be applied.", metric_name)
    return statuses


def override_metric_prompt(metric: Any, prompt_text: str) -> bool:
    """Best-effort override for metric prompt templates."""

    if hasattr(metric, "prompt"):
        target = metric.prompt
        if isinstance(target, str):
            metric.prompt = prompt_text
            return True
        if target is not None and hasattr(target, "template"):
            target.template = prompt_text
            return True
        if target is not None and hasattr(target, "instruction"):
            target.instruction = prompt_text
            return True

    if hasattr(metric, "question_generation"):
        target = getattr(metric, "question_generation", None)
        if isinstance(target, str):
            metric.question_generation = prompt_text
            return True
        if target is not None and hasattr(target, "template"):
            target.template = prompt_text
            return True
        if target is not None and hasattr(target, "instruction"):
            target.instruction = prompt_text
            return True

    candidates: list[tuple[str, Any]] = []
    for attr in dir(metric):
        if not attr.endswith("_prompt") or attr == "prompt":
            continue
        try:
            value = getattr(metric, attr)
        except Exception:
            continue
        if value is None:
            continue
        candidates.append((attr, value))

    if len(candidates) == 1:
        attr, value = candidates[0]
        if isinstance(value, str):
            setattr(metric, attr, prompt_text)
            return True
        if hasattr(value, "template"):
            value.template = prompt_text
            return True
        if hasattr(value, "instruction"):
            value.instruction = prompt_text
            return True

    return False


def override_faithfulness_prompt(metric: Any, prompt_text: str) -> bool:
    target = getattr(metric, "nli_statements_prompt", None)
    if target is None:
        return False
    if hasattr(target, "instruction"):
        target.instruction = prompt_text
        return True
    return False


def extract_prompt_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    for attr in ("template", "instruction", "prompt", "text"):
        try:
            candidate = getattr(value, attr)
        except Exception:
            continue
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return None


def collect_metric_prompt_text(metric: Any) -> str | None:
    for attr in ("prompt", "question_generation"):
        if hasattr(metric, attr):
            try:
                value = getattr(metric, attr)
            except Exception:
                continue
            text = extract_prompt_text(value)
            if text:
                return text
    for attr in dir(metric):
        if not attr.endswith("_prompt") or attr == "prompt":
            continue
        try:
            value = getattr(metric, attr)
        except Exception:
            continue
        text = extract_prompt_text(value)
        if text:
            return text
    return None


def collect_ragas_prompt_snapshots(
    ragas_metrics: list[Any],
    prompt_overrides: dict[str, str] | None,
    override_status: dict[str, str],
) -> dict[str, dict[str, Any]]:
    snapshots: dict[str, dict[str, Any]] = {}
    for metric in ragas_metrics:
        metric_name = getattr(metric, "name", None)
        if not metric_name:
            continue
        requested = bool(prompt_overrides and metric_name in prompt_overrides)
        status = override_status.get(metric_name)
        source = "override" if status == "applied" else "default"

        prompts: dict[str, str] = {}
        if metric_name == "summary_score":
            prompts["question_generation"] = (
                extract_prompt_text(getattr(metric, "question_generation_prompt", None)) or ""
            )
            prompts["answer_generation"] = (
                extract_prompt_text(getattr(metric, "answer_generation_prompt", None)) or ""
            )
            prompts["extract_keyphrases"] = (
                extract_prompt_text(getattr(metric, "extract_keyphrases_prompt", None)) or ""
            )
            prompts = {k: v for k, v in prompts.items() if v}
        elif metric_name == "summary_faithfulness":
            prompts["statement_generation"] = (
                extract_prompt_text(getattr(metric, "statement_generator_prompt", None)) or ""
            )
            prompts["nli_statements"] = (
                extract_prompt_text(getattr(metric, "nli_statements_prompt", None)) or ""
            )
            prompts = {k: v for k, v in prompts.items() if v}

        prompt_text = collect_metric_prompt_text(metric)
        if prompts:
            snapshots[str(metric_name)] = {
                "prompts": prompts,
                "source": source,
                "override_requested": requested,
                "override_status": status,
            }
        elif prompt_text:
            snapshots[str(metric_name)] = {
                "prompt": prompt_text,
                "source": source,
                "override_requested": requested,
                "override_status": status,
            }
    return snapshots
