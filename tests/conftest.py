"""Shared pytest configuration for optional parallel runs."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


def _find_repo_root(start: Path, max_depth: int = 6) -> Path | None:
    current = start
    for _ in range(max_depth):
        if (current / "pyproject.toml").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return None


def _ensure_repo_on_path() -> None:
    repo_root = _find_repo_root(Path(__file__).resolve())
    if repo_root is None:
        return
    src_path = str((repo_root / "src").resolve())
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


_ensure_repo_on_path()


def _resolve_xdist_workers(value: str) -> str | int:
    normalized = value.strip().lower()
    if normalized == "auto":
        return "auto"
    if normalized.isdigit():
        return int(normalized)
    return "auto"


def pytest_configure(config: Any) -> None:
    xdist_value = os.environ.get("EVALVAULT_XDIST")
    if not xdist_value:
        return
    if not config.pluginmanager.hasplugin("xdist"):
        return
    config.option.numprocesses = _resolve_xdist_workers(xdist_value)
    if hasattr(config.option, "dist") and not config.option.dist:
        config.option.dist = "loadscope"


def pytest_runtest_setup(item: Any) -> None:
    """Skip tests whose ``requires_*`` marker has no matching environment.

    Hoisted from ``tests/integration/conftest.py`` in T-S3 so the
    marker-based skip applies to both ``tests/unit`` and ``tests/integration``
    (langfuse/phoenix flow tests were reclassified to ``tests/unit``).
    """
    import pytest as _pytest

    if item.get_closest_marker("requires_openai") and not os.environ.get("OPENAI_API_KEY"):
        _pytest.skip("Requires OPENAI_API_KEY environment variable")

    if item.get_closest_marker("requires_langfuse") and not (
        os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")
    ):
        _pytest.skip("Requires LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")

    if item.get_closest_marker("requires_phoenix"):
        try:
            import opentelemetry  # noqa: F401
        except ImportError:
            _pytest.skip("Requires OpenTelemetry dependencies (uv sync --extra phoenix)")
