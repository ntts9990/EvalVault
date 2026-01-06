"""Project label helpers for the web UI."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evalvault.ports.inbound.web_port import RunSummary

ALL_PROJECTS_TOKEN = "__all__"
UNASSIGNED_PROJECT_TOKEN = "__unassigned__"


def normalize_project_name(name: str | None) -> str | None:
    """Normalize project names for comparison and display."""
    if not name:
        return None
    cleaned = name.strip()
    return cleaned or None


def collect_project_names(runs: Iterable[RunSummary]) -> list[str]:
    """Collect unique project names from runs."""
    names = {
        normalized
        for run in runs
        if (normalized := normalize_project_name(getattr(run, "project_name", None)))
    }
    return sorted(names)


def build_project_options(
    runs: Sequence[RunSummary],
    *,
    include_all: bool = True,
    include_unassigned: bool = True,
) -> list[str]:
    """Build project selector options with optional system tokens."""
    options: list[str] = []
    if include_all:
        options.append(ALL_PROJECTS_TOKEN)
    if include_unassigned:
        options.append(UNASSIGNED_PROJECT_TOKEN)
    options.extend(collect_project_names(runs))
    return options


def filter_runs_by_projects(
    runs: Sequence[RunSummary],
    selected: Sequence[str] | None,
    *,
    all_token: str = ALL_PROJECTS_TOKEN,
    unassigned_token: str = UNASSIGNED_PROJECT_TOKEN,
) -> list[RunSummary]:
    """Filter runs by selected projects."""
    if not selected or all_token in selected:
        return list(runs)

    include_unassigned = unassigned_token in selected
    allowed = {name for name in selected if name not in {all_token, unassigned_token}}

    return [
        run
        for run in runs
        if (run.project_name in allowed) or (include_unassigned and not run.project_name)
    ]
