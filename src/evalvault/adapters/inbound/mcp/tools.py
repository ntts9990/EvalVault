from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from evalvault.adapters.inbound.api.adapter import WebUIAdapter
from evalvault.adapters.inbound.cli.utils.analysis_io import (
    extract_markdown_report,
    resolve_artifact_dir,
    resolve_output_paths,
    serialize_pipeline_result,
    write_json,
    write_pipeline_artifacts,
)
from evalvault.adapters.outbound.analysis.pipeline_factory import build_analysis_pipeline_service
from evalvault.adapters.outbound.analysis.statistical_adapter import StatisticalAnalysisAdapter
from evalvault.adapters.outbound.llm import SettingsLLMFactory, get_llm_adapter
from evalvault.adapters.outbound.nlp.korean.toolkit_factory import try_create_korean_toolkit
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
from evalvault.domain.services.analysis_service import AnalysisService
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.ports.inbound.web_port import EvalRequest, RunFilters, RunSummary
from evalvault.ports.outbound.storage_port import StoragePort

from .schemas import (
    AnalyzeCompareRequest,
    AnalyzeCompareResponse,
    ArtifactsKind,
    ArtifactsPayload,
    ComparisonArtifactsPayload,
    ErrorStage,
    EvaluationArtifactsPayload,
    GetArtifactsRequest,
    GetArtifactsResponse,
    GetRunSummaryRequest,
    GetRunSummaryResponse,
    ListRunsRequest,
    ListRunsResponse,
    McpError,
    MetricsDeltaPayload,
    RunEvaluationRequest,
    RunEvaluationResponse,
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

    storage = build_storage_adapter(settings=Settings(), db_path=db_path)
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

    storage = build_storage_adapter(settings=Settings(), db_path=db_path)
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


def run_evaluation(payload: dict[str, Any] | RunEvaluationRequest) -> RunEvaluationResponse:
    try:
        request = RunEvaluationRequest.model_validate(payload)
    except ValidationError as exc:
        return RunEvaluationResponse(run_id="", errors=[_validation_error(exc)])

    try:
        dataset_path = _resolve_dataset_path(request.dataset_path)
    except ValueError as exc:
        return RunEvaluationResponse(
            run_id="",
            errors=[_error("EVAL_DATASET_UNSAFE_PATH", str(exc), stage=ErrorStage.preprocess)],
        )

    try:
        db_path = _resolve_db_path(request.db_path)
    except ValueError as exc:
        return RunEvaluationResponse(
            run_id="",
            errors=[_error("EVAL_DB_UNSAFE_PATH", str(exc), stage=ErrorStage.storage)],
        )

    settings = Settings()
    if request.profile:
        settings = apply_profile(settings, request.profile)

    model_name = request.model_name or _default_model_name(settings)

    try:
        llm_adapter = get_llm_adapter(settings)
    except Exception as exc:
        return RunEvaluationResponse(
            run_id="",
            errors=[_error("EVAL_LLM_INIT_FAILED", str(exc), stage=ErrorStage.evaluate)],
        )

    storage = build_storage_adapter(settings=Settings(), db_path=db_path)
    llm_factory = SettingsLLMFactory(settings)
    korean_toolkit = try_create_korean_toolkit()
    evaluator = RagasEvaluator(korean_toolkit=korean_toolkit, llm_factory=llm_factory)
    adapter = WebUIAdapter(
        storage=storage,
        evaluator=evaluator,
        llm_adapter=llm_adapter,
        settings=settings,
    )

    eval_request = EvalRequest(
        dataset_path=str(dataset_path),
        metrics=request.metrics,
        model_name=model_name,
        evaluation_task=request.evaluation_task or "qa",
        thresholds=request.thresholds or {},
        threshold_profile=request.threshold_profile,
        parallel=request.parallel,
        batch_size=request.batch_size,
    )

    try:
        result = asyncio.run(adapter.run_evaluation(eval_request))
    except Exception as exc:
        return RunEvaluationResponse(
            run_id="",
            errors=[_error("EVAL_RUN_FAILED", str(exc), stage=ErrorStage.evaluate)],
        )

    metrics_summary = {metric: result.get_avg_score(metric) for metric in result.metrics_evaluated}
    artifacts_payload = None

    if request.auto_analyze:
        try:
            analysis_payload = _run_auto_analysis(
                run_id=result.run_id,
                run=result,
                storage=storage,
                llm_adapter=llm_adapter,
                analysis_output=request.analysis_output,
                analysis_report=request.analysis_report,
                analysis_dir=request.analysis_dir,
            )
            artifacts_payload = analysis_payload
        except Exception as exc:
            return RunEvaluationResponse(
                run_id=result.run_id,
                metrics=metrics_summary,
                thresholds=result.thresholds,
                errors=[_error("EVAL_AUTO_ANALYZE_FAILED", str(exc), stage=ErrorStage.analyze)],
            )

    return RunEvaluationResponse(
        run_id=result.run_id,
        metrics=metrics_summary,
        thresholds=result.thresholds,
        artifacts=artifacts_payload,
        errors=[],
    )


def analyze_compare(payload: dict[str, Any] | AnalyzeCompareRequest) -> AnalyzeCompareResponse:
    try:
        request = AnalyzeCompareRequest.model_validate(payload)
    except ValidationError as exc:
        return AnalyzeCompareResponse(
            baseline_run_id="",
            candidate_run_id="",
            errors=[_validation_error(exc)],
        )

    try:
        _validate_run_id(request.run_id_a)
        _validate_run_id(request.run_id_b)
    except ValueError as exc:
        return AnalyzeCompareResponse(
            baseline_run_id=request.run_id_a,
            candidate_run_id=request.run_id_b,
            errors=[_error("EVAL_INVALID_RUN_ID", str(exc), stage=ErrorStage.compare)],
        )

    try:
        db_path = _resolve_db_path(request.db_path)
    except ValueError as exc:
        return AnalyzeCompareResponse(
            baseline_run_id=request.run_id_a,
            candidate_run_id=request.run_id_b,
            errors=[_error("EVAL_DB_UNSAFE_PATH", str(exc), stage=ErrorStage.storage)],
        )

    storage = build_storage_adapter(settings=Settings(), db_path=db_path)
    try:
        run_a = storage.get_run(request.run_id_a)
        run_b = storage.get_run(request.run_id_b)
    except KeyError as exc:
        return AnalyzeCompareResponse(
            baseline_run_id=request.run_id_a,
            candidate_run_id=request.run_id_b,
            errors=[_error("EVAL_RUN_NOT_FOUND", str(exc), stage=ErrorStage.storage)],
        )
    except Exception as exc:
        return AnalyzeCompareResponse(
            baseline_run_id=request.run_id_a,
            candidate_run_id=request.run_id_b,
            errors=[_error("EVAL_RUN_LOAD_FAILED", str(exc), stage=ErrorStage.storage)],
        )

    analysis_adapter = StatisticalAnalysisAdapter()
    service = AnalysisService(analysis_adapter)
    comparisons = service.compare_runs(
        run_a,
        run_b,
        metrics=request.metrics,
        test_type=request.test_type,
    )

    if not comparisons:
        return AnalyzeCompareResponse(
            baseline_run_id=request.run_id_a,
            candidate_run_id=request.run_id_b,
            errors=[
                _error(
                    "EVAL_COMPARE_NO_COMMON_METRICS",
                    "공통 메트릭이 없어 비교 결과를 생성할 수 없습니다.",
                    stage=ErrorStage.compare,
                )
            ],
        )

    try:
        output_dir = _resolve_reports_dir(request.output_dir)
    except ValueError as exc:
        return AnalyzeCompareResponse(
            baseline_run_id=request.run_id_a,
            candidate_run_id=request.run_id_b,
            errors=[_error("EVAL_REPORT_UNSAFE_PATH", str(exc), stage=ErrorStage.compare)],
        )

    comparison_prefix = f"comparison_{request.run_id_a[:8]}_{request.run_id_b[:8]}"
    output_path, report_path = resolve_output_paths(
        base_dir=output_dir,
        output_path=request.output,
        report_path=request.report,
        prefix=comparison_prefix,
    )
    _ensure_allowed_path(output_path.resolve())
    _ensure_allowed_path(report_path.resolve())

    settings = Settings()
    if request.profile:
        settings = apply_profile(settings, request.profile)

    llm_adapter = None
    try:
        llm_adapter = get_llm_adapter(settings)
    except Exception:
        llm_adapter = None

    pipeline_service = build_analysis_pipeline_service(storage=storage, llm_adapter=llm_adapter)
    pipeline_result = pipeline_service.analyze_intent(
        AnalysisIntent.GENERATE_COMPARISON,
        run_id=request.run_id_a,
        run_ids=[request.run_id_a, request.run_id_b],
        compare_metrics=request.metrics,
        test_type=request.test_type,
        report_type="comparison",
        use_llm_report=True,
    )

    artifacts_dir = resolve_artifact_dir(
        base_dir=output_dir,
        output_path=output_path,
        report_path=report_path,
        prefix=comparison_prefix,
    )
    _ensure_allowed_path(artifacts_dir.resolve())
    artifact_index = write_pipeline_artifacts(pipeline_result, artifacts_dir=artifacts_dir)

    payload = serialize_pipeline_result(pipeline_result)
    payload["run_ids"] = [request.run_id_a, request.run_id_b]
    payload["artifacts"] = artifact_index
    write_json(output_path, payload)

    report_text = extract_markdown_report(pipeline_result.final_output)
    if not report_text:
        report_text = "# 비교 분석 보고서\n\n보고서 본문을 찾지 못했습니다.\n"
    report_path.write_text(report_text, encoding="utf-8")

    delta_by_metric = {comparison.metric: comparison.diff for comparison in comparisons}
    notes = [
        f"{comparison.metric}: {comparison.winner} 우세 ({comparison.diff:+.4f})"
        for comparison in comparisons
        if comparison.is_significant and comparison.winner
    ]
    metrics_delta = MetricsDeltaPayload(
        avg=delta_by_metric,
        by_metric=delta_by_metric,
        notes=notes or None,
    )

    artifacts_payload = ComparisonArtifactsPayload(
        json_path=str(output_path),
        report_path=str(report_path),
        artifacts_dir=artifact_index.get("dir"),
        artifacts_index_path=artifact_index.get("index"),
    )

    return AnalyzeCompareResponse(
        baseline_run_id=request.run_id_a,
        candidate_run_id=request.run_id_b,
        comparison_report_path=str(report_path),
        metrics_delta=metrics_delta,
        artifacts=artifacts_payload,
        errors=[],
    )


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


def _resolve_db_path(db_path: Path | None) -> Path | None:
    settings = Settings()
    if db_path is None:
        if getattr(settings, "db_backend", "postgres") != "sqlite":
            return None
        db_path = Path(settings.evalvault_db_path)
    resolved = db_path.expanduser().resolve()
    _ensure_allowed_path(resolved)
    return resolved


def _resolve_dataset_path(dataset_path: Path) -> Path:
    resolved = dataset_path.expanduser().resolve()
    _ensure_allowed_path(resolved)
    if not resolved.exists():
        raise ValueError("dataset_path가 존재하지 않습니다.")
    return resolved


def _resolve_reports_dir(output_dir: Path | None) -> Path:
    resolved = (output_dir or Path("reports") / "comparison").expanduser().resolve()
    _ensure_allowed_path(resolved)
    return resolved


def _resolve_analysis_dir(analysis_dir: Path | None) -> Path:
    resolved = (analysis_dir or Path("reports") / "analysis").expanduser().resolve()
    _ensure_allowed_path(resolved)
    return resolved


def _default_model_name(settings: Settings) -> str:
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        return f"ollama/{settings.ollama_model}"
    if provider == "vllm":
        return f"vllm/{settings.vllm_model}"
    if provider == "openai":
        return f"openai/{settings.openai_model}"
    return f"{provider}/{settings.openai_model}"


def _run_auto_analysis(
    *,
    run_id: str,
    run: Any,
    storage: StoragePort,
    llm_adapter: Any,
    analysis_output: Path | None,
    analysis_report: Path | None,
    analysis_dir: Path | None,
) -> EvaluationArtifactsPayload:
    analysis_prefix = f"analysis_{run_id}"
    base_dir = _resolve_analysis_dir(analysis_dir)
    output_path, report_path = resolve_output_paths(
        base_dir=base_dir,
        output_path=analysis_output,
        report_path=analysis_report,
        prefix=analysis_prefix,
    )
    _ensure_allowed_path(output_path.resolve())
    _ensure_allowed_path(report_path.resolve())

    pipeline_service = build_analysis_pipeline_service(storage=storage, llm_adapter=llm_adapter)
    pipeline_result = pipeline_service.analyze_intent(
        AnalysisIntent.GENERATE_DETAILED,
        run_id=run_id,
        evaluation_run=run,
        report_type="analysis",
        use_llm_report=True,
    )

    artifacts_dir = resolve_artifact_dir(
        base_dir=base_dir,
        output_path=output_path,
        report_path=report_path,
        prefix=analysis_prefix,
    )
    _ensure_allowed_path(artifacts_dir.resolve())
    artifact_index = write_pipeline_artifacts(pipeline_result, artifacts_dir=artifacts_dir)

    payload = serialize_pipeline_result(pipeline_result)
    payload["run_id"] = run_id
    payload["artifacts"] = artifact_index
    write_json(output_path, payload)

    report_text = extract_markdown_report(pipeline_result.final_output)
    if not report_text:
        report_text = "# 자동 분석 보고서\n\n보고서 본문을 찾지 못했습니다.\n"
    report_path.write_text(report_text, encoding="utf-8")

    return EvaluationArtifactsPayload(
        analysis_report_path=str(report_path),
        analysis_output_path=str(output_path),
        analysis_artifacts_dir=artifact_index.get("dir"),
        analysis_artifacts_index_path=artifact_index.get("index"),
    )


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
        name="run_evaluation",
        description="데이터셋 평가를 실행합니다.",
        input_schema=RunEvaluationRequest.model_json_schema(),
        output_schema=RunEvaluationResponse.model_json_schema(),
    ),
    ToolSpec(
        name="analyze_compare",
        description="두 실행을 비교 분석합니다.",
        input_schema=AnalyzeCompareRequest.model_json_schema(),
        output_schema=AnalyzeCompareResponse.model_json_schema(),
    ),
    ToolSpec(
        name="get_artifacts",
        description="분석/비교 결과 아티팩트 경로를 조회합니다.",
        input_schema=GetArtifactsRequest.model_json_schema(),
        output_schema=GetArtifactsResponse.model_json_schema(),
    ),
)
