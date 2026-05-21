"""``VERIFY_*`` 의도에 대응하는 파이프라인 템플릿 빌더."""

from __future__ import annotations

from evalvault.domain.entities.analysis_pipeline import (
    AnalysisIntent,
    AnalysisNode,
    AnalysisPipeline,
)
from evalvault.domain.services.pipeline_templates import register


def create_verify_morpheme_template() -> AnalysisPipeline:
    """형태소 검증 템플릿."""
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
            id="quality_check",
            name="형태소 품질 점검",
            module="morpheme_quality_checker",
            depends_on=["morpheme_analysis"],
        ),
        AnalysisNode(
            id="report",
            name="검증 보고서",
            module="verification_report",
            depends_on=["quality_check"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.VERIFY_MORPHEME,
        nodes=nodes,
    )


def create_verify_embedding_template() -> AnalysisPipeline:
    """임베딩 품질 검증 템플릿."""
    nodes = [
        AnalysisNode(
            id="load_data",
            name="데이터 로드",
            module="data_loader",
        ),
        AnalysisNode(
            id="embedding_analysis",
            name="임베딩 분석",
            module="embedding_analyzer",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="quality_check",
            name="임베딩 분포 점검",
            module="embedding_distribution",
            depends_on=["embedding_analysis"],
        ),
        AnalysisNode(
            id="report",
            name="검증 보고서",
            module="verification_report",
            depends_on=["quality_check"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.VERIFY_EMBEDDING,
        nodes=nodes,
    )


def create_verify_retrieval_template() -> AnalysisPipeline:
    """검색 품질 검증 템플릿."""
    nodes = [
        AnalysisNode(
            id="load_data",
            name="데이터 로드",
            module="data_loader",
        ),
        AnalysisNode(
            id="retrieval_analysis",
            name="검색 분석",
            module="retrieval_analyzer",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="quality_check",
            name="검색 품질 점검",
            module="retrieval_quality_checker",
            depends_on=["retrieval_analysis"],
        ),
        AnalysisNode(
            id="report",
            name="검증 보고서",
            module="verification_report",
            depends_on=["quality_check"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.VERIFY_RETRIEVAL,
        nodes=nodes,
    )


register(AnalysisIntent.VERIFY_MORPHEME, create_verify_morpheme_template)
register(AnalysisIntent.VERIFY_EMBEDDING, create_verify_embedding_template)
register(AnalysisIntent.VERIFY_RETRIEVAL, create_verify_retrieval_template)
