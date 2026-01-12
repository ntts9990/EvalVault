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
