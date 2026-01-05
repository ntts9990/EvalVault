from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
from evalvault.domain.services.pipeline_orchestrator import AnalysisPipelineService

router = APIRouter(tags=["pipeline"])

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


def _intent_label(intent_value: str) -> str:
    try:
        intent = AnalysisIntent(intent_value)
    except ValueError:
        return intent_value
    meta = INTENT_CATALOG.get(intent)
    return meta["label"] if meta else intent.value


def _build_pipeline_service() -> tuple[AnalysisPipelineService, SQLiteStorageAdapter]:
    service = AnalysisPipelineService()
    db_path = "evalvault.db"
    storage = SQLiteStorageAdapter(db_path=db_path)

    from evalvault.adapters.outbound.analysis import (
        AnalysisReportModule,
        BM25SearcherModule,
        CausalAnalyzerModule,
        ComparisonReportModule,
        DataLoaderModule,
        DetailedReportModule,
        DiagnosticPlaybookModule,
        EmbeddingAnalyzerModule,
        EmbeddingDistributionModule,
        EmbeddingSearcherModule,
        HybridRRFModule,
        HybridWeightedModule,
        LowPerformerExtractorModule,
        ModelAnalyzerModule,
        MorphemeAnalyzerModule,
        MorphemeQualityCheckerModule,
        NLPAnalyzerModule,
        PatternDetectorModule,
        RagasEvaluatorModule,
        RetrievalAnalyzerModule,
        RetrievalQualityCheckerModule,
        RootCauseAnalyzerModule,
        RunAnalyzerModule,
        RunComparatorModule,
        RunLoaderModule,
        SearchComparatorModule,
        StatisticalAnalyzerModule,
        StatisticalComparatorModule,
        SummaryReportModule,
        TimeSeriesAnalyzerModule,
        TrendDetectorModule,
        VerificationReportModule,
    )

    service.register_module(DataLoaderModule(storage=storage))
    service.register_module(RunLoaderModule(storage=storage))
    service.register_module(StatisticalAnalyzerModule())
    service.register_module(NLPAnalyzerModule())
    service.register_module(CausalAnalyzerModule())
    service.register_module(SummaryReportModule())
    service.register_module(DetailedReportModule())
    service.register_module(AnalysisReportModule())
    service.register_module(VerificationReportModule())
    service.register_module(ComparisonReportModule())

    service.register_module(MorphemeAnalyzerModule())
    service.register_module(MorphemeQualityCheckerModule())
    service.register_module(EmbeddingAnalyzerModule())
    service.register_module(EmbeddingDistributionModule())
    service.register_module(RetrievalAnalyzerModule())
    service.register_module(RetrievalQualityCheckerModule())
    service.register_module(BM25SearcherModule())
    service.register_module(EmbeddingSearcherModule())
    service.register_module(HybridRRFModule())
    service.register_module(HybridWeightedModule())
    service.register_module(SearchComparatorModule())
    service.register_module(ModelAnalyzerModule())
    service.register_module(RunAnalyzerModule())
    service.register_module(StatisticalComparatorModule())
    service.register_module(RunComparatorModule())
    service.register_module(RagasEvaluatorModule())
    service.register_module(LowPerformerExtractorModule())
    service.register_module(DiagnosticPlaybookModule())
    service.register_module(RootCauseAnalyzerModule())
    service.register_module(PatternDetectorModule())
    service.register_module(TimeSeriesAnalyzerModule())
    service.register_module(TrendDetectorModule())

    return service, storage


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_query(request: AnalyzeRequest):
    """Run natural language analysis on evaluation results."""
    try:
        service, _storage = _build_pipeline_service()

        if request.intent:
            try:
                intent = AnalysisIntent(request.intent)
            except ValueError as exc:
                raise HTTPException(
                    status_code=400, detail=f"Unknown intent: {request.intent}"
                ) from exc
            result = service.analyze_intent(
                intent,
                query=request.query,
                run_id=request.run_id,
            )
        else:
            result = service.analyze(request.query, run_id=request.run_id)

        node_results_summary = {}
        for node_id, node_res in result.node_results.items():
            node_results_summary[node_id] = {
                "status": node_res.status,
                "error": node_res.error,
                "duration_ms": node_res.duration_ms,
            }

        return AnalysisResponse(
            intent=result.intent.value if result.intent else "unknown",
            is_complete=result.is_complete,
            duration_ms=result.total_duration_ms,
            pipeline_id=result.pipeline_id,
            started_at=result.started_at.isoformat() if result.started_at else None,
            finished_at=result.finished_at.isoformat() if result.finished_at else None,
            final_output=result.final_output,
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
