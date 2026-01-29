import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from evalvault.adapters.outbound.llm import get_llm_adapter
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import get_settings
from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
from evalvault.domain.metrics.analysis_registry import list_analysis_metric_specs
from evalvault.domain.services.pipeline_orchestrator import AnalysisPipelineService

router = APIRouter(tags=["pipeline"])
logger = logging.getLogger(__name__)

INTENT_CATALOG = {
    AnalysisIntent.VERIFY_MORPHEME: {
        "label": "형태소 검증",
        "category": "verification",
        "description": "형태소 분석/품사 태깅 품질을 점검합니다.",
        "sample_query": "형태소 분석 품질을 검증해줘",
    },
    AnalysisIntent.VERIFY_EMBEDDING: {
        "label": "임베딩 품질 검증",
        "category": "verification",
        "description": "임베딩 분포/품질을 확인합니다.",
        "sample_query": "임베딩 품질과 분포를 확인해줘",
    },
    AnalysisIntent.VERIFY_RETRIEVAL: {
        "label": "검색 품질 검증",
        "category": "verification",
        "description": "검색 컨텍스트 품질을 점검합니다.",
        "sample_query": "검색 품질을 검증해줘",
    },
    AnalysisIntent.COMPARE_SEARCH_METHODS: {
        "label": "검색 방식 비교",
        "category": "comparison",
        "description": "BM25/하이브리드 등 검색 방식을 비교합니다.",
        "sample_query": "BM25와 하이브리드 검색을 비교해줘",
    },
    AnalysisIntent.COMPARE_MODELS: {
        "label": "모델 비교",
        "category": "comparison",
        "description": "모델별 성능 차이를 비교합니다.",
        "sample_query": "모델 성능을 비교해줘",
    },
    AnalysisIntent.COMPARE_RUNS: {
        "label": "실행 결과 비교",
        "category": "comparison",
        "description": "서로 다른 실행 결과를 비교합니다.",
        "sample_query": "이전 실행과 현재 실행을 비교해줘",
    },
    AnalysisIntent.ANALYZE_LOW_METRICS: {
        "label": "낮은 메트릭 원인 분석",
        "category": "analysis",
        "description": "점수가 낮은 메트릭의 원인을 분석합니다.",
        "sample_query": "낮은 메트릭 원인을 분석해줘",
    },
    AnalysisIntent.ANALYZE_PATTERNS: {
        "label": "패턴 분석",
        "category": "analysis",
        "description": "실패/성공 패턴을 분석합니다.",
        "sample_query": "평가 결과 패턴을 분석해줘",
    },
    AnalysisIntent.ANALYZE_TRENDS: {
        "label": "추세 분석",
        "category": "analysis",
        "description": "시간에 따른 추세를 분석합니다.",
        "sample_query": "메트릭 추세를 분석해줘",
    },
    AnalysisIntent.ANALYZE_STATISTICAL: {
        "label": "기술 통계량",
        "category": "analysis",
        "description": "메트릭별 기초 통계량을 계산합니다.",
        "sample_query": "기초 통계 분석해줘",
    },
    AnalysisIntent.ANALYZE_NLP: {
        "label": "NLP 분석",
        "category": "analysis",
        "description": "질문/답변 텍스트를 분석합니다.",
        "sample_query": "텍스트 분석해줘",
    },
    AnalysisIntent.ANALYZE_DATASET_FEATURES: {
        "label": "데이터셋 특성 분석",
        "category": "analysis",
        "description": "질문/답변/컨텍스트 특성을 추출하고 메트릭 상관을 분석합니다.",
        "sample_query": "데이터셋 특성 분석해줘",
    },
    AnalysisIntent.ANALYZE_CAUSAL: {
        "label": "인과 관계 분석",
        "category": "analysis",
        "description": "요인별 영향도와 인과 관계를 분석합니다.",
        "sample_query": "인과 관계 분석해줘",
    },
    AnalysisIntent.ANALYZE_NETWORK: {
        "label": "네트워크 분석",
        "category": "analysis",
        "description": "메트릭 간 상관관계 네트워크를 분석합니다.",
        "sample_query": "메트릭 네트워크 분석해줘",
    },
    AnalysisIntent.ANALYZE_PLAYBOOK: {
        "label": "플레이북 분석",
        "category": "analysis",
        "description": "개선 플레이북 기반 진단을 수행합니다.",
        "sample_query": "플레이북으로 분석해줘",
    },
    AnalysisIntent.DETECT_ANOMALIES: {
        "label": "이상 탐지",
        "category": "timeseries",
        "description": "시계열 이상 패턴을 탐지합니다.",
        "sample_query": "이상 탐지해줘",
    },
    AnalysisIntent.FORECAST_PERFORMANCE: {
        "label": "성능 예측",
        "category": "timeseries",
        "description": "미래 성능을 예측합니다.",
        "sample_query": "성능 예측해줘",
    },
    AnalysisIntent.GENERATE_HYPOTHESES: {
        "label": "가설 생성",
        "category": "generation",
        "description": "성능 저하 원인에 대한 가설을 생성합니다.",
        "sample_query": "가설 생성해줘",
    },
    AnalysisIntent.BENCHMARK_RETRIEVAL: {
        "label": "검색 벤치마크",
        "category": "benchmark",
        "description": "실제 문서 기반 검색 성능을 벤치마크합니다.",
        "sample_query": "검색 벤치마크를 실행해줘",
    },
    AnalysisIntent.GENERATE_SUMMARY: {
        "label": "요약 보고서",
        "category": "report",
        "description": "핵심 지표 요약 보고서를 생성합니다.",
        "sample_query": "평가 요약 보고서를 만들어줘",
    },
    AnalysisIntent.GENERATE_DETAILED: {
        "label": "상세 보고서",
        "category": "report",
        "description": "상세 분석 보고서를 생성합니다.",
        "sample_query": "상세 평가 보고서를 만들어줘",
    },
    AnalysisIntent.GENERATE_COMPARISON: {
        "label": "비교 보고서",
        "category": "report",
        "description": "비교 보고서를 생성합니다.",
        "sample_query": "비교 보고서를 만들어줘",
    },
}


