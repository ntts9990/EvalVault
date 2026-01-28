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


def test_stage_event_requires_positive_attempt() -> None:
    with pytest.raises(ValueError, match="attempt"):
        StageEvent.from_dict({"run_id": "run-001", "stage_type": "input", "attempt": 0})


def test_stage_event_rejects_negative_duration() -> None:
    with pytest.raises(ValueError, match="duration_ms"):
        StageEvent.from_dict({"run_id": "run-001", "stage_type": "input", "duration_ms": -1})


def test_stage_event_rejects_inverted_timestamps() -> None:
    with pytest.raises(ValueError, match="finished_at"):
        StageEvent.from_dict(
            {
                "run_id": "run-001",
                "stage_type": "input",
                "started_at": "2026-01-10T10:00:00+00:00",
                "finished_at": "2026-01-10T09:59:59+00:00",
            }
        )


def test_stage_event_requires_attributes_dict() -> None:
    with pytest.raises(ValueError, match="dict"):
        StageEvent.from_dict({"run_id": "run-001", "stage_type": "input", "attributes": []})
