"""API Router for Evaluation Runs."""

from __future__ import annotations

import asyncio
import csv
import json
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, Response, StreamingResponse
from pydantic import BaseModel

from evalvault.adapters.inbound.api.main import AdapterDep
from evalvault.adapters.outbound.dataset.templates import (
    render_dataset_template_csv,
    render_dataset_template_json,
    render_dataset_template_xlsx,
)
from evalvault.adapters.outbound.debug.report_renderer import render_markdown
from evalvault.adapters.outbound.domain_memory import build_domain_memory_adapter
from evalvault.adapters.outbound.report import DashboardGenerator
from evalvault.config.settings import get_settings
from evalvault.domain.entities import (
    CalibrationResult,
    EvaluationRun,
    SatisfactionFeedback,
)
from evalvault.domain.services.domain_learning_hook import DomainLearningHook
from evalvault.domain.services.ragas_prompt_overrides import (
    PromptOverrideError,
    normalize_ragas_prompt_overrides,
)
from evalvault.domain.services.visual_space_service import VisualSpaceQuery
from evalvault.ports.inbound.web_port import EvalProgress, EvalRequest

router = APIRouter()


# --- Pydantic Models for Response ---


class RunSummaryResponse(BaseModel):
    """Evaluation Run Summary Response Model."""

    run_id: str
    dataset_name: str
    project_name: str | None = None
    model_name: str
    pass_rate: float
    total_test_cases: int
    passed_test_cases: int
    started_at: str  # ISO format string
    finished_at: str | None = None
    metrics_evaluated: list[str] = []
    run_mode: str | None = None
    evaluation_task: str | None = None
    threshold_profile: str | None = None
    avg_metric_scores: dict[str, float] | None = None
    total_cost_usd: float | None = None
    phoenix_precision: float | None = None
    phoenix_drift: float | None = None
    phoenix_experiment_url: str | None = None
    feedback_count: int | None = None

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


class PromptDiffSummaryItem(BaseModel):
    role: str
    base_checksum: str | None = None
    target_checksum: str | None = None
    status: Literal["same", "diff", "missing"]
    base_name: str | None = None
    target_name: str | None = None
    base_kind: str | None = None
    target_kind: str | None = None


class PromptDiffEntry(BaseModel):
    role: str
    lines: list[str]
    truncated: bool


class PromptDiffResponse(BaseModel):
    base_run_id: str
    target_run_id: str
    summary: list[PromptDiffSummaryItem]
    diffs: list[PromptDiffEntry]


class StartEvaluationRequest(BaseModel):
    dataset_path: str
    metrics: list[str]
    model: str
    evaluation_task: str | None = None
    parallel: bool = True
    batch_size: int = 5
    thresholds: dict[str, float] | None = None
    threshold_profile: str | None = None
    project_name: str | None = None
    retriever_config: dict[str, Any] | None = None
    memory_config: dict[str, Any] | None = None
    tracker_config: dict[str, Any] | None = None
    stage_store: bool = False
    prompt_config: dict[str, Any] | None = None
    system_prompt: str | None = None
    system_prompt_name: str | None = None
    prompt_set_name: str | None = None
    prompt_set_description: str | None = None
    ragas_prompts: dict[str, str] | None = None
    ragas_prompts_yaml: str | None = None


class DatasetItemResponse(BaseModel):
    name: str
    path: str
    type: str
    size: int


class ModelItemResponse(BaseModel):
    id: str
    name: str
    supports_tools: bool | None = None


class MetricSpecResponse(BaseModel):
    name: str
    description: str
    requires_ground_truth: bool
    requires_embeddings: bool
    source: str
    category: str
    signal_group: str


class ClusterMapItemResponse(BaseModel):
    test_case_id: str
    cluster_id: str


class ClusterMapFileResponse(BaseModel):
    name: str
    path: str
    size: int


class ClusterMapContentResponse(BaseModel):
    source: str
    items: list[ClusterMapItemResponse]


class ClusterMapResponse(BaseModel):
    run_id: str
    dataset_name: str
    map_id: str
    source: str | None = None
    created_at: str | None = None
    metadata: dict[str, Any] | None = None
    items: list[ClusterMapItemResponse]


class ClusterMapSaveRequest(BaseModel):
    source: str | None = None
    metadata: dict[str, Any] | None = None
    items: list[ClusterMapItemResponse]


