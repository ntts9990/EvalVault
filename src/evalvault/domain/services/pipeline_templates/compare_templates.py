"""``COMPARE_*`` 의도에 대응하는 파이프라인 템플릿 빌더."""

from __future__ import annotations

from evalvault.domain.entities.analysis_pipeline import (
    AnalysisIntent,
    AnalysisNode,
    AnalysisPipeline,
)
from evalvault.domain.services.pipeline_templates import register


def create_compare_search_template() -> AnalysisPipeline:
    """검색 방식 비교 템플릿."""
    nodes = [
        AnalysisNode(
            id="load_data",
            name="데이터 로드",
            module="data_loader",
        ),
        AnalysisNode(
            id="morpheme_analysis",
            name="형태소 분석",
            module="morpheme_analyzer",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="bm25_search",
            name="BM25 검색",
            module="bm25_searcher",
            depends_on=["load_data", "morpheme_analysis"],
        ),
        AnalysisNode(
            id="embedding_search",
            name="임베딩 검색",
            module="embedding_searcher",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="rrf_hybrid",
            name="RRF 하이브리드",
            module="hybrid_rrf",
            depends_on=["bm25_search", "embedding_search"],
        ),
        AnalysisNode(
            id="weighted_hybrid",
            name="가중치 하이브리드",
            module="hybrid_weighted",
            depends_on=["bm25_search", "embedding_search"],
        ),
        AnalysisNode(
            id="comparison",
            name="검색 비교",
            module="search_comparator",
            depends_on=["rrf_hybrid", "weighted_hybrid"],
        ),
        AnalysisNode(
            id="report",
            name="비교 보고서",
            module="comparison_report",
            depends_on=["comparison"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.COMPARE_SEARCH_METHODS,
        nodes=nodes,
    )


def create_compare_models_template() -> AnalysisPipeline:
    """모델 비교 템플릿."""
    nodes = [
        AnalysisNode(
            id="load_runs",
            name="실행 결과 로드",
            module="run_loader",
        ),
        AnalysisNode(
            id="model_analysis",
            name="모델별 분석",
            module="model_analyzer",
            depends_on=["load_runs"],
        ),
        AnalysisNode(
            id="statistical_comparison",
            name="통계 비교",
            module="statistical_comparator",
            depends_on=["model_analysis"],
        ),
        AnalysisNode(
            id="report",
            name="비교 보고서",
            module="comparison_report",
            depends_on=["statistical_comparison"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.COMPARE_MODELS,
        nodes=nodes,
    )


def create_compare_runs_template() -> AnalysisPipeline:
    """실행 비교 템플릿."""
    nodes = [
        AnalysisNode(
            id="load_runs",
            name="실행 결과 로드",
            module="run_loader",
        ),
        AnalysisNode(
            id="run_analysis",
            name="실행 분석",
            module="run_analyzer",
            depends_on=["load_runs"],
        ),
        AnalysisNode(
            id="statistical_comparison",
            name="통계 비교",
            module="statistical_comparator",
            depends_on=["run_analysis"],
        ),
        AnalysisNode(
            id="report",
            name="비교 보고서",
            module="comparison_report",
            depends_on=["statistical_comparison"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.COMPARE_RUNS,
        nodes=nodes,
    )


register(AnalysisIntent.COMPARE_SEARCH_METHODS, create_compare_search_template)
register(AnalysisIntent.COMPARE_MODELS, create_compare_models_template)
register(AnalysisIntent.COMPARE_RUNS, create_compare_runs_template)