class AnalyzeRequest(BaseModel):
    query: str
    run_id: str | None = None
    intent: str | None = None
    params: dict[str, Any] | None = None


class AnalysisResponse(BaseModel):
    intent: str
    is_complete: bool
    duration_ms: float | None
    pipeline_id: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    final_output: dict[str, Any] | None
    node_results: dict[str, Any]


class PipelineNodeInfo(BaseModel):
    id: str
    name: str
    module: str
    depends_on: list[str]


class IntentCatalogResponse(BaseModel):
    intent: str
    label: str
    category: str
    description: str
    sample_query: str
    available: bool
    missing_modules: list[str]
    nodes: list[PipelineNodeInfo]


class PipelineResultPayload(BaseModel):
    intent: str
    query: str | None = None
    run_id: str | None = None
    pipeline_id: str | None = None
    profile: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    is_complete: bool = True
    duration_ms: float | None = None
    final_output: dict[str, Any] | None = None
    node_results: dict[str, Any] | None = None
    started_at: str | None = None
    finished_at: str | None = None


class PipelineResultSummary(BaseModel):
    result_id: str
    intent: str
    label: str
    query: str | None = None
    run_id: str | None = None
    profile: str | None = None
    tags: list[str] | None = None
    duration_ms: float | None = None
    is_complete: bool
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None


class PipelineResultResponse(PipelineResultSummary):
    pipeline_id: str | None = None
    metadata: dict[str, Any] | None = None
    node_results: dict[str, Any] | None = None
    final_output: dict[str, Any] | None = None


class AnalysisMetricSpecResponse(BaseModel):
    key: str
    label: str
    description: str
    signal_group: str
    module_id: str
    output_path: list[str]


def _serialize_payload(value: Any) -> Any:
    try:
        return jsonable_encoder(value)
    except Exception:
        return {"_error": "serialization_failed", "repr": repr(value)}


def _serialize_node_result(node_res: Any) -> dict[str, Any]:
    status = getattr(node_res, "status", None)
    if hasattr(status, "value"):
        status = status.value
    return {
        "status": status,
        "error": getattr(node_res, "error", None),
        "duration_ms": getattr(node_res, "duration_ms", None),
        "output": _serialize_payload(getattr(node_res, "output", None)),
    }


def _intent_label(intent_value: str) -> str:
    try:
        intent = AnalysisIntent(intent_value)
    except ValueError:
        return intent_value
    meta = INTENT_CATALOG.get(intent)
    return meta["label"] if meta else intent.value


