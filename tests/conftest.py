"""Shared pytest configuration for optional parallel runs."""

from __future__ import annotations

import os
from typing import Any


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
