from __future__ import annotations

import importlib
import sys
from datetime import datetime
from pathlib import Path

from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.domain.entities.auth import Role
from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.services.authorization import Principal


def _load_mcp_tools():
    repo_root = Path(__file__).resolve().parents[5]
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    tools_path = src_path / "evalvault" / "adapters" / "inbound" / "mcp" / "tools.py"
    module_parts = tools_path.relative_to(src_path).with_suffix("").parts
    module_path = ".".join(module_parts)
    return importlib.import_module(module_path)


mcp_tools = _load_mcp_tools()


def _principal(role: Role = Role.viewer, project_id: str = "proj-a") -> Principal:
    return Principal(
        user_id="user-a",
        email="user-a@example.com",
        memberships={project_id: role},
    )


def _seed_run(storage: SQLiteStorageAdapter, run_id: str, project_id: str) -> EvaluationRun:
    run = EvaluationRun(
        run_id=run_id,
        dataset_name="sample-dataset",
        model_name="sample-model",
        project_id=project_id,
        metrics_evaluated=["faithfulness"],
        started_at=datetime(2026, 1, 2, 10, 0, 0),
        finished_at=datetime(2026, 1, 2, 10, 1, 0),
        results=[
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[MetricScore(name="faithfulness", score=0.92, threshold=0.8)],
            )
        ],
    )
    storage.save_run(run)
    return run


def test_list_runs_scopes_to_project_for_member_principal(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    db_path = tmp_path / "data" / "db" / "evalvault.db"
    storage = SQLiteStorageAdapter(db_path=db_path)
    _seed_run(storage, "run-a", "proj-a")
    _seed_run(storage, "run-b", "proj-b")

    response = mcp_tools.list_runs(
        {"limit": 10, "db_path": db_path, "project_id": "proj-a"},
        principal=_principal(),
    )

    assert response.errors == []
    assert {run.run_id for run in response.runs} == {"run-a"}


def test_project_scoped_list_requires_principal(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    db_path = tmp_path / "data" / "db" / "evalvault.db"
    SQLiteStorageAdapter(db_path=db_path)

    response = mcp_tools.list_runs({"db_path": db_path, "project_id": "proj-a"})

    assert [error.code for error in response.errors] == ["EVAL_AUTH_REQUIRED"]


def test_get_run_summary_hides_foreign_project_run(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    db_path = tmp_path / "data" / "db" / "evalvault.db"
    storage = SQLiteStorageAdapter(db_path=db_path)
    _seed_run(storage, "run-b", "proj-b")

    response = mcp_tools.get_run_summary(
        {"run_id": "run-b", "db_path": db_path, "project_id": "proj-a"},
        principal=_principal(),
    )

    assert [error.code for error in response.errors] == ["EVAL_RUN_NOT_FOUND"]


def test_analyze_compare_rejects_cross_project_run(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    db_path = tmp_path / "data" / "db" / "evalvault.db"
    storage = SQLiteStorageAdapter(db_path=db_path)
    _seed_run(storage, "run-a", "proj-a")
    _seed_run(storage, "run-b", "proj-b")

    response = mcp_tools.analyze_compare(
        {
            "run_id_a": "run-a",
            "run_id_b": "run-b",
            "db_path": db_path,
            "project_id": "proj-a",
        },
        principal=_principal(),
    )

    assert [error.code for error in response.errors] == ["EVAL_RUN_NOT_FOUND"]


def test_get_artifacts_requires_project_run_membership(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    db_path = tmp_path / "data" / "db" / "evalvault.db"
    storage = SQLiteStorageAdapter(db_path=db_path)
    _seed_run(storage, "run-b", "proj-b")
    reports_dir = tmp_path / "reports" / "analysis"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "analysis_run-b.md").write_text("# foreign", encoding="utf-8")

    response = mcp_tools.get_artifacts(
        {
            "run_id": "run-b",
            "kind": "analysis",
            "db_path": db_path,
            "project_id": "proj-a",
        },
        principal=_principal(),
    )

    assert [error.code for error in response.errors] == ["EVAL_RUN_NOT_FOUND"]


def test_viewer_cannot_run_project_evaluation(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    response = mcp_tools.run_evaluation(
        {
            "dataset_path": Path("data/datasets/proj-a/ds.json"),
            "metrics": ["exact_match"],
            "project_id": "proj-a",
        },
        principal=_principal(Role.viewer),
    )

    assert [error.code for error in response.errors] == ["EVAL_INSUFFICIENT_ROLE"]


def test_editor_run_evaluation_rejects_foreign_project_dataset_path(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    dataset_path = tmp_path / "data" / "datasets" / "proj-b" / "foreign.json"
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    dataset_path.write_text("{}", encoding="utf-8")

    response = mcp_tools.run_evaluation(
        {
            "dataset_path": dataset_path,
            "metrics": ["exact_match"],
            "project_id": "proj-a",
        },
        principal=_principal(Role.editor),
    )

    assert [error.code for error in response.errors] == ["EVAL_DATASET_UNSAFE_PATH"]