class ClusterMapVersionResponse(BaseModel):
    map_id: str
    source: str | None = None
    created_at: str | None = None
    item_count: int


class ClusterMapSaveResponse(BaseModel):
    run_id: str
    map_id: str
    source: str | None = None
    created_at: str | None = None
    metadata: dict[str, Any] | None = None
    saved_count: int
    skipped_count: int = 0


class ClusterMapDeleteResponse(BaseModel):
    run_id: str
    map_id: str
    deleted_count: int


class FeedbackSaveRequest(BaseModel):
    test_case_id: str
    satisfaction_score: float | None = None
    thumb_feedback: Literal["up", "down", "none"] | None = None
    comment: str | None = None
    rater_id: str | None = None


class FeedbackResponse(BaseModel):
    feedback_id: str
    run_id: str
    test_case_id: str
    satisfaction_score: float | None = None
    thumb_feedback: str | None = None
    comment: str | None = None
    rater_id: str | None = None
    created_at: str | None = None


class FeedbackSummaryResponse(BaseModel):
    avg_satisfaction_score: float | None = None
    thumb_up_rate: float | None = None
    total_feedback: int


class VisualSpaceRequest(BaseModel):
    granularity: Literal["run", "case", "cluster"] = "case"
    base_run_id: str | None = None
    auto_base: bool = True
    include: list[str] | None = None
    limit: int | None = None
    offset: int | None = None
    cluster_map: dict[str, str] | None = None


def _serialize_run_details(
    run: EvaluationRun,
    *,
    calibration: CalibrationResult | None = None,
) -> dict[str, Any]:
    summary = run.to_summary_dict()
    if calibration is not None:
        summary.update(
            {
                "avg_satisfaction_score": calibration.summary.avg_satisfaction_score,
                "thumb_up_rate": calibration.summary.thumb_up_rate,
                "imputed_ratio": calibration.summary.imputed_ratio,
            }
        )
    payload = {
        "summary": summary,
        "results": [
            {
                "test_case_id": result.test_case_id,
                "question": result.question,
                "answer": result.answer,
                "ground_truth": result.ground_truth,
                "contexts": result.contexts,
                "metrics": [
                    {
                        "name": metric.name,
                        "score": metric.score,
                        "passed": metric.passed,
                        "reason": metric.reason,
                    }
                    for metric in result.metrics
                ],
                "calibrated_satisfaction": (
                    calibration.cases[result.test_case_id].calibrated_satisfaction
                    if calibration and result.test_case_id in calibration.cases
                    else None
                ),
                "imputed": (
                    calibration.cases[result.test_case_id].imputed
                    if calibration and result.test_case_id in calibration.cases
                    else False
                ),
                "imputation_source": (
                    calibration.cases[result.test_case_id].imputation_source
                    if calibration and result.test_case_id in calibration.cases
                    else None
                ),
            }
            for result in run.results
        ],
    }
    prompt_set_detail = (run.tracker_metadata or {}).get("prompt_set_detail")
    if prompt_set_detail:
        payload["prompt_set"] = prompt_set_detail
    return payload


