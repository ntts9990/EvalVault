"""Storage-enforced project isolation for evaluation runs (EvalVault G4).

Principle 2 of the G4 plan: isolation must be enforced at the StoragePort layer,
not only via route guards. These tests prove that project scoping cannot be
bypassed by a known run_id, and that legacy/unscoped runs land in a deterministic
default project. Fast, local SQLite only — no external services.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from evalvault.adapters.outbound.storage.base_sql import DEFAULT_PROJECT_ID, SQLQueries
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.domain.entities import EvaluationRun


@pytest.fixture
def storage(tmp_path):
    return SQLiteStorageAdapter(db_path=tmp_path / "isolation.db")


def _run(run_id: str, project_id: str | None) -> EvaluationRun:
    return EvaluationRun(
        run_id=run_id,
        dataset_name="insurance-qa",
        dataset_version="1.0.0",
        model_name="gpt-5-nano",
        started_at=datetime(2026, 1, 2, 10, 0, 0),
        project_id=project_id,
    )


def test_project_id_persists_and_round_trips(storage):
    storage.save_run(_run("run-a", "project-a"))
    assert storage.get_run("run-a").project_id == "project-a"


def test_unscoped_run_normalized_to_default_project(storage):
    storage.save_run(_run("run-legacy", None))
    assert storage.get_run("run-legacy").project_id == DEFAULT_PROJECT_ID


def test_get_run_denies_cross_project_without_leaking_existence(storage):
    storage.save_run(_run("run-a", "project-a"))
    # Correct project resolves.
    assert storage.get_run("run-a", project_id="project-a").run_id == "run-a"
    # Foreign project must be indistinguishable from "not found".
    with pytest.raises(KeyError):
        storage.get_run("run-a", project_id="project-b")


def test_list_runs_is_scoped_by_project(storage):
    storage.save_run(_run("run-a1", "project-a"))
    storage.save_run(_run("run-a2", "project-a"))
    storage.save_run(_run("run-b1", "project-b"))

    a_ids = {r.run_id for r in storage.list_runs(project_id="project-a")}
    b_ids = {r.run_id for r in storage.list_runs(project_id="project-b")}

    assert a_ids == {"run-a1", "run-a2"}
    assert b_ids == {"run-b1"}
    assert "run-b1" not in a_ids


def test_list_runs_without_project_is_backward_compatible(storage):
    storage.save_run(_run("run-a", "project-a"))
    storage.save_run(_run("run-b", "project-b"))
    # No project filter → legacy behavior returns all runs.
    all_ids = {r.run_id for r in storage.list_runs()}
    assert {"run-a", "run-b"}.issubset(all_ids)


@pytest.mark.parametrize("placeholder", ["?", "%s"])
def test_shared_run_sql_includes_project_id_for_both_backends(placeholder):
    """SQLite ('?') and Postgres ('%s') share base_sql query generation."""
    queries = SQLQueries(placeholder=placeholder)
    assert "project_id" in queries.insert_run()
    assert "project_id" in queries.select_run()
