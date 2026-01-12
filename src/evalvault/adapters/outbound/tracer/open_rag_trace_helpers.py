"""Helpers for building Open RAG Trace attributes."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


def serialize_json(value: Any) -> str:
    """Serialize value to JSON string for OTel-safe attributes."""
    return json.dumps(value, ensure_ascii=False, default=str)


def build_input_output_attributes(
    input_value: Any | None = None,
    output_value: Any | None = None,
) -> dict[str, Any]:
    attributes: dict[str, Any] = {}
    if input_value is not None:
        attributes["input.value"] = _as_otel_value(input_value)
    if output_value is not None:
        attributes["output.value"] = _as_otel_value(output_value)
    return attributes


def build_retrieval_attributes(
    query: str,
    top_k: int | None = None,
    documents: Sequence[Mapping[str, Any]] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    attributes: dict[str, Any] = {"retrieval.query": query}
    if top_k is not None:
        attributes["retrieval.top_k"] = top_k
    if documents:
        attributes["retrieval.documents_json"] = serialize_json(list(documents))
    attributes.update(_extra_attributes(extra))
    return attributes


def build_rerank_attributes(
    model_name: str | None = None,
    scores: Sequence[float] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    attributes: dict[str, Any] = {}
    if model_name:
        attributes["rerank.model_name"] = model_name
    if scores is not None:
        attributes["rerank.scores"] = list(scores)
    attributes.update(_extra_attributes(extra))
    return attributes


def build_llm_attributes(
    model_name: str | None = None,
    temperature: float | None = None,
    token_counts: Mapping[str, int] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    attributes: dict[str, Any] = {}
    if model_name:
        attributes["llm.model_name"] = model_name
    if temperature is not None:
        attributes["llm.temperature"] = temperature
    if token_counts:
        for key, value in token_counts.items():
            attributes[f"llm.token_count.{key}"] = value
    attributes.update(_extra_attributes(extra))
    return attributes


def build_eval_attributes(
    metric_name: str,
    score: float | None = None,
    passed: bool | None = None,
    **extra: Any,
) -> dict[str, Any]:
    attributes: dict[str, Any] = {"eval.metric_name": metric_name}
    if score is not None:
        attributes["eval.score"] = score
    if passed is not None:
        attributes["eval.passed"] = passed
    attributes.update(_extra_attributes(extra))
    return attributes


def _extra_attributes(extra: Mapping[str, Any]) -> dict[str, Any]:
    return {key: _as_otel_value(value) for key, value in extra.items() if value is not None}


def _as_otel_value(value: Any) -> Any:
    if isinstance(value, bool | int | float | str | bytes):
        return value
    if isinstance(value, list | tuple):
        if all(isinstance(item, bool | int | float | str | bytes) for item in value):
            return list(value)
        return serialize_json(value)
    if isinstance(value, Mapping):
        return serialize_json(value)
    if isinstance(value, Iterable) and not isinstance(value, str | bytes):
        return serialize_json(list(value))
    return serialize_json(value)


__all__ = [
    "build_eval_attributes",
    "build_input_output_attributes",
    "build_llm_attributes",
    "build_rerank_attributes",
    "build_retrieval_attributes",
    "serialize_json",
]
