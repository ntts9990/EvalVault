"""Tests for the A-S4 ``tracker_trace_ids`` migration & hydration path.

These cover three guarantees the rename promised:

1. The one-shot migration script :mod:`scripts.migrate_tracker_trace_ids`
   adds the new column on legacy SQLite databases and back-fills rows
   that only had ``langfuse_trace_id``.
2. Re-running the migration is a no-op (idempotent).
3. The storage adapter round-trips ``tracker_trace_ids`` end-to-end --
   write a row with the new dict, read it back, assert dict matches.

Note: there is intentionally no "legacy column projection" runtime test.
A-S4 maintains a single read/write path through ``tracker_trace_ids``;
the migration script is the boundary for converting historical rows.
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pytest

from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.domain.entities import EvaluationRun

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_SCRIPT = REPO_ROOT / "scripts" / "migrate_tracker_trace_ids.py"


def _load_migration_module():
    """Load the migration script as an importable module."""
    spec = importlib.util.spec_from_file_location(
        "migrate_tracker_trace_ids", MIGRATION_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def legacy_sqlite_db(tmp_path: Path) -> Path:
    """Create a SQLite DB that mimics the pre-A-S4 schema.

    The DB has ``langfuse_trace_id`` populated but no
    ``tracker_trace_ids`` column at all -- this is the shape historical
    deployments will present to the migration script.
    """
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE evaluation_runs (
                run_id TEXT PRIMARY KEY,
                dataset_name TEXT NOT NULL,
                dataset_version TEXT,
                model_name TEXT NOT NULL,
                started_at TIMESTAMP NOT NULL,
                finished_at TIMESTAMP,
                total_tokens INTEGER DEFAULT 0,
                total_cost_usd REAL,
                pass_rate REAL,
                metrics_evaluated TEXT,
                thresholds TEXT,
                langfuse_trace_id TEXT,
                metadata TEXT,
                retrieval_metadata TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO evaluation_runs (run_id, dataset_name, model_name, "
            "started_at, langfuse_trace_id) VALUES (?, ?, ?, ?, ?)",
            ("legacy-run-1", "qa", "gpt-x", "2025-01-01T00:00:00", "trace-legacy"),
        )
        conn.execute(
            "INSERT INTO evaluation_runs (run_id, dataset_name, model_name, "
            "started_at, langfuse_trace_id) VALUES (?, ?, ?, ?, ?)",
            ("legacy-run-2", "qa", "gpt-x", "2025-01-01T00:00:00", None),
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def _column_exists(db_path: Path, table: str, column: str) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cursor.fetchall())
    finally:
        conn.close()


def _row(db_path: Path, run_id: str) -> sqlite3.Row:
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM evaluation_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
    finally:
        conn.close()


class TestMigrationSqlite:
    """SQLite migration: add column + backfill rows."""

    def test_adds_column_and_backfills_legacy_rows(self, legacy_sqlite_db: Path):
        migrate = _load_migration_module()

        # Pre-condition: legacy schema, no tracker_trace_ids column.
        assert not _column_exists(legacy_sqlite_db, "evaluation_runs", "tracker_trace_ids")

        updated = migrate.migrate_sqlite(legacy_sqlite_db)

        # Column exists post-migration.
        assert _column_exists(legacy_sqlite_db, "evaluation_runs", "tracker_trace_ids")
        # Only the row with a non-NULL legacy trace_id is backfilled.
        assert updated == 1

        row1 = _row(legacy_sqlite_db, "legacy-run-1")
        assert row1["tracker_trace_ids"] is not None
        assert json.loads(row1["tracker_trace_ids"]) == {"langfuse": "trace-legacy"}
        # Untouched row (legacy was NULL) stays NULL.
        row2 = _row(legacy_sqlite_db, "legacy-run-2")
        assert row2["tracker_trace_ids"] in (None, "")

    def test_rerun_is_idempotent(self, legacy_sqlite_db: Path):
        migrate = _load_migration_module()
        first = migrate.migrate_sqlite(legacy_sqlite_db)
        second = migrate.migrate_sqlite(legacy_sqlite_db)
        assert first == 1
        assert second == 0, "Second run must be a no-op once rows are backfilled"


class TestRoundTrip:
    """``tracker_trace_ids`` survives save_run -> get_run."""

    def test_dict_roundtrips_through_sqlite(self, tmp_path: Path):
        db_path = tmp_path / "round.db"
        adapter = SQLiteStorageAdapter(db_path=db_path)

        run = EvaluationRun(
            run_id="round-1",
            dataset_name="qa",
            dataset_version="1.0.0",
            model_name="gpt-x",
            started_at=datetime(2025, 1, 1),
            finished_at=datetime(2025, 1, 1, 0, 5),
            tracker_trace_ids={"mlflow": "abc", "phoenix": "def"},
            results=[],
        )
        adapter.save_run(run)
        loaded = adapter.get_run("round-1")
        assert loaded.tracker_trace_ids == {"mlflow": "abc", "phoenix": "def"}


class TestUnmigratedRowDegradation:
    """Runtime intentionally has NO legacy column projection.

    Rows whose ``tracker_trace_ids`` is NULL (e.g. legacy data that the
    migration script has not yet processed) hydrate to an empty dict.
    The migration script is the single mechanism for converting legacy
    rows; the storage adapter must NOT silently project the legacy
    ``langfuse_trace_id`` column at read time.
    """

    def test_unmigrated_row_hydrates_to_empty_dict(self, legacy_sqlite_db: Path):
        # The adapter's own _apply_migrations adds the new column when
        # opened. Don't run the script -- emulate a deployment that
        # picked up the new code before the operator ran the migration.
        adapter = SQLiteStorageAdapter(db_path=legacy_sqlite_db)
        loaded = adapter.get_run("legacy-run-1")
        # langfuse_trace_id is populated in the legacy row but the
        # runtime read path no longer references that column.
        assert loaded.tracker_trace_ids == {}
