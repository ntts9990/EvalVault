from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from evalvault.adapters.inbound.api.main import AdapterDep

router = APIRouter()


class JudgeCalibrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    labels_source: Literal["feedback", "gold", "hybrid"] = "feedback"
    method: Literal["platt", "isotonic", "temperature", "none"] = "isotonic"
    metrics: list[str] | None = None
    holdout_ratio: float = Field(0.2, gt=0.0, lt=1.0)
    seed: int = Field(42, ge=0)
    parallel: bool = False
    concurrency: int = Field(8, ge=1)


class JudgeCalibrationCaseResponse(BaseModel):
    test_case_id: str
    raw_score: float
    calibrated_score: float
    label: float | None = None
    label_source: str | None = None


class JudgeCalibrationMetricResponse(BaseModel):
    metric: str
    method: str
    sample_count: int
    label_count: int
    mae: float | None
    pearson: float | None
    spearman: float | None
    temperature: float | None = None
    parameters: dict[str, float | None] = Field(default_factory=dict)
    gate_passed: bool | None = None
    warning: str | None = None


class JudgeCalibrationSummaryResponse(BaseModel):
    calibration_id: str
    run_id: str
    labels_source: str
    method: str
    metrics: list[str]
    holdout_ratio: float
    seed: int
    total_labels: int
    total_samples: int
    gate_passed: bool
    gate_threshold: float | None = None
    notes: list[str] = Field(default_factory=list)
    created_at: str


class JudgeCalibrationResponse(BaseModel):
    calibration_id: str
    status: Literal["ok", "degraded"]
    started_at: str
    finished_at: str
    duration_ms: int
    artifacts: dict[str, str]
    summary: JudgeCalibrationSummaryResponse
    metrics: list[JudgeCalibrationMetricResponse]
    case_results: dict[str, list[JudgeCalibrationCaseResponse]]
    warnings: list[str]


class JudgeCalibrationHistoryItem(BaseModel):
    calibration_id: str
    run_id: str
    labels_source: str
    method: str
    metrics: list[str]
    holdout_ratio: float
    seed: int
    total_labels: int
    total_samples: int
    gate_passed: bool
    gate_threshold: float | None = None
    created_at: str


@router.post("/judge", response_model=JudgeCalibrationResponse)
def run_judge_calibration(
    request: JudgeCalibrationRequest, adapter: AdapterDep
) -> JudgeCalibrationResponse:
    try:
        payload = adapter.run_judge_calibration(
            run_id=request.run_id,
            labels_source=request.labels_source,
            method=request.method,
            metrics=request.metrics or [],
            holdout_ratio=request.holdout_ratio,
            seed=request.seed,
            parallel=request.parallel,
            concurrency=request.concurrency,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return JudgeCalibrationResponse.model_validate(payload)


@router.get("/judge/history", response_model=list[JudgeCalibrationHistoryItem])
def list_calibrations(
    adapter: AdapterDep,
    limit: int = Query(20, ge=1, le=200),
) -> list[JudgeCalibrationHistoryItem]:
    entries = adapter.list_judge_calibrations(limit=limit)
    return [JudgeCalibrationHistoryItem.model_validate(entry) for entry in entries]


@router.get("/judge/{calibration_id}", response_model=JudgeCalibrationResponse)
def get_calibration_result(calibration_id: str, adapter: AdapterDep) -> JudgeCalibrationResponse:
    try:
        payload = adapter.get_judge_calibration(calibration_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return JudgeCalibrationResponse.model_validate(payload)
