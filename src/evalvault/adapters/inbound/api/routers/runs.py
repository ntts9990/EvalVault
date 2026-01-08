"""API Router for Evaluation Runs."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from evalvault.adapters.inbound.api.main import AdapterDep
from evalvault.adapters.outbound.dataset.templates import (
    render_dataset_template_csv,
    render_dataset_template_json,
    render_dataset_template_xlsx,
)
from evalvault.adapters.outbound.domain_memory.sqlite_adapter import SQLiteDomainMemoryAdapter
from evalvault.config.settings import get_settings
from evalvault.domain.entities import EvaluationRun
from evalvault.domain.services.domain_learning_hook import DomainLearningHook
from evalvault.domain.services.ragas_prompt_overrides import (
    PromptOverrideError,
    normalize_ragas_prompt_overrides,
)
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


def _serialize_run_details(run: EvaluationRun) -> dict[str, Any]:
    payload = {
        "summary": run.to_summary_dict(),
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
            }
            for result in run.results
        ],
    }
    prompt_set_detail = (run.tracker_metadata or {}).get("prompt_set_detail")
    if prompt_set_detail:
        payload["prompt_set"] = prompt_set_detail
    return payload


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

    return {
        "base": _serialize_run_details(base_run),
        "target": _serialize_run_details(target_run),
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
                    settings = get_settings()
                    memory_db = memory_config.get("db_path") or settings.evalvault_memory_db_path
                    domain = memory_config.get("domain") or "default"
                    language = memory_config.get("language") or "ko"
                    memory_adapter = SQLiteDomainMemoryAdapter(memory_db)
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
        }
        for s in summaries
    ]


@router.get("/{run_id}", response_model=None)
def get_run_details(run_id: str, adapter: AdapterDep) -> dict[str, Any]:
    """Get detailed information for a specific run."""
    try:
        run: EvaluationRun = adapter.get_run_details(run_id)
        return _serialize_run_details(run)
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


@router.get("/{run_id}/report")
def generate_llm_report(
    run_id: str,
    adapter: AdapterDep,
    model_id: str | None = None,
):
    """Generate LLM-based detailed report."""
    try:
        report = adapter.generate_llm_report(run_id, model_id=model_id)
        return report
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
