"""Unit tests for stage event storage in SQLite."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.domain.entities.stage import StageEvent, StageMetric, StagePayloadRef


@pytest.fixture
def temp_db() -> Path:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = Path(handle.name)
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def storage_adapter(temp_db: Path) -> SQLiteStorageAdapter:
    return SQLiteStorageAdapter(db_path=temp_db)


def test_save_and_list_stage_events(storage_adapter: SQLiteStorageAdapter) -> None:
    started_at = datetime(2026, 1, 3, 10, 0, 0)
    finished_at = started_at + timedelta(milliseconds=120)
    event = StageEvent(
        run_id="run-001",
        stage_type="input",
        stage_id="stg-input-001",
        stage_name="user_query",
        status="success",
        started_at=started_at,
        finished_at=finished_at,
        input_ref=StagePayloadRef(store="payload", id="pl-001", type="json"),
        attributes={"query": "hello"},
        metadata={"test_case_id": "tc-001"},
    )

    storage_adapter.save_stage_event(event)
    events = storage_adapter.list_stage_events("run-001")

    assert len(events) == 1
    stored = events[0]
    assert stored.stage_id == "stg-input-001"
    assert stored.stage_type == "input"
    assert stored.stage_name == "user_query"
    assert stored.input_ref is not None
    assert stored.input_ref.store == "payload"
    assert stored.attributes["query"] == "hello"
    assert stored.metadata["test_case_id"] == "tc-001"
    assert stored.duration_ms == pytest.approx(120.0)


def test_save_and_list_stage_metrics(storage_adapter: SQLiteStorageAdapter) -> None:
    metric = StageMetric(
        run_id="run-002",
        stage_id="stg-retrieval-001",
        metric_name="recall_at_5",
        score=0.8,
        threshold=0.7,
        evidence={"relevant_count": 4},
    )

    stored_count = storage_adapter.save_stage_metrics([metric])
    metrics = storage_adapter.list_stage_metrics("run-002")

    assert stored_count == 1
    assert len(metrics) == 1
    stored = metrics[0]
    assert stored.metric_name == "recall_at_5"
    assert stored.score == pytest.approx(0.8)
    assert stored.threshold == pytest.approx(0.7)
    assert stored.evidence == {"relevant_count": 4}
