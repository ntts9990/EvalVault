from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from evalvault.adapters.inbound.api.adapter import WebUIAdapter
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.config.settings import Settings
from evalvault.ports.inbound.web_port import RunFilters, RunSummary

from .schemas import (
    ArtifactsKind,
    ArtifactsPayload,
    ErrorStage,
    GetArtifactsRequest,
    GetArtifactsResponse,
    GetRunSummaryRequest,
    GetRunSummaryResponse,
    ListRunsRequest,
    ListRunsResponse,
    McpError,
    RunSummaryPayload,
)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
            "outputSchema": self.output_schema,
        }


def get_tool_specs() -> list[dict[str, Any]]:
    return [spec.to_dict() for spec in TOOL_SPECS]


def list_runs(payload: dict[str, Any] | ListRunsRequest) -> ListRunsResponse:
    try:
        request = ListRunsRequest.model_validate(payload)
    except ValidationError as exc:
        return ListRunsResponse(errors=[_validation_error(exc)])

    try:
        db_path = _resolve_db_path(request.db_path)
    except ValueError as exc:
        return ListRunsResponse(
            errors=[_error("EVAL_DB_UNSAFE_PATH", str(exc), stage=ErrorStage.storage)]
        )

    storage = SQLiteStorageAdapter(db_path=db_path)
    adapter = WebUIAdapter(storage=storage, settings=Settings())

    filters = RunFilters(
        dataset_name=request.dataset_name,
        model_name=request.model_name,
        run_mode=request.run_mode,
        project_names=request.project_names or [],
    )

    try:
        summaries = adapter.list_runs(limit=request.limit, filters=filters)
    except Exception as exc:
        return ListRunsResponse(errors=[_error("EVAL_LIST_RUNS_FAILED", str(exc))])

    return ListRunsResponse(
        runs=[_serialize_run_summary(summary) for summary in summaries],
        errors=[],
    )


def get_run_summary(payload: dict[str, Any] | GetRunSummaryRequest) -> GetRunSummaryResponse:
    try:
        request = GetRunSummaryRequest.model_validate(payload)
    except ValidationError as exc:
        return GetRunSummaryResponse(errors=[_validation_error(exc)])

    try:
        _validate_run_id(request.run_id)
    except ValueError as exc:
        return GetRunSummaryResponse(
            errors=[_error("EVAL_INVALID_RUN_ID", str(exc), stage=ErrorStage.storage)]
        )

    try:
        db_path = _resolve_db_path(request.db_path)
    except ValueError as exc:
        return GetRunSummaryResponse(
            errors=[_error("EVAL_DB_UNSAFE_PATH", str(exc), stage=ErrorStage.storage)]
        )

    storage = SQLiteStorageAdapter(db_path=db_path)
    try:
        run = storage.get_run(request.run_id)
    except KeyError as exc:
        return GetRunSummaryResponse(
            errors=[_error("EVAL_RUN_NOT_FOUND", str(exc), stage=ErrorStage.storage)]
        )
    except Exception as exc:
        return GetRunSummaryResponse(
            errors=[_error("EVAL_RUN_LOAD_FAILED", str(exc), stage=ErrorStage.storage)]
        )

    summary_payload = RunSummaryPayload.model_validate(run.to_summary_dict())
    return GetRunSummaryResponse(summary=summary_payload, errors=[])


def get_artifacts(payload: Any) -> GetArtifactsResponse:
    try:
        request = GetArtifactsRequest.model_validate(payload)
    except ValidationError as exc:
        return GetArtifactsResponse(run_id="", errors=[_validation_error(exc)])

    try:
        _validate_run_id(request.run_id)
        if request.comparison_run_id:
            _validate_run_id(request.comparison_run_id)
    except ValueError as exc:
        return GetArtifactsResponse(
            run_id=request.run_id,
            errors=[_error("EVAL_INVALID_RUN_ID", str(exc), stage=_stage_for_kind(request.kind))],
        )

    try:
        base_dir = _resolve_artifact_base_dir(request.base_dir, request.kind)
    except ValueError as exc:
        return GetArtifactsResponse(
            run_id=request.run_id,
            errors=[
                _error("EVAL_ARTIFACT_UNSAFE_PATH", str(exc), stage=_stage_for_kind(request.kind))
            ],
        )

    if request.kind == ArtifactsKind.comparison:
        if not request.comparison_run_id:
            return GetArtifactsResponse(
                run_id=request.run_id,
                errors=[
                    _error(
                        "EVAL_COMPARISON_ID_REQUIRED",
                        "comparison_run_id가 필요합니다.",
                        stage=ErrorStage.compare,
                    )
                ],
            )
        prefix = f"comparison_{request.run_id[:8]}_{request.comparison_run_id[:8]}"
        stage = ErrorStage.compare
    else:
        prefix = f"analysis_{request.run_id}"
        stage = ErrorStage.analyze

    report_path = base_dir / f"{prefix}.md"
    output_path = base_dir / f"{prefix}.json"
    artifacts_dir = base_dir / "artifacts" / prefix
    index_path = artifacts_dir / "index.json"

    artifact_info: ArtifactsPayload = ArtifactsPayload(
        kind=request.kind.value,
        report_path=_existing_path(report_path),
        output_path=_existing_path(output_path),
        artifacts_dir=_existing_dir(artifacts_dir),
        artifacts_index_path=_existing_path(index_path),
    )

    errors: list[McpError] = []
    missing = [
        name
        for name, value in {
            "report": artifact_info.report_path,
            "output": artifact_info.output_path,
            "artifacts_dir": artifact_info.artifacts_dir,
            "artifacts_index": artifact_info.artifacts_index_path,
        }.items()
        if value is None
    ]
    if missing:
        errors.append(
            _error(
                "EVAL_ARTIFACT_NOT_FOUND",
                "아티팩트 일부가 존재하지 않습니다.",
                details={"missing": missing},
                stage=stage,
            )
        )

    return GetArtifactsResponse(
        run_id=request.run_id,
        artifacts=artifact_info,
        errors=errors,
    )


