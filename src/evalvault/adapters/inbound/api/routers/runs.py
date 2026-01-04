"""API Router for Evaluation Runs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from evalvault.adapters.inbound.api.main import AdapterDep
from evalvault.domain.entities import EvaluationRun

router = APIRouter()


# --- Pydantic Models for Response ---


class RunSummaryResponse(BaseModel):
    """Evaluation Run Summary Response Model."""

    run_id: str
    dataset_name: str
    model_name: str
    pass_rate: float
    total_test_cases: int
    started_at: str  # ISO format string
    finished_at: str | None = None
    metrics_evaluated: list[str] = []
    phoenix_precision: float | None = None
    phoenix_drift: float | None = None
    phoenix_experiment_url: str | None = None

    model_config = {"from_attributes": True}


class QualityGateResultResponse(BaseModel):
    metric: str
    score: float
    threshold: float
    passed: bool
    gap: float


class QualityGateReportResponse(BaseModel):
    run_id: str
    overall_passed: bool
    results: list[QualityGateResultResponse]
    regression_detected: bool
    regression_amount: float | None = None


# --- Endpoints ---


@router.get("/", response_model=list[RunSummaryResponse])
def list_runs(
    adapter: AdapterDep,
    limit: int = 50,
    dataset_name: str | None = Query(None, description="Filter by dataset name"),
    model_name: str | None = Query(None, description="Filter by model name"),
) -> list[Any]:
    """List evaluation runs."""
    from evalvault.ports.inbound.web_port import RunFilters

    filters = RunFilters(dataset_name=dataset_name, model_name=model_name)
    summaries = adapter.list_runs(limit=limit, filters=filters)

    # Convert RunSummary dataclass to dict/Pydantic compatible format
    # The adapter returns RunSummary objects which matches our response model mostly
    return [
        {
            "run_id": s.run_id,
            "dataset_name": s.dataset_name,
            "model_name": s.model_name,
            "pass_rate": s.pass_rate,
            "total_test_cases": s.total_test_cases,
            "started_at": s.started_at.isoformat(),
            "finished_at": s.finished_at.isoformat() if s.finished_at else None,
            "metrics_evaluated": s.metrics_evaluated,
            "phoenix_precision": s.phoenix_precision,
            "phoenix_drift": s.phoenix_drift,
            "phoenix_experiment_url": s.phoenix_experiment_url,
        }
        for s in summaries
    ]


@router.get("/{run_id}", response_model=None)
def get_run_details(run_id: str, adapter: AdapterDep) -> dict[str, Any]:
    """Get detailed information for a specific run."""
    try:
        run: EvaluationRun = adapter.get_run_details(run_id)
        # Using to_summary_dict() or returning full object.
        # Returning full object might be complex due to validation, so we start with summary dict
        # and enrich it with results if needed.
        # For now, let's return a detailed dict.
        return {
            "summary": run.to_summary_dict(),
            "results": [
                {
                    "test_case_id": r.test_case_id,
                    "question": r.question,
                    "answer": r.answer,
                    "ground_truth": r.ground_truth,
                    "contexts": r.contexts,
                    "metrics": [
                        {
                            "name": m.name,
                            "score": m.score,
                            "passed": m.passed,
                            "reason": m.reason,
                        }
                        for m in r.metrics
                    ],
                }
                for r in run.results
            ],
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/quality-gate", response_model=QualityGateReportResponse)
def check_quality_gate(run_id: str, adapter: AdapterDep):
    """Check quality gate status for a run."""
    try:
        report = adapter.check_quality_gate(run_id)
        return report
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
