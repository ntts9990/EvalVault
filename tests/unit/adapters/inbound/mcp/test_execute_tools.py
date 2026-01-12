from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult
from evalvault.ports.outbound.llm_port import LLMPort


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


class StubLLM(LLMPort):
    def get_model_name(self) -> str:
        return "stub"

    def as_ragas_llm(self):
        return None

    def generate_text(self, prompt: str, *, json_mode: bool = False) -> str:  # noqa: ARG002
        return "# Stub Report"


def _patch_llm(monkeypatch) -> None:
    from evalvault.adapters.outbound import llm as llm_module

    monkeypatch.setattr(mcp_tools, "get_llm_adapter", lambda _settings: StubLLM())
    monkeypatch.setattr(
        llm_module, "create_llm_adapter_for_model", lambda _provider, _model, _settings: StubLLM()
    )


def _write_dataset(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": "sample",
        "version": "1.0.0",
        "test_cases": [
            {
                "id": "tc-1",
                "question": "What is Python?",
                "answer": "Python is a language.",
                "contexts": ["Python is a programming language."],
                "ground_truth": "Python is a programming language.",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_run_evaluation_with_auto_analyze(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _patch_llm(monkeypatch)

    dataset_path = tmp_path / "data" / "dataset.json"
    _write_dataset(dataset_path)
    db_path = tmp_path / "data" / "db" / "evalvault.db"

    response = mcp_tools.run_evaluation(
        {
            "dataset_path": dataset_path,
            "metrics": ["exact_match"],
            "db_path": db_path,
            "auto_analyze": True,
        }
    )

    assert response.errors == []
    assert response.run_id
    assert response.metrics["exact_match"] is not None
    assert response.artifacts is not None
    assert response.artifacts.analysis_report_path
    assert Path(response.artifacts.analysis_report_path).exists()


def test_analyze_compare_generates_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _patch_llm(monkeypatch)

    db_path = tmp_path / "data" / "db" / "evalvault.db"
    storage = SQLiteStorageAdapter(db_path=db_path)

    run_a = EvaluationRun(
        run_id="run-a",
        dataset_name="sample",
        dataset_version="1.0",
        model_name="stub",
        metrics_evaluated=["exact_match"],
        results=[
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[MetricScore(name="exact_match", score=0.6, threshold=0.7)],
            )
        ],
    )
    run_b = EvaluationRun(
        run_id="run-b",
        dataset_name="sample",
        dataset_version="1.0",
        model_name="stub",
        metrics_evaluated=["exact_match"],
        results=[
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[MetricScore(name="exact_match", score=0.9, threshold=0.7)],
            )
        ],
    )

    storage.save_run(run_a)
    storage.save_run(run_b)

    response = mcp_tools.analyze_compare(
        {
            "run_id_a": "run-a",
            "run_id_b": "run-b",
            "db_path": db_path,
        }
    )

    assert response.errors == []
    assert response.comparison_report_path
    assert Path(response.comparison_report_path).exists()
    assert response.artifacts is not None
    assert response.artifacts.json_path
    assert Path(response.artifacts.json_path).exists()
