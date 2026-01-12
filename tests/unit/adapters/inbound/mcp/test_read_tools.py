from __future__ import annotations

import importlib
import sys
from datetime import datetime
from pathlib import Path

from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult


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


def _seed_run(storage: SQLiteStorageAdapter, run_id: str) -> EvaluationRun:
    run = EvaluationRun(
        run_id=run_id,
        dataset_name="sample-dataset",
        model_name="sample-model",
        metrics_evaluated=["faithfulness"],
        finished_at=datetime.now(),
        results=[
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[MetricScore(name="faithfulness", score=0.92, threshold=0.8)],
            )
        ],
    )
    storage.save_run(run)
    return run


def test_list_runs_returns_summary(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    db_path = tmp_path / "data" / "db" / "evalvault.db"
    storage = SQLiteStorageAdapter(db_path=db_path)
    _seed_run(storage, "run-test")

    response = mcp_tools.list_runs({"limit": 5, "db_path": db_path})

    assert response.errors == []
    assert response.runs
    assert response.runs[0].run_id == "run-test"


def test_get_run_summary_returns_thresholds(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    db_path = tmp_path / "data" / "db" / "evalvault.db"
    storage = SQLiteStorageAdapter(db_path=db_path)
    _seed_run(storage, "run-summary")

    response = mcp_tools.get_run_summary({"run_id": "run-summary", "db_path": db_path})

    assert response.errors == []
    assert response.summary is not None
    assert response.summary.run_id == "run-summary"
    assert response.summary.thresholds is not None
    assert response.summary.thresholds["faithfulness"] == 0.8


def test_get_artifacts_returns_existing_paths(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "run-artifacts"
    reports_dir = tmp_path / "reports" / "analysis"
    reports_dir.mkdir(parents=True, exist_ok=True)

    prefix = f"analysis_{run_id}"
    output_path = reports_dir / f"{prefix}.json"
    report_path = reports_dir / f"{prefix}.md"
    artifacts_dir = reports_dir / "artifacts" / prefix
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    index_path = artifacts_dir / "index.json"

    output_path.write_text("{}", encoding="utf-8")
    report_path.write_text("# report", encoding="utf-8")
    index_path.write_text("{}", encoding="utf-8")

    response = mcp_tools.get_artifacts({"run_id": run_id, "kind": "analysis"})

    assert response.errors == []
    assert response.artifacts is not None
    assert response.artifacts.report_path == str(report_path)
    assert response.artifacts.output_path == str(output_path)
    assert response.artifacts.artifacts_dir == str(artifacts_dir)
    assert response.artifacts.artifacts_index_path == str(index_path)
