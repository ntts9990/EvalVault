"""Unit tests for StageSummaryService."""

from evalvault.domain.entities.stage import StageEvent
from evalvault.domain.services.stage_summary_service import StageSummaryService


def test_stage_summary_detects_missing_required() -> None:
    events = [
        StageEvent(run_id="run-001", stage_type="input"),
        StageEvent(run_id="run-001", stage_type="retrieval"),
    ]

    summary = StageSummaryService().summarize(events)

    assert summary.run_id == "run-001"
    assert summary.total_events == 2
    assert summary.stage_type_counts["input"] == 1
    assert "system_prompt" in summary.missing_required_stage_types
    assert "output" in summary.missing_required_stage_types
