"""Open RAG Trace adapter using OpenTelemetry when available."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from typing import Any

try:
    from opentelemetry import trace
except Exception:  # pragma: no cover - optional dependency
    trace = None  # type: ignore[assignment]


@dataclass(frozen=True)
class OpenRagTraceConfig:
    """Configuration for Open RAG Trace adapter."""

    spec_version: str = "0.1"
    module_attribute: str = "rag.module"
    custom_prefix: str = "custom."
    allowed_modules: tuple[str, ...] = (
        "ingest",
        "chunk",
        "embed",
        "retrieve",
        "rerank",
        "prompt",
        "llm",
        "postprocess",
        "eval",
        "cache",
    )


class _NoOpSpan:
    """No-op span used when OpenTelemetry is unavailable."""

    def set_attribute(self, _key: str, _value: Any) -> None:
        return None

    def add_event(self, _name: str, _attributes: dict[str, Any] | None = None) -> None:
        return None

    def record_exception(self, _exc: Exception) -> None:
        return None

    def end(self) -> None:
        return None


class OpenRagTraceAdapter:
    """Minimal Open RAG Trace adapter.

    This adapter is safe to use even when OpenTelemetry is not installed.
    """

    def __init__(
        self,
        tracer: Any | None = None,
        config: OpenRagTraceConfig | None = None,
    ) -> None:
        self._config = config or OpenRagTraceConfig()
        if tracer is not None:
            self._tracer = tracer
        elif trace is not None:
            self._tracer = trace.get_tracer("open-rag-trace")
        else:
            self._tracer = None

    def start_span(
        self,
        name: str,
        module: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> Any:
        span = self._tracer.start_span(name) if self._tracer is not None else _NoOpSpan()
        self._apply_standard_attributes(span, module, attributes)
        return span

    @contextmanager
    def span(
        self,
        name: str,
        module: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> Iterator[Any]:
        span = self.start_span(name, module, attributes)
        if trace is not None and not isinstance(span, _NoOpSpan):
            with trace.use_span(span, end_on_exit=False):
                try:
                    yield span
                except Exception as exc:
                    self.add_log(span, "error", "span error", error=str(exc))
                    with suppress(Exception):
                        span.record_exception(exc)
                    raise
                finally:
                    span.end()
        else:
            try:
                yield span
            except Exception as exc:
                self.add_log(span, "error", "span error", error=str(exc))
                with suppress(Exception):
                    span.record_exception(exc)
                raise
            finally:
                span.end()

    def set_span_attributes(self, span: Any, attributes: Mapping[str, Any]) -> None:
        for key, value in attributes.items():
            coerced = _coerce_attribute_value(value)
            if coerced is None:
                continue
            span.set_attribute(key, coerced)

    def add_log(self, span: Any, level: str, message: str, **data: Any) -> None:
        attributes: dict[str, Any] = {"log.level": level, "log.message": message}
        if data:
            attributes["log.data"] = _coerce_attribute_value(data)
        span.add_event("log", attributes)

    def add_custom(self, span: Any, **attrs: Any) -> None:
        prefix = self._config.custom_prefix
        for key, value in attrs.items():
            coerced = _coerce_attribute_value(value)
            if coerced is None:
                continue
            span.set_attribute(f"{prefix}{key}", coerced)

    def _apply_standard_attributes(
        self,
        span: Any,
        module: str,
        attributes: Mapping[str, Any] | None,
    ) -> None:
        span.set_attribute("spec.version", self._config.spec_version)
        span.set_attribute(self._config.module_attribute, self._normalize_module(module))
        if attributes:
            self.set_span_attributes(span, attributes)

    def _normalize_module(self, module: str) -> str:
        normalized = str(module).strip().lower()
        if not normalized:
            return f"{self._config.custom_prefix}unknown"
        if normalized in self._config.allowed_modules:
            return normalized
        if normalized.startswith(self._config.custom_prefix):
            return normalized
        return f"{self._config.custom_prefix}{normalized}"


def _coerce_attribute_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool | int | float | str | bytes):
        return value
    if isinstance(value, list | tuple):
        if all(isinstance(item, bool | int | float | str | bytes) for item in value):
            return list(value)
        return json.dumps(value, ensure_ascii=False, default=str)
    if isinstance(value, Mapping):
        return json.dumps(value, ensure_ascii=False, default=str)
    return json.dumps(value, ensure_ascii=False, default=str)


__all__ = ["OpenRagTraceAdapter", "OpenRagTraceConfig"]
