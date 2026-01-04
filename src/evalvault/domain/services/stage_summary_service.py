"""Stage summary service for pipeline observability."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from evalvault.domain.entities.stage import (
    REQUIRED_STAGE_TYPES,
    StageEvent,
    StageSummary,
)


class StageSummaryService:
    """Compute summary statistics for stage events."""

    def summarize(self, events: Iterable[StageEvent]) -> StageSummary:
        event_list = list(events)
        run_id = event_list[0].run_id if event_list else ""
        stage_counts: dict[str, int] = defaultdict(int)
        duration_totals: dict[str, float] = defaultdict(float)
        duration_counts: dict[str, int] = defaultdict(int)

        for event in event_list:
            stage_counts[event.stage_type] += 1
            if event.duration_ms is not None:
                duration_totals[event.stage_type] += event.duration_ms
                duration_counts[event.stage_type] += 1

        avg_durations = {
            stage_type: duration_totals[stage_type] / duration_counts[stage_type]
            for stage_type in duration_totals
            if duration_counts[stage_type] > 0
        }

        observed_types = set(stage_counts.keys())
        missing_required = [stage for stage in REQUIRED_STAGE_TYPES if stage not in observed_types]

        return StageSummary(
            run_id=run_id,
            total_events=len(event_list),
            stage_type_counts=dict(stage_counts),
            stage_type_avg_durations=avg_durations,
            missing_required_stage_types=missing_required,
        )
