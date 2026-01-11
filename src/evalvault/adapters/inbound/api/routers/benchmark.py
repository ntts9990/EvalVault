"""API Router for Benchmark Runs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from evalvault.adapters.inbound.api.main import AdapterDep

router = APIRouter()


class BenchmarkTaskScoreResponse(BaseModel):
    task_name: str
    accuracy: float
    num_samples: int
    metrics: dict[str, float]
    version: str


class BenchmarkRunResponse(BaseModel):
    run_id: str
    benchmark_type: str
    model_name: str
    backend: str
    tasks: list[str]
    status: str
    task_scores: list[BenchmarkTaskScoreResponse]
    overall_accuracy: float | None
    num_fewshot: int
    started_at: str | None
    finished_at: str | None
    duration_seconds: float
    error_message: str | None
    phoenix_trace_id: str | None
    metadata: dict[str, Any]

    model_config = {"from_attributes": True}


class BenchmarkRunSummaryResponse(BaseModel):
    run_id: str
    benchmark_type: str
    model_name: str
    backend: str
    status: str
    overall_accuracy: float | None
    started_at: str | None
    duration_seconds: float

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[BenchmarkRunSummaryResponse])
def list_benchmark_runs(
    adapter: AdapterDep,
    benchmark_type: str | None = Query(
        None, description="Filter by benchmark type (kmmlu, mmlu, custom)"
    ),
    model_name: str | None = Query(None, description="Filter by model name"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
) -> list[dict[str, Any]]:
    """List benchmark runs with optional filtering."""
    try:
        runs = adapter.storage.list_benchmark_runs(
            benchmark_type=benchmark_type,
            model_name=model_name,
            limit=limit,
        )
        return [
            {
                "run_id": run.run_id,
                "benchmark_type": run.benchmark_type.value,
                "model_name": run.model_name,
                "backend": run.backend,
                "status": run.status.value,
                "overall_accuracy": run.overall_accuracy,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "duration_seconds": run.duration_seconds,
            }
            for run in runs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}", response_model=BenchmarkRunResponse)
def get_benchmark_run(run_id: str, adapter: AdapterDep) -> dict[str, Any]:
    """Get detailed information for a specific benchmark run."""
    try:
        run = adapter.storage.get_benchmark_run(run_id)
        return {
            "run_id": run.run_id,
            "benchmark_type": run.benchmark_type.value,
            "model_name": run.model_name,
            "backend": run.backend,
            "tasks": run.tasks,
            "status": run.status.value,
            "task_scores": [
                {
                    "task_name": ts.task_name,
                    "accuracy": ts.accuracy,
                    "num_samples": ts.num_samples,
                    "metrics": ts.metrics,
                    "version": ts.version,
                }
                for ts in run.task_scores
            ],
            "overall_accuracy": run.overall_accuracy,
            "num_fewshot": run.num_fewshot,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "duration_seconds": run.duration_seconds,
            "error_message": run.error_message,
            "phoenix_trace_id": run.phoenix_trace_id,
            "metadata": run.metadata,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Benchmark run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{run_id}")
def delete_benchmark_run(run_id: str, adapter: AdapterDep) -> dict[str, str]:
    """Delete a benchmark run."""
    try:
        deleted = adapter.storage.delete_benchmark_run(run_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Benchmark run not found")
        return {"message": f"Benchmark run {run_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