def _parse_cluster_map_csv(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as file:
        reader = csv.reader(file)
        rows = list(reader)
    if not rows:
        return mapping
    start_index = 0
    header = [cell.strip().lower() for cell in rows[0]]
    if "test_case_id" in header and "cluster_id" in header:
        start_index = 1
    for row in rows[start_index:]:
        if len(row) < 2:
            continue
        test_case_id = row[0].strip()
        cluster_id = row[1].strip()
        if not test_case_id or not cluster_id:
            continue
        mapping[test_case_id] = cluster_id
    return mapping


def _find_cluster_map_for_run(run: EvaluationRun) -> tuple[dict[str, str], str] | None:
    if not run.results:
        return None
    dataset_name = (run.dataset_name or "").strip()
    search_dirs = [Path("data/datasets"), Path("data/inputs")]
    case_ids = {result.test_case_id for result in run.results}
    candidate_basenames = {dataset_name, Path(dataset_name).stem} if dataset_name else set()
    for base in candidate_basenames:
        if not base:
            continue
        for dir_path in search_dirs:
            candidate = dir_path / f"{base}_cluster_map.csv"
            if candidate.exists():
                mapping = _parse_cluster_map_csv(candidate)
                if mapping:
                    return mapping, candidate.name

    best_match: tuple[float, int, dict[str, str], str] | None = None
    for dir_path in search_dirs:
        if not dir_path.exists():
            continue
        for candidate in dir_path.glob("*_cluster_map.csv"):
            mapping = _parse_cluster_map_csv(candidate)
            if not mapping:
                continue
            overlap = len(case_ids.intersection(mapping.keys()))
            if overlap == 0:
                continue
            precision = overlap / max(1, len(mapping))
            if best_match is None or (precision, overlap) > (best_match[0], best_match[1]):
                best_match = (precision, overlap, mapping, candidate.name)

    if best_match:
        _, _, mapping, name = best_match
        return mapping, name
    return None


def _list_cluster_map_files() -> list[ClusterMapFileResponse]:
    files: list[ClusterMapFileResponse] = []
    search_dirs = [Path("data/datasets"), Path("data/inputs")]
    for dir_path in search_dirs:
        if not dir_path.exists():
            continue
        for candidate in dir_path.glob("*_cluster_map.csv"):
            files.append(
                ClusterMapFileResponse(
                    name=candidate.name,
                    path=str(candidate.absolute()),
                    size=candidate.stat().st_size,
                )
            )
    return sorted(files, key=lambda item: item.name)


def _resolve_cluster_map_path(file_name: str) -> Path | None:
    if Path(file_name).name != file_name:
        return None
    if not file_name.endswith("_cluster_map.csv"):
        return None
    search_dirs = [Path("data/datasets"), Path("data/inputs")]
    for dir_path in search_dirs:
        candidate = dir_path / file_name
        if candidate.exists():
            return candidate
    return None


def _build_case_counts(base_run: EvaluationRun, target_run: EvaluationRun) -> dict[str, int]:
    base_map = {result.test_case_id: result for result in base_run.results}
    target_map = {result.test_case_id: result for result in target_run.results}
    case_ids = set(base_map) | set(target_map)
    counts = {
        "regressions": 0,
        "improvements": 0,
        "same_pass": 0,
        "same_fail": 0,
        "new": 0,
        "removed": 0,
    }

    for case_id in case_ids:
        base_case = base_map.get(case_id)
        target_case = target_map.get(case_id)
        if base_case is None:
            counts["new"] += 1
            continue
        if target_case is None:
            counts["removed"] += 1
            continue

        base_passed = base_case.all_passed
        target_passed = target_case.all_passed
        if base_passed and target_passed:
            counts["same_pass"] += 1
        elif not base_passed and not target_passed:
            counts["same_fail"] += 1
        elif base_passed and not target_passed:
            counts["regressions"] += 1
        else:
            counts["improvements"] += 1

    return counts


# --- Options Endpoints ---


@router.get("/options/datasets", response_model=list[DatasetItemResponse])
def list_datasets(adapter: AdapterDep):
    """Get available datasets."""
    return adapter.list_datasets()


@router.post("/options/datasets")
async def upload_dataset(adapter: AdapterDep, file: UploadFile = File(...)):
    """Upload a new dataset file."""
    try:
        content = await file.read()
        saved_path = adapter.save_dataset_file(file.filename, content)
        return {
            "message": "Dataset uploaded successfully",
            "path": saved_path,
            "filename": file.filename,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save dataset: {e}")


@router.post("/options/retriever-docs")
async def upload_retriever_docs(adapter: AdapterDep, file: UploadFile = File(...)):
    """Upload retriever documents file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".json", ".jsonl", ".txt"}:
        raise HTTPException(status_code=400, detail="Unsupported retriever docs format.")

    try:
        content = await file.read()
        saved_path = adapter.save_retriever_docs_file(file.filename, content)
        return {
            "message": "Retriever docs uploaded successfully",
            "path": saved_path,
            "filename": file.filename,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save retriever docs: {e}")


@router.get("/options/models", response_model=list[ModelItemResponse])
def list_models(
    adapter: AdapterDep,
    provider: str | None = Query(None, description="Filter by provider (ollama, openai, etc.)"),
):
    """Get available models."""
    return adapter.list_models(provider=provider)


@router.get("/options/metrics", response_model=list[str])
def list_metrics(adapter: AdapterDep):
    """Get available metrics."""
    return adapter.get_available_metrics()


@router.get("/options/metric-specs", response_model=list[MetricSpecResponse])
def list_metric_specs(adapter: AdapterDep):
    """Get available metrics with metadata."""
    return adapter.get_metric_specs()


@router.get("/options/cluster-maps", response_model=list[ClusterMapFileResponse])
def list_cluster_maps():
    """List available cluster map CSV files."""
    return _list_cluster_map_files()


@router.get("/options/cluster-maps/{file_name}", response_model=ClusterMapContentResponse)
def get_cluster_map_file(file_name: str):
    """Get cluster map content from a named CSV file."""
    resolved = _resolve_cluster_map_path(file_name)
    if resolved is None:
        raise HTTPException(status_code=400, detail="Invalid cluster map file name")
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Cluster map not found")
    mapping = _parse_cluster_map_csv(resolved)
    items = [
        ClusterMapItemResponse(test_case_id=test_case_id, cluster_id=cluster_id)
        for test_case_id, cluster_id in mapping.items()
    ]
    return ClusterMapContentResponse(source=resolved.name, items=items)


@router.get("/options/dataset-templates/{template_format}")
def get_dataset_template(template_format: str) -> Response:
    """Download an empty dataset template."""
    fmt = template_format.lower()
    if fmt == "json":
        content = render_dataset_template_json()
        return Response(
            content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=dataset_template.json"},
        )
    if fmt == "csv":
        content = render_dataset_template_csv()
        return Response(
            content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=dataset_template.csv"},
        )
    if fmt == "xlsx":
        content = render_dataset_template_xlsx()
        return Response(
            content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=dataset_template.xlsx"},
        )
    raise HTTPException(status_code=400, detail="Unsupported template format")


@router.get("/{run_id}/cluster-map", response_model=ClusterMapResponse)
def get_cluster_map(run_id: str, adapter: AdapterDep):
    """Get cluster map for a run if available."""
    try:
        run = adapter.get_run_details(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    stored = None
    try:
        stored = adapter.get_run_cluster_map(run_id)
    except RuntimeError:
        stored = None

    if stored:
        mapping = stored.mapping
        source = stored.source
        items = [
            ClusterMapItemResponse(test_case_id=test_case_id, cluster_id=cluster_id)
            for test_case_id, cluster_id in mapping.items()
        ]
        return ClusterMapResponse(
            run_id=run_id,
            dataset_name=run.dataset_name,
            map_id=stored.map_id,
            source=source,
            created_at=stored.created_at.isoformat() if stored.created_at else None,
            metadata=stored.metadata,
            items=items,
        )

    match = _find_cluster_map_for_run(run)
    if not match:
        raise HTTPException(status_code=404, detail="Cluster map not found")
    mapping, source = match
    try:
        map_id = adapter.save_run_cluster_map(run_id, mapping, source)
    except RuntimeError:
        map_id = "legacy"
    items = [
        ClusterMapItemResponse(test_case_id=test_case_id, cluster_id=cluster_id)
        for test_case_id, cluster_id in mapping.items()
    ]
    return ClusterMapResponse(
        run_id=run_id,
        dataset_name=run.dataset_name,
        map_id=map_id,
        source=source,
        created_at=None,
        metadata=None,
        items=items,
    )


@router.post("/{run_id}/cluster-map", response_model=ClusterMapSaveResponse)
def save_cluster_map(
    run_id: str,
    payload: ClusterMapSaveRequest,
    adapter: AdapterDep,
) -> ClusterMapSaveResponse:
    """Save a cluster map for a run."""
    if not payload.items:
        raise HTTPException(status_code=400, detail="Cluster map is empty")
    try:
        run = adapter.get_run_details(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    valid_ids = {result.test_case_id for result in run.results}
    mapping: dict[str, str] = {}
    skipped = 0
    for item in payload.items:
        if item.test_case_id in valid_ids:
            mapping[item.test_case_id] = item.cluster_id
        else:
            skipped += 1

    if not mapping:
        raise HTTPException(status_code=400, detail="No matching test_case_id for run")

    try:
        map_id = adapter.save_run_cluster_map(
            run_id,
            mapping,
            payload.source,
            metadata=payload.metadata,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ClusterMapSaveResponse(
        run_id=run_id,
        map_id=map_id,
        source=payload.source,
        created_at=datetime.now().isoformat(),
        metadata=payload.metadata,
        saved_count=len(mapping),
        skipped_count=skipped,
    )


@router.post("/{run_id}/cluster-maps", response_model=ClusterMapSaveResponse)
def save_cluster_map_version(
    run_id: str,
    payload: ClusterMapSaveRequest,
    adapter: AdapterDep,
) -> ClusterMapSaveResponse:
    """Save a cluster map version for a run."""
    return save_cluster_map(run_id, payload, adapter)


@router.get("/{run_id}/cluster-maps", response_model=list[ClusterMapVersionResponse])
def list_run_cluster_maps(run_id: str, adapter: AdapterDep) -> list[ClusterMapVersionResponse]:
    """List cluster map versions for a run."""
    try:
        adapter.get_run_details(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        maps = adapter.list_run_cluster_maps(run_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [
        ClusterMapVersionResponse(
            map_id=entry.map_id,
            source=entry.source,
            created_at=entry.created_at.isoformat() if entry.created_at else None,
            item_count=entry.item_count,
        )
        for entry in maps
    ]


@router.get("/{run_id}/cluster-maps/{map_id}", response_model=ClusterMapResponse)
def get_cluster_map_version(run_id: str, map_id: str, adapter: AdapterDep) -> ClusterMapResponse:
    """Get a specific cluster map version for a run."""
    try:
        run = adapter.get_run_details(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        stored = adapter.get_run_cluster_map(run_id, map_id=map_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if stored is None:
        raise HTTPException(status_code=404, detail="Cluster map not found")

    items = [
        ClusterMapItemResponse(test_case_id=test_case_id, cluster_id=cluster_id)
        for test_case_id, cluster_id in stored.mapping.items()
    ]
    return ClusterMapResponse(
        run_id=run_id,
        dataset_name=run.dataset_name,
        map_id=stored.map_id,
        source=stored.source,
        created_at=stored.created_at.isoformat() if stored.created_at else None,
        metadata=stored.metadata,
        items=items,
    )


@router.delete("/{run_id}/cluster-maps/{map_id}", response_model=ClusterMapDeleteResponse)
def delete_cluster_map_version(
    run_id: str, map_id: str, adapter: AdapterDep
) -> ClusterMapDeleteResponse:
    """Delete a cluster map version for a run."""
    try:
        adapter.get_run_details(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        deleted = adapter.delete_run_cluster_map(run_id, map_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Cluster map not found")

    return ClusterMapDeleteResponse(run_id=run_id, map_id=map_id, deleted_count=deleted)


@router.post("/{run_id}/visual-space", response_model=None)
def get_visual_space(
    run_id: str, payload: VisualSpaceRequest, adapter: AdapterDep
) -> dict[str, Any]:
    """Build visual space coordinates for a run."""
    try:
        adapter.get_run_details(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    include = set(payload.include) if payload.include else None
    query = VisualSpaceQuery(
        run_id=run_id,
        granularity=payload.granularity,
        base_run_id=payload.base_run_id,
        auto_base=payload.auto_base,
        include=include,
        limit=payload.limit,
        offset=payload.offset,
        cluster_map=payload.cluster_map,
    )

    try:
        return adapter.get_visual_space(query)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --- Endpoints ---


@router.get("/compare", response_model=None)
def compare_runs(
    adapter: AdapterDep,
    base: str | None = Query(None, description="Base run ID"),
    target: str | None = Query(None, description="Target run ID"),
    run_id1: str | None = Query(None, description="Base run ID (alias)"),
    run_id2: str | None = Query(None, description="Target run ID (alias)"),
) -> dict[str, Any]:
    """Compare two evaluation runs and return summary + run details."""
    base_id = base or run_id1
    target_id = target or run_id2
    if not base_id or not target_id:
        raise HTTPException(status_code=400, detail="base and target run IDs are required")

    try:
        base_run = adapter.get_run_details(base_id)
        target_run = adapter.get_run_details(target_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    metrics = sorted(set(base_run.metrics_evaluated) | set(target_run.metrics_evaluated))
    metric_deltas = []
    for metric in metrics:
        base_score = base_run.get_avg_score(metric)
        target_score = target_run.get_avg_score(metric)
        delta = (
            target_score - base_score
            if base_score is not None and target_score is not None
            else None
        )
        metric_deltas.append(
            {
                "name": metric,
                "base": base_score,
                "target": target_score,
                "delta": delta,
            }
        )

    base_calibration = adapter.build_calibration(base_id)
    target_calibration = adapter.build_calibration(target_id)

    return {
        "base": _serialize_run_details(base_run, calibration=base_calibration),
        "target": _serialize_run_details(target_run, calibration=target_calibration),
        "metric_deltas": metric_deltas,
        "case_counts": _build_case_counts(base_run, target_run),
        "pass_rate_delta": target_run.pass_rate - base_run.pass_rate,
        "total_cases_delta": target_run.total_test_cases - base_run.total_test_cases,
    }


@router.post("/start", status_code=200)
async def start_evaluation_endpoint(
    request: StartEvaluationRequest,
    adapter: AdapterDep,
):
    """Start evaluation with streaming progress."""
    ragas_prompt_overrides = None
    if request.ragas_prompts_yaml or request.ragas_prompts:
        try:
            raw = request.ragas_prompts_yaml or request.ragas_prompts
            ragas_prompt_overrides = normalize_ragas_prompt_overrides(raw)
        except PromptOverrideError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    eval_req = EvalRequest(
        dataset_path=request.dataset_path,
        metrics=request.metrics,
        model_name=request.model,
        evaluation_task=request.evaluation_task or "qa",
        parallel=request.parallel,
        batch_size=request.batch_size,
        thresholds=request.thresholds or {},
        threshold_profile=request.threshold_profile,
        project_name=request.project_name,
        retriever_config=request.retriever_config,
        memory_config=request.memory_config,
        tracker_config=request.tracker_config,
        stage_store=request.stage_store,
        prompt_config=request.prompt_config,
        system_prompt=request.system_prompt,
        system_prompt_name=request.system_prompt_name,
        prompt_set_name=request.prompt_set_name,
        prompt_set_description=request.prompt_set_description,
        ragas_prompt_overrides=ragas_prompt_overrides,
    )

    queue = asyncio.Queue()

    def progress_callback(progress: EvalProgress):
        # 진행 상황을 큐에 추가
        queue.put_nowait(
            {
                "type": "progress",
                "data": {
                    "current": progress.current,
                    "total": progress.total,
                    "percent": progress.percent,
                    "status": progress.status,
                    "message": progress.current_metric or progress.error_message or "",
                    "elapsed_seconds": progress.elapsed_seconds,
                    "eta_seconds": progress.eta_seconds,
                    "rate": progress.rate,
                },
            }
        )

    async def event_generator():
        # 평가 테스크 시작
        task = asyncio.create_task(adapter.run_evaluation(eval_req, on_progress=progress_callback))

        try:
            # Task가 완료될 때까지 Queue 모니터링
            while not task.done():
                try:
                    # 0.1초마다 큐 확인 또는 Task 상태 확인
                    data = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield json.dumps(data) + "\n"
                    queue.task_done()
                except TimeoutError:
                    continue

            # 남은 큐 아이템 처리
            while not queue.empty():
                data = await queue.get()
                yield json.dumps(data) + "\n"
                queue.task_done()

            # 결과 및 예외 확인
            if task.exception():
                raise task.exception()

            result = task.result()

            memory_config = request.memory_config or {}
            memory_enabled = bool(memory_config.get("enabled"))
            if memory_enabled:
                yield (
                    json.dumps({"type": "info", "message": "Learning from evaluation results..."})
                    + "\n"
                )

                try:
                    from pathlib import Path

                    settings = get_settings()
                    if memory_config.get("db_path"):
                        memory_db = memory_config.get("db_path")
                    elif settings.db_backend == "sqlite":
                        memory_db = settings.evalvault_memory_db_path
                    else:
                        memory_db = None
                    domain = memory_config.get("domain") or "default"
                    language = memory_config.get("language") or "ko"
                    memory_adapter = build_domain_memory_adapter(
                        settings=settings, db_path=Path(memory_db) if memory_db else None
                    )
                    hook = DomainLearningHook(memory_adapter)
                    await hook.on_evaluation_complete(
                        evaluation_run=result,
                        domain=domain,
                        language=language,
                    )
                    yield json.dumps({"type": "info", "message": "Domain memory updated."}) + "\n"
                except Exception as e:
                    yield (
                        json.dumps({"type": "warning", "message": f"Domain learning failed: {e}"})
                        + "\n"
                    )

            # 최종 결과 반환
            yield (
                json.dumps(
                    {"type": "result", "data": {"run_id": result.run_id, "status": "completed"}}
                )
                + "\n"
            )

        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@router.get("/", response_model=list[RunSummaryResponse])
def list_runs(
    adapter: AdapterDep,
    limit: int = 50,
    offset: int = Query(0, ge=0, description="Pagination offset"),
    dataset_name: str | None = Query(None, description="Filter by dataset name"),
    model_name: str | None = Query(None, description="Filter by model name"),
    include_feedback: bool = Query(False, description="Include feedback count"),
) -> list[Any]:
    """List evaluation runs."""
    from evalvault.ports.inbound.web_port import RunFilters

    filters = RunFilters(dataset_name=dataset_name, model_name=model_name)
    summaries = adapter.list_runs(limit=limit, offset=offset, filters=filters)
    feedback_counts: dict[str, int] = {}
    if include_feedback:
        feedback_counts = {
            summary.run_id: adapter.get_feedback_summary(summary.run_id).total_feedback
            for summary in summaries
        }

    # Convert RunSummary dataclass to dict/Pydantic compatible format
    # The adapter returns RunSummary objects which matches our response model mostly
    return [
        {
            "run_id": s.run_id,
            "dataset_name": s.dataset_name,
            "project_name": s.project_name,
            "model_name": s.model_name,
            "pass_rate": s.pass_rate,
            "total_test_cases": s.total_test_cases,
            "passed_test_cases": s.passed_test_cases,
            "started_at": s.started_at.isoformat(),
            "finished_at": s.finished_at.isoformat() if s.finished_at else None,
            "metrics_evaluated": s.metrics_evaluated,
            "run_mode": s.run_mode,
            "evaluation_task": s.evaluation_task,
            "threshold_profile": s.threshold_profile,
            "avg_metric_scores": s.avg_metric_scores or None,
            "total_cost_usd": s.total_cost_usd,
            "phoenix_precision": s.phoenix_precision,
            "phoenix_drift": s.phoenix_drift,
            "phoenix_experiment_url": s.phoenix_experiment_url,
            "feedback_count": feedback_counts.get(s.run_id) if include_feedback else None,
        }
        for s in summaries
    ]


@router.get("/{run_id}", response_model=None)
def get_run_details(run_id: str, adapter: AdapterDep) -> dict[str, Any]:
    """Get detailed information for a specific run."""
    try:
        run: EvaluationRun = adapter.get_run_details(run_id)
        calibration = adapter.build_calibration(run_id)
        return _serialize_run_details(run, calibration=calibration)
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{run_id}/feedback", response_model=FeedbackResponse)
def save_feedback(
    run_id: str,
    request: FeedbackSaveRequest,
    adapter: AdapterDep,
) -> dict[str, Any]:
    try:
        adapter.get_run_details(run_id)
        thumb_feedback = request.thumb_feedback
        if thumb_feedback == "none":
            thumb_feedback = None
        satisfaction_score = request.satisfaction_score
        if satisfaction_score is not None:
            satisfaction_score = max(1.0, min(5.0, satisfaction_score))
        feedback = SatisfactionFeedback(
            feedback_id="",
            run_id=run_id,
            test_case_id=request.test_case_id,
            satisfaction_score=satisfaction_score,
            thumb_feedback=thumb_feedback,
            comment=request.comment,
            rater_id=request.rater_id,
            created_at=datetime.now(),
        )
        feedback_id = adapter.save_feedback(feedback)
        saved = feedback.to_dict()
        saved["feedback_id"] = feedback_id
        return saved
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/feedback", response_model=list[FeedbackResponse])
def list_feedback(run_id: str, adapter: AdapterDep) -> list[dict[str, Any]]:
    try:
        adapter.get_run_details(run_id)
        feedbacks = adapter.list_feedback(run_id)
        return [feedback.to_dict() for feedback in feedbacks]
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/feedback/summary", response_model=FeedbackSummaryResponse)
def get_feedback_summary(run_id: str, adapter: AdapterDep) -> dict[str, Any]:
    try:
        adapter.get_run_details(run_id)
        summary = adapter.get_feedback_summary(run_id)
        return {
            "avg_satisfaction_score": summary.avg_satisfaction_score,
            "thumb_up_rate": summary.thumb_up_rate,
            "total_feedback": summary.total_feedback,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/stage-events", response_model=None)
def list_stage_events(
    run_id: str,
    adapter: AdapterDep,
    stage_type: str | None = Query(None, description="Filter by stage type"),
) -> list[dict[str, Any]]:
    """List stage events for a run."""
    try:
        adapter.get_run_details(run_id)
        events = adapter.list_stage_events(run_id, stage_type=stage_type)
        return [event.to_dict() for event in events]
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/stage-metrics", response_model=None)
def list_stage_metrics(
    run_id: str,
    adapter: AdapterDep,
    stage_id: str | None = Query(None, description="Filter by stage id"),
    metric_name: str | None = Query(None, description="Filter by metric name"),
) -> list[dict[str, Any]]:
    """List stage metrics for a run."""
    try:
        adapter.get_run_details(run_id)
        metrics = adapter.list_stage_metrics(
            run_id,
            stage_id=stage_id,
            metric_name=metric_name,
        )
        return [metric.to_dict() for metric in metrics]
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompt-diff", response_model=PromptDiffResponse)
def prompt_diff(
    adapter: AdapterDep,
    base_run_id: str = Query(..., description="Base run id"),
    target_run_id: str = Query(..., description="Target run id"),
    max_lines: int = Query(40, ge=1, le=200),
    include_diff: bool = Query(True),
):
    try:
        return adapter.compare_prompt_sets(
            base_run_id,
            target_run_id,
            max_lines=max_lines,
            include_diff=include_diff,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Prompt set not found")
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


@router.get("/{run_id}/debug-report", response_model=None)
def get_debug_report(
    run_id: str,
    adapter: AdapterDep,
    format: Literal["json", "markdown"] = Query("json", description="Report format"),
):
    try:
        report = adapter.build_debug_report(run_id)
        if format == "markdown":
            return PlainTextResponse(render_markdown(report))
        return report.to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/improvement")
def get_improvement_guide(
    run_id: str,
    adapter: AdapterDep,
    include_llm: bool = False,
):
    """Get improvement guide for a run."""
    try:
        report = adapter.get_improvement_guide(run_id, include_llm=include_llm)
        # ImprovementReport is a Pydantic model (or dataclass), we need to return it.
        return report
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/analysis-report", response_model=None)
def get_analysis_report(
    run_id: str,
    adapter: AdapterDep,
    format: Literal["markdown", "html"] = Query("markdown", description="Report format"),
    include_nlp: bool = Query(True, description="Include NLP analysis"),
    include_causal: bool = Query(True, description="Include causal analysis"),
    use_cache: bool = Query(True, description="Use cached report if available"),
    save: bool = Query(False, description="Save report to database"),
):
    """Generate analysis report (Markdown/HTML)."""
    try:
        report = adapter.generate_report(
            run_id,
            output_format=format,
            include_nlp=include_nlp,
            include_causal=include_causal,
            use_cache=use_cache,
            save=save,
        )
        if format == "html":
            return HTMLResponse(report)
        return PlainTextResponse(report)
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/dashboard", response_model=None)
def get_dashboard(
    run_id: str,
    adapter: AdapterDep,
    format: Literal["png", "svg", "pdf"] = Query("png", description="Dashboard format"),
    include_nlp: bool = Query(True, description="Include NLP analysis"),
    include_causal: bool = Query(True, description="Include causal analysis"),
):
    """Generate dashboard image for a run."""
    try:
        dashboard_payload = adapter.build_dashboard_payload(
            run_id,
            include_nlp=include_nlp,
            include_causal=include_causal,
        )
        generator = DashboardGenerator()
        fig = generator.generate_evaluation_dashboard(
            run_id,
            analysis_data=dashboard_payload,
        )
        buffer = BytesIO()
        fig.savefig(buffer, format=format, dpi=300, bbox_inches="tight")
        fig.clear()
        media_types = {
            "png": "image/png",
            "svg": "image/svg+xml",
            "pdf": "application/pdf",
        }
        return Response(content=buffer.getvalue(), media_type=media_types[format])
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/report")
def generate_llm_report(
    run_id: str,
    adapter: AdapterDep,
    model_id: str | None = None,
    language: str | None = Query(None, description="Report language (ko/en)"),
):
    """Generate LLM-based detailed report."""
    try:
        report = adapter.generate_llm_report(run_id, model_id=model_id, language=language)
        return report
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
