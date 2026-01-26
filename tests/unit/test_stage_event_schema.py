"""Unit tests for StageEvent schema normalization."""

import pytest

from evalvault.domain.entities.stage import StageEvent


def test_stage_event_requires_run_id() -> None:
    with pytest.raises(ValueError, match="run_id"):
        StageEvent.from_dict({"stage_type": "input"})


def test_stage_event_requires_non_empty_stage_type() -> None:
    with pytest.raises(ValueError, match="stage_type"):
        StageEvent.from_dict({"run_id": "run-001", "stage_type": " "})


def test_stage_event_normalizes_stage_type() -> None:
    event = StageEvent.from_dict({"run_id": "run-001", "stage_type": "Retrieval"})
    assert event.stage_type == "retrieval"
