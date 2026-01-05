from typing import Any

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
    duration_ms: float
    final_output: dict[str, Any]
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


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_query(request: AnalyzeRequest):
    """Run natural language analysis on evaluation results."""
    try:
        # Initialize service (in a real app, use dependency injection)
        service = AnalysisPipelineService()

        # Register default modules
        from evalvault.adapters.outbound.analysis import (
            AnalysisReportModule,
            CausalAnalyzerModule,
            ComparisonReportModule,
            DataLoaderModule,
            NLPAnalyzerModule,
            StatisticalAnalyzerModule,
            SummaryReportModule,
            VerificationReportModule,
        )

        # We need a proper DB path. Using default for now or env var.
        db_path = "evalvault.db"
        storage = SQLiteStorageAdapter(db_path=db_path)

        service.register_module(DataLoaderModule(storage=storage))
        service.register_module(StatisticalAnalyzerModule())
        service.register_module(NLPAnalyzerModule())
        service.register_module(CausalAnalyzerModule())
        service.register_module(SummaryReportModule())
        service.register_module(AnalysisReportModule())
        service.register_module(VerificationReportModule())
        service.register_module(ComparisonReportModule())

        # Execute pipeline
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

        # Format response
        node_results_summary = {}
        for node_id, node_res in result.node_results.items():
            node_results_summary[node_id] = {
                "status": node_res.status,
                "error": node_res.error,
                # We omit full output to keep response light, unless needed
            }

        return AnalysisResponse(
            intent=result.intent.value if result.intent else "unknown",
            is_complete=result.is_complete,
            duration_ms=result.total_duration_ms,
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
        service = AnalysisPipelineService()

        from evalvault.adapters.outbound.analysis import (
            AnalysisReportModule,
            CausalAnalyzerModule,
            ComparisonReportModule,
            DataLoaderModule,
            NLPAnalyzerModule,
            StatisticalAnalyzerModule,
            SummaryReportModule,
            VerificationReportModule,
        )

        db_path = "evalvault.db"
        storage = SQLiteStorageAdapter(db_path=db_path)

        service.register_module(DataLoaderModule(storage=storage))
        service.register_module(StatisticalAnalyzerModule())
        service.register_module(NLPAnalyzerModule())
        service.register_module(CausalAnalyzerModule())
        service.register_module(SummaryReportModule())
        service.register_module(AnalysisReportModule())
        service.register_module(VerificationReportModule())
        service.register_module(ComparisonReportModule())

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
