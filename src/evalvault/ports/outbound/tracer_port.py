"""Outbound port for tracing spans without infrastructure coupling."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Protocol


class TracerPort(Protocol):
    """Tracing port used by domain services."""

    def span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> AbstractContextManager[Any | None]:
        """Start a tracing span as a context manager."""
        ...

    def set_span_attributes(self, span: Any, attributes: dict[str, Any]) -> None:
        """Attach attributes to an active span."""
        ...
