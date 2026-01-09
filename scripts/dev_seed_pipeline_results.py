"""Seed pipeline_results with sample data for UI comparison demos."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.config.settings import get_settings

SEED_RESULTS = (
    "seed-analysis-a",
    "seed-analysis-b",
)


def _build_priority_summary(case_prefix: str) -> dict[str, Any]:
    return {
        "bottom_cases": [
            {
                "test_case_id": f"{case_prefix}-low-1",
                "failed_metrics": ["faithfulness"],
                "avg_score": 0.42,
            },
        ],
        "impact_cases": [
            {
                "test_case_id": f"{case_prefix}-impact-1",
                "failed_metrics": ["context_precision"],
                "avg_score": 0.37,
            },
        ],
        "bottom_count": 1,
        "impact_count": 1,
        "total_cases": 12,
        "run_metadata": {
            "dataset_name": "sample_dataset",
            "model_name": "sample_model",
        },
    }


def _build_record(
    *,
    result_id: str,
    created_at: datetime,
    intent: str,
    query: str,
    duration_ms: float,
    metrics: dict[str, float],
    priority_summary: dict[str, Any],
    node_results: dict[str, Any],
) -> dict[str, Any]:
    started_at = created_at - timedelta(milliseconds=duration_ms)
    finished_at = created_at
    return {
        "result_id": result_id,
        "intent": intent,
        "query": query,
        "run_id": None,
        "pipeline_id": "seed-pipeline",
        "profile": "dev",
        "tags": ["seed", "compare"],
        "metadata": {"seed": True, "source": "dev_seed"},
        "is_complete": True,
        "duration_ms": duration_ms,
        "final_output": {
            "metrics": metrics,
            "priority_summary": priority_summary,
            "report": {
                "report": (
                    "## Seed Report\n\n"
                    "- Sample metrics summary for UI comparison.\n"
                    "- This is mock data for local demos."
                )
            },
        },
        "node_results": node_results,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "created_at": created_at.isoformat(),
    }


def seed_pipeline_results() -> list[str]:
    settings = get_settings()
    storage = SQLiteStorageAdapter(settings.evalvault_db_path)
    existing = storage.list_pipeline_results(limit=200)
    existing_ids = {item.get("result_id") for item in existing}
    missing = [seed_id for seed_id in SEED_RESULTS if seed_id not in existing_ids]
    if not missing:
        return []

    now = datetime.now()
    priority_a = _build_priority_summary("case-a")
    priority_b = _build_priority_summary("case-b")
    priority_b["bottom_cases"].append(
        {
            "test_case_id": "case-b-low-2",
            "failed_metrics": ["answer_relevancy"],
            "avg_score": 0.38,
        }
    )
    priority_b["bottom_count"] = 2

    record_a = _build_record(
        result_id=SEED_RESULTS[0],
        created_at=now - timedelta(minutes=12),
        intent="generate_summary",
        query="Summarize the latest evaluation results.",
        duration_ms=1320,
        metrics={"score": 0.72, "precision": 0.88, "recall": 0.81},
        priority_summary=priority_a,
        node_results={
            "statistics": {"status": "completed"},
            "priority_summary": {"status": "completed", "output": priority_a},
            "report": {"status": "failed", "error": "LLM timeout"},
        },
    )

    record_b = _build_record(
        result_id=SEED_RESULTS[1],
        created_at=now - timedelta(minutes=4),
        intent="generate_summary",
        query="Summarize the latest evaluation results.",
        duration_ms=980,
        metrics={"score": 0.81, "precision": 0.92, "recall": 0.87},
        priority_summary=priority_b,
        node_results={
            "statistics": {"status": "completed"},
            "priority_summary": {"status": "completed", "output": priority_b},
            "report": {"status": "completed"},
        },
    )

    for record in (record_a, record_b):
        if record["result_id"] in missing:
            storage.save_pipeline_result(record)

    return missing


def main() -> None:
    inserted = seed_pipeline_results()
    if inserted:
        print(f"Seeded pipeline results: {', '.join(inserted)}")
    else:
        print("Seed pipeline results already exist.")


if __name__ == "__main__":
    main()
