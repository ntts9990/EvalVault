"""Open RAG Trace logging handler."""

from __future__ import annotations

import json
import logging
from typing import Any

try:
    from opentelemetry import trace
except Exception:  # pragma: no cover - optional dependency
    trace = None  # type: ignore[assignment]


class OpenRagLogHandler(logging.Handler):
    """Attach structured logs to the active OpenTelemetry span."""

    def emit(self, record: logging.LogRecord) -> None:
        if trace is None:
            return
        span = trace.get_current_span()
        if span is None:
            return
        span_context = span.get_span_context()
        if not span_context or not span_context.is_valid:
            return

        attributes: dict[str, Any] = {
            "log.level": record.levelname.lower(),
            "log.message": record.getMessage(),
            "log.logger": record.name,
            "log.file": record.pathname,
            "log.line": record.lineno,
            "log.func": record.funcName,
        }
        data = _extract_record_data(record)
        if data:
            attributes["log.data"] = _coerce_attribute_value(data)
        span.add_event("log", attributes)


def install_open_rag_log_handler(
    logger: logging.Logger | None = None,
    level: int = logging.INFO,
) -> OpenRagLogHandler:
    """Install OpenRagLogHandler on a logger if not already present."""
    target_logger = logger or logging.getLogger()
    for handler in target_logger.handlers:
        if isinstance(handler, OpenRagLogHandler):
            return handler
    handler = OpenRagLogHandler(level=level)
    target_logger.addHandler(handler)
    return handler


def _extract_record_data(record: logging.LogRecord) -> dict[str, Any]:
    reserved = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
    }
    data: dict[str, Any] = {}
    for key, value in record.__dict__.items():
        if key in reserved:
            continue
        data[key] = value
    return data


def _coerce_attribute_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool | int | float | str | bytes):
        return value
    if isinstance(value, list | tuple):
        if all(isinstance(item, bool | int | float | str | bytes) for item in value):
            return list(value)
        return json.dumps(value, ensure_ascii=False, default=str)
    return json.dumps(value, ensure_ascii=False, default=str)


__all__ = ["OpenRagLogHandler", "install_open_rag_log_handler"]