def _build_pipeline_service() -> tuple[AnalysisPipelineService, Any]:
    settings = get_settings()
    storage = build_storage_adapter(settings=settings)
    llm_adapter = None
    try:
        llm_adapter = get_llm_adapter(settings)
    except Exception as exc:
        logger.warning("LLM adapter initialization failed for pipeline: %s", exc)
    from evalvault.adapters.outbound.analysis.pipeline_factory import (
        build_analysis_pipeline_service,
    )

    service = build_analysis_pipeline_service(storage=storage, llm_adapter=llm_adapter)
    return service, storage


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_query(request: AnalyzeRequest):
    """Run natural language analysis on evaluation results."""
    try:
        service, _storage = _build_pipeline_service()
        extra_params = {
            key: value
            for key, value in (request.params or {}).items()
            if key not in {"query", "run_id", "intent"}
        }

        if request.intent:
            try:
                intent = AnalysisIntent(request.intent)
            except ValueError as exc:
                raise HTTPException(
                    status_code=400, detail=f"Unknown intent: {request.intent}"
                ) from exc
            result = await service.analyze_intent_async(
                intent,
                query=request.query,
                run_id=request.run_id,
                **extra_params,
            )
        else:
            result = await service.analyze_async(
                request.query,
                run_id=request.run_id,
                **extra_params,
            )

        node_results_summary = {
            node_id: _serialize_node_result(node_res)
            for node_id, node_res in result.node_results.items()
        }

        return AnalysisResponse(
            intent=result.intent.value if result.intent else "unknown",
            is_complete=result.is_complete,
            duration_ms=result.total_duration_ms,
            pipeline_id=result.pipeline_id,
            started_at=result.started_at.isoformat() if result.started_at else None,
            finished_at=result.finished_at.isoformat() if result.finished_at else None,
            final_output=_serialize_payload(result.final_output),
            node_results=node_results_summary,
        )

    except Exception as e:
        print(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intents", response_model=list[IntentCatalogResponse])
async def list_intents():
    """List available analysis intents and templates."""
    try:
        service, _storage = _build_pipeline_service()
        registered_modules = set(service.get_registered_modules())

        responses: list[IntentCatalogResponse] = []
        for intent in service.get_available_intents():
            meta = INTENT_CATALOG.get(intent)
            label = meta["label"] if meta else intent.value
            category = meta["category"] if meta else "analysis"
            description = meta["description"] if meta else ""
            sample_query = meta["sample_query"] if meta else intent.value

            template = service.get_pipeline_template(intent)
            nodes: list[PipelineNodeInfo] = []
            modules_in_template: list[str] = []
            if template:
                for node in template.nodes:
                    nodes.append(
                        PipelineNodeInfo(
                            id=node.id,
                            name=node.name,
                            module=node.module,
                            depends_on=node.depends_on,
                        )
                    )
                    modules_in_template.append(node.module)
            missing = sorted({m for m in modules_in_template if m not in registered_modules})
            available = len(missing) == 0

            responses.append(
                IntentCatalogResponse(
                    intent=intent.value,
                    label=label,
                    category=category,
                    description=description,
                    sample_query=sample_query,
                    available=available,
                    missing_modules=missing,
                    nodes=nodes,
                )
            )

        return responses
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/options/analysis-metric-specs", response_model=list[AnalysisMetricSpecResponse])
async def list_analysis_metric_specs_endpoint():
    """List analysis metric specs for pipeline outputs."""
    return [spec.to_dict() for spec in list_analysis_metric_specs()]


@router.post("/results", response_model=PipelineResultSummary)
async def save_pipeline_result(payload: PipelineResultPayload):
    """Save a pipeline analysis result for history."""
    try:
        _service, storage = _build_pipeline_service()
        result_id = str(uuid4())
        created_at = datetime.now().isoformat()

        record = payload.model_dump()
        record.update(
            {
                "result_id": result_id,
                "created_at": created_at,
            }
        )
        storage.save_pipeline_result(record)

        return PipelineResultSummary(
            result_id=result_id,
            intent=payload.intent,
            label=_intent_label(payload.intent),
            query=payload.query,
            run_id=payload.run_id,
            profile=payload.profile,
            tags=payload.tags,
            duration_ms=payload.duration_ms,
            is_complete=payload.is_complete,
            created_at=created_at,
            started_at=payload.started_at,
            finished_at=payload.finished_at,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/results", response_model=list[PipelineResultSummary])
async def list_pipeline_results(limit: int = 50):
    """List saved pipeline analysis results."""
    try:
        _service, storage = _build_pipeline_service()
        results = storage.list_pipeline_results(limit=limit)

        return [
            PipelineResultSummary(
                result_id=item["result_id"],
                intent=item["intent"],
                label=_intent_label(item["intent"]),
                query=item.get("query"),
                run_id=item.get("run_id"),
                profile=item.get("profile"),
                tags=item.get("tags"),
                duration_ms=item.get("duration_ms"),
                is_complete=item.get("is_complete", False),
                created_at=item.get("created_at"),
                started_at=item.get("started_at"),
                finished_at=item.get("finished_at"),
            )
            for item in results
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/results/{result_id}", response_model=PipelineResultResponse)
async def get_pipeline_result(result_id: str):
    """Get a saved pipeline analysis result."""
    try:
        _service, storage = _build_pipeline_service()
        item = storage.get_pipeline_result(result_id)
        return PipelineResultResponse(
            result_id=item["result_id"],
            intent=item["intent"],
            label=_intent_label(item["intent"]),
            query=item.get("query"),
            run_id=item.get("run_id"),
            pipeline_id=item.get("pipeline_id"),
            profile=item.get("profile"),
            tags=item.get("tags"),
            duration_ms=item.get("duration_ms"),
            is_complete=item.get("is_complete", False),
            created_at=item.get("created_at"),
            started_at=item.get("started_at"),
            finished_at=item.get("finished_at"),
            node_results=item.get("node_results"),
            final_output=item.get("final_output"),
            metadata=item.get("metadata"),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
