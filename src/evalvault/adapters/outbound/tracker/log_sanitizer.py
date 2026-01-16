from __future__ import annotations

import re
from typing import Any

MASK_TOKEN = "[REDACTED]"
MAX_LOG_CHARS = 1000
MAX_CONTEXT_CHARS = 500
MAX_LIST_ITEMS = 20
MAX_PAYLOAD_DEPTH = 2

_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_PATTERN = re.compile(
    r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}\b"
)
_SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")


def _mask_pii(text: str) -> str:
    text = _EMAIL_PATTERN.sub(MASK_TOKEN, text)
    text = _PHONE_PATTERN.sub(MASK_TOKEN, text)
    text = _SSN_PATTERN.sub(MASK_TOKEN, text)
    text = _CARD_PATTERN.sub(MASK_TOKEN, text)
    return text


def _truncate(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return f"{text[: max_chars - 3]}..."


def sanitize_text(value: str | None, *, max_chars: int = MAX_LOG_CHARS) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    return _truncate(_mask_pii(value), max_chars)


def sanitize_text_list(
    values: list[str] | tuple[str, ...] | None,
    *,
    max_items: int = MAX_LIST_ITEMS,
    max_chars: int = MAX_CONTEXT_CHARS,
) -> list[str]:
    if not values:
        return []
    trimmed = list(values)[:max_items]
    return [sanitize_text(item, max_chars=max_chars) or "" for item in trimmed]


def sanitize_payload(
    value: Any,
    *,
    max_chars: int = MAX_LOG_CHARS,
    max_items: int = MAX_LIST_ITEMS,
    max_depth: int = MAX_PAYLOAD_DEPTH,
) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        return sanitize_text(value, max_chars=max_chars)
    if isinstance(value, bool | int | float):
        return value
    if max_depth <= 0:
        return sanitize_text(str(value), max_chars=max_chars)
    if isinstance(value, dict):
        return {
            key: sanitize_payload(
                item,
                max_chars=max_chars,
                max_items=max_items,
                max_depth=max_depth - 1,
            )
            for key, item in list(value.items())[:max_items]
        }
    if isinstance(value, list | tuple | set):
        return [
            sanitize_payload(
                item,
                max_chars=max_chars,
                max_items=max_items,
                max_depth=max_depth - 1,
            )
            for item in list(value)[:max_items]
        ]
    return sanitize_text(str(value), max_chars=max_chars)
