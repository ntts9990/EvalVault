"""Helpers for Langfuse metadata extraction."""

from __future__ import annotations

from typing import Any


def get_langfuse_trace_url(metadata: dict[str, Any] | None) -> str | None:
    """Extract Langfuse trace URL from tracker metadata."""
    if not metadata:
        return None
    langfuse_meta = metadata.get("langfuse")
    if not isinstance(langfuse_meta, dict):
        return None
    trace_url = langfuse_meta.get("trace_url")
    if isinstance(trace_url, str):
        trace_url = trace_url.strip()
        if trace_url:
            return trace_url
    return None
