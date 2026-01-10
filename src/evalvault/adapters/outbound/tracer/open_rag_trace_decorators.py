"""Convenience decorators for Open RAG Trace spans."""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable, Mapping
from typing import Any, TypeVar

from evalvault.adapters.outbound.tracer.open_rag_trace_adapter import OpenRagTraceAdapter

R = TypeVar("R")
AttributeBuilder = Callable[..., Mapping[str, Any]]


def trace_module(
    module: str,
    *,
    name: str | None = None,
    adapter: OpenRagTraceAdapter | None = None,
    attributes: Mapping[str, Any] | None = None,
    attributes_builder: AttributeBuilder | None = None,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """Wrap a function with an Open RAG Trace span."""

    adapter_to_use = adapter or OpenRagTraceAdapter()

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        span_name = name or func.__name__

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> R:
                merged = _merge_attributes(attributes, attributes_builder, args, kwargs)
                with adapter_to_use.span(span_name, module, merged):
                    return await func(*args, **kwargs)

            return async_wrapper

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            merged = _merge_attributes(attributes, attributes_builder, args, kwargs)
            with adapter_to_use.span(span_name, module, merged):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def _merge_attributes(
    static_attrs: Mapping[str, Any] | None,
    builder: AttributeBuilder | None,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Mapping[str, Any] | None:
    merged: dict[str, Any] = {}
    if static_attrs:
        merged.update(static_attrs)
    if builder:
        dynamic = builder(*args, **kwargs)
        if dynamic:
            merged.update(dynamic)
    return merged or None


__all__ = ["trace_module"]
