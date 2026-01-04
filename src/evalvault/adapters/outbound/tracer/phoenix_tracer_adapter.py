"""Phoenix/OpenTelemetry tracer adapter."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any

from evalvault.config.phoenix_support import instrumentation_span, set_span_attributes
from evalvault.ports.outbound.tracer_port import TracerPort


class PhoenixTracerAdapter(TracerPort):
    """Adapter that delegates spans to Phoenix instrumentation helpers."""

    def span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> AbstractContextManager[Any | None]:
        return instrumentation_span(name, attributes)

    def set_span_attributes(self, span: Any, attributes: dict[str, Any]) -> None:
        set_span_attributes(span, attributes)
