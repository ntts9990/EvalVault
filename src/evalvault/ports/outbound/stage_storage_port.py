"""Stage event/metric storage port."""

from __future__ import annotations

from typing import Protocol

from evalvault.domain.entities.stage import StageEvent, StageMetric


class StageStoragePort(Protocol):
    """Port for persisting stage-level events and metrics."""

    def save_stage_event(self, event: StageEvent) -> str:
        """Store a single stage event and return its stage_id."""
        ...

    def save_stage_events(self, events: list[StageEvent]) -> int:
        """Store multiple stage events and return the count stored."""
        ...

    def list_stage_events(
        self,
        run_id: str,
        *,
        stage_type: str | None = None,
    ) -> list[StageEvent]:
        """List stage events for a run (optionally filtered by stage type)."""
        ...

    def save_stage_metrics(self, metrics: list[StageMetric]) -> int:
        """Store multiple stage metrics and return the count stored."""
        ...

    def list_stage_metrics(
        self,
        run_id: str,
        *,
        stage_id: str | None = None,
        metric_name: str | None = None,
    ) -> list[StageMetric]:
        """List stage metrics for a run with optional filters."""
        ...
