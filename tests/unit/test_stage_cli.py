"""CLI tests for stage commands."""

import json
from pathlib import Path

from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app
from evalvault.adapters.inbound.cli.commands import stage as stage_commands
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter


def test_stage_ingest_jsonl(tmp_path: Path) -> None:
    db_path = tmp_path / "stage.db"
    file_path = tmp_path / "stage_events.jsonl"
    file_path.write_text(
        "\n".join(
            [
                '{"run_id":"run-001","stage_id":"stg-0","stage_type":"system_prompt","status":"success"}',
                '{"run_id":"run-001","stage_id":"stg-1","stage_type":"input","status":"success"}',
                '{"run_id":"run-001","stage_id":"stg-2","stage_type":"retrieval","status":"success"}',
                '{"run_id":"run-001","stage_id":"stg-3","stage_type":"output","status":"success"}',
            ]
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(app, ["stage", "ingest", str(file_path), "--db", str(db_path)])

    assert result.exit_code == 0

    storage = SQLiteStorageAdapter(db_path=db_path)
    events = storage.list_stage_events("run-001")
    assert len(events) == 4


def test_stage_compute_metrics(tmp_path: Path) -> None:
    db_path = tmp_path / "stage_metrics.db"
    file_path = tmp_path / "stage_events.jsonl"
    file_path.write_text(
        "\n".join(
            [
                '{"run_id":"run-002","stage_id":"stg-sys","stage_type":"system_prompt","status":"success"}',
                '{"run_id":"run-002","stage_id":"stg-input","stage_type":"input","status":"success"}',
                '{"run_id":"run-002","stage_id":"stg-retrieval","stage_type":"retrieval","status":"success",'
                '"attributes":{"doc_ids":["doc-1","doc-2"],"scores":[0.9,0.3],"top_k":2}}',
                '{"run_id":"run-002","stage_id":"stg-output","stage_type":"output","status":"success",'
                '"attributes":{"tokens_in":200,"tokens_out":50}}',
            ]
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    ingest_result = runner.invoke(app, ["stage", "ingest", str(file_path), "--db", str(db_path)])
    assert ingest_result.exit_code == 0

    compute_result = runner.invoke(
        app, ["stage", "compute-metrics", "run-002", "--db", str(db_path)]
    )
    assert compute_result.exit_code == 0

    storage = SQLiteStorageAdapter(db_path=db_path)
    metrics = storage.list_stage_metrics("run-002")
    metric_names = {metric.metric_name for metric in metrics}
    assert "retrieval.result_count" in metric_names
    assert "retrieval.avg_score" in metric_names
    assert "output.token_ratio" in metric_names


def test_stage_report(tmp_path: Path) -> None:
    db_path = tmp_path / "stage_report.db"
    file_path = tmp_path / "stage_events.jsonl"
    file_path.write_text(
        "\n".join(
            [
                '{"run_id":"run-003","stage_id":"stg-sys","stage_type":"system_prompt","status":"success"}',
                '{"run_id":"run-003","stage_id":"stg-input","stage_type":"input","status":"success",'
                '"attributes":{"query":"보험 약관 요약해줘"}}',
                '{"run_id":"run-003","stage_id":"stg-retrieval","stage_type":"retrieval","status":"success",'
                '"attributes":{"doc_ids":["doc-1","doc-2"],"scores":[0.8,0.4],"top_k":2}}',
                '{"run_id":"run-003","stage_id":"stg-output","stage_type":"output","status":"success",'
                '"attributes":{"tokens_in":200,"tokens_out":50,"citations":["doc-1"]}}',
            ]
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    ingest_result = runner.invoke(app, ["stage", "ingest", str(file_path), "--db", str(db_path)])
    assert ingest_result.exit_code == 0

    report_result = runner.invoke(app, ["stage", "report", "run-003", "--db", str(db_path)])
    assert report_result.exit_code == 0

    storage = SQLiteStorageAdapter(db_path=db_path)
    metrics = storage.list_stage_metrics("run-003")
    assert metrics


def test_load_thresholds_map_with_profile(tmp_path: Path) -> None:
    thresholds_path = tmp_path / "thresholds.json"
    thresholds_path.write_text(
        json.dumps(
            {
                "default": {
                    "rerank.keep_rate": 0.25,
                    "output.latency_ms": 3000.0,
                    "output.citation_count": 1.0,
                },
                "profiles": {"prod": {"output.latency_ms": 2000.0, "output.citation_count": 2.0}},
            }
        ),
        encoding="utf-8",
    )

    thresholds = stage_commands._load_thresholds_map(thresholds_path, profile="prod")

    assert thresholds["rerank.keep_rate"] == 0.25
    assert thresholds["output.latency_ms"] == 2000.0
    assert thresholds["output.citation_count"] == 2.0
