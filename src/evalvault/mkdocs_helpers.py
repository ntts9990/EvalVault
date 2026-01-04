"""MkDocs helpers for documentation build."""

from __future__ import annotations

from pymdownx import slugs

_slugify = slugs.slugify(case="lower", normalize="NFC")


def unicode_slugify(value: str, separator: str) -> str:
    """Generate Unicode-friendly anchors for Markdown headings."""

    return _slugify(value, separator)