def _serialize_run_summary(summary: RunSummary) -> RunSummaryPayload:
    payload = {
        "run_id": summary.run_id,
        "dataset_name": summary.dataset_name,
        "model_name": summary.model_name,
        "pass_rate": summary.pass_rate,
        "total_test_cases": summary.total_test_cases,
        "passed_test_cases": summary.passed_test_cases,
        "started_at": summary.started_at.isoformat(),
        "finished_at": summary.finished_at.isoformat() if summary.finished_at else None,
        "metrics_evaluated": list(summary.metrics_evaluated),
        "threshold_profile": summary.threshold_profile,
        "run_mode": summary.run_mode,
        "evaluation_task": summary.evaluation_task,
        "project_name": summary.project_name,
        "avg_metric_scores": summary.avg_metric_scores or None,
        "total_cost_usd": summary.total_cost_usd,
        "phoenix_precision": summary.phoenix_precision,
        "phoenix_drift": summary.phoenix_drift,
        "phoenix_experiment_url": summary.phoenix_experiment_url,
        "thresholds": None,
    }
    return RunSummaryPayload.model_validate(payload)


def _resolve_db_path(db_path: Path | None) -> Path:
    if db_path is None:
        settings = Settings()
        db_path = Path(settings.evalvault_db_path)
    resolved = db_path.expanduser().resolve()
    _ensure_allowed_path(resolved)
    return resolved


def _resolve_artifact_base_dir(base_dir: Path | None, kind: ArtifactsKind) -> Path:
    if base_dir is None:
        base_dir = Path("reports") / (
            "comparison" if kind == ArtifactsKind.comparison else "analysis"
        )
    resolved = base_dir.expanduser().resolve()
    _ensure_allowed_path(resolved)
    return resolved


def _ensure_allowed_path(path: Path) -> None:
    allowed_roots = _allowed_roots()
    if not any(path.is_relative_to(root) for root in allowed_roots):
        raise ValueError("허용된 경로(data/, tests/fixtures/, reports/) 밖은 접근할 수 없습니다.")


def _allowed_roots() -> list[Path]:
    repo_root = _find_repo_root()
    base = repo_root if repo_root is not None else Path.cwd()
    return [
        (base / "data").resolve(),
        (base / "tests" / "fixtures").resolve(),
        (base / "reports").resolve(),
    ]


def _find_repo_root() -> Path | None:
    current = Path.cwd().resolve()
    for _ in range(6):
        if (current / "pyproject.toml").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return None


def _validation_error(exc: ValidationError) -> McpError:
    return _error(
        "EVAL_INVALID_PARAMS",
        "입력 스키마가 올바르지 않습니다.",
        details={"errors": exc.errors()},
    )


def _validate_run_id(run_id: str) -> None:
    if not run_id or Path(run_id).name != run_id or "/" in run_id or "\\" in run_id:
        raise ValueError("run_id 형식이 올바르지 않습니다.")


def _existing_path(path: Path) -> str | None:
    return str(path) if path.exists() else None


def _existing_dir(path: Path) -> str | None:
    return str(path) if path.exists() and path.is_dir() else None


def _stage_for_kind(kind: ArtifactsKind) -> ErrorStage:
    return ErrorStage.compare if kind == ArtifactsKind.comparison else ErrorStage.analyze


def _error(
    code: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    retryable: bool = False,
    stage: ErrorStage | None = None,
) -> McpError:
    return McpError(
        code=code,
        message=message,
        details=details,
        retryable=retryable,
        stage=stage,
    )


TOOL_SPECS = (
    ToolSpec(
        name="list_runs",
        description="평가 실행 목록을 조회합니다.",
        input_schema=ListRunsRequest.model_json_schema(),
        output_schema=ListRunsResponse.model_json_schema(),
    ),
    ToolSpec(
        name="get_run_summary",
        description="평가 실행 요약 정보를 조회합니다.",
        input_schema=GetRunSummaryRequest.model_json_schema(),
        output_schema=GetRunSummaryResponse.model_json_schema(),
    ),
    ToolSpec(
        name="get_artifacts",
        description="분석/비교 결과 아티팩트 경로를 조회합니다.",
        input_schema=GetArtifactsRequest.model_json_schema(),
        output_schema=GetArtifactsResponse.model_json_schema(),
    ),
)
