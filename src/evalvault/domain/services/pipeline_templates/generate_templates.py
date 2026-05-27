"""``GENERATE_*`` 의도에 대응하는 파이프라인 템플릿 빌더 (보고서/가설)."""

from __future__ import annotations

from evalvault.domain.entities.analysis_pipeline import (
    AnalysisIntent,
    AnalysisNode,
    AnalysisPipeline,
)
from evalvault.domain.services.pipeline_templates import register


def create_generate_hypotheses_template() -> AnalysisPipeline:
    nodes = [
        AnalysisNode(
            id="load_data",
            name="데이터 로드",
            module="data_loader",
        ),
        AnalysisNode(
            id="statistics",
            name="통계 분석",
            module="statistical_analyzer",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="ragas_eval",
            name="RAGAS 평가",
            module="ragas_evaluator",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="low_samples",
            name="낮은 성능 케이스 추출",
            module="low_performer_extractor",
            depends_on=["ragas_eval"],
        ),
        AnalysisNode(
            id="hypothesis",
            name="가설 생성",
            module="hypothesis_generator",
            depends_on=["statistics", "low_samples"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.GENERATE_HYPOTHESES,
        nodes=nodes,
    )


def create_generate_summary_template() -> AnalysisPipeline:
    """요약 보고서 생성 템플릿."""
    nodes = [
        AnalysisNode(
            id="load_data",
            name="데이터 로드",
            module="data_loader",
        ),
        AnalysisNode(
            id="statistics",
            name="통계 분석",
            module="statistical_analyzer",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="retrieval_analysis",
            name="검색 분석",
            module="retrieval_analyzer",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="priority_summary",
            name="우선순위 요약",
            module="priority_summary",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="report",
            name="LLM 요약 보고서",
            module="llm_report",
            params={"report_type": "summary"},
            depends_on=["load_data", "statistics", "retrieval_analysis"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.GENERATE_SUMMARY,
        nodes=nodes,
    )


def create_generate_detailed_template() -> AnalysisPipeline:
    """상세 보고서 생성 템플릿."""
    nodes = [
        AnalysisNode(
            id="load_data",
            name="데이터 로드",
            module="data_loader",
            params={"allow_sample": False},
        ),
        AnalysisNode(
            id="statistics",
            name="통계 분석",
            module="statistical_analyzer",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="ragas_eval",
            name="RAGAS 요약",
            module="ragas_evaluator",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="retrieval_analysis",
            name="검색 분석",
            module="retrieval_analyzer",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="low_samples",
            name="낮은 성능 케이스 추출",
            module="low_performer_extractor",
            depends_on=["ragas_eval"],
        ),
        AnalysisNode(
            id="diagnostic",
            name="진단 분석",
            module="diagnostic_playbook",
            depends_on=["load_data", "ragas_eval"],
        ),
        AnalysisNode(
            id="multiturn",
            name="멀티턴 분석",
            module="multiturn_analyzer",
            depends_on=["load_data", "ragas_eval"],
        ),
        AnalysisNode(
            id="nlp_analysis",
            name="NLP 분석",
            module="nlp_analyzer",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="pattern_detection",
            name="패턴 분석",
            module="pattern_detector",
            depends_on=["nlp_analysis"],
        ),
        AnalysisNode(
            id="causal_analysis",
            name="인과 분석",
            module="causal_analyzer",
            depends_on=["load_data", "statistics"],
        ),
        AnalysisNode(
            id="root_cause",
            name="근본 원인 분석",
            module="root_cause_analyzer",
            depends_on=["low_samples", "diagnostic", "causal_analysis"],
        ),
        AnalysisNode(
            id="priority_summary",
            name="우선순위 요약",
            module="priority_summary",
            depends_on=["load_data", "ragas_eval"],
        ),
        AnalysisNode(
            id="load_runs",
            name="실행 이력 로드",
            module="run_loader",
            params={"limit": 5, "allow_sample": False},
        ),
        AnalysisNode(
            id="time_series",
            name="시계열 요약",
            module="time_series_analyzer",
            depends_on=["load_runs"],
        ),
        AnalysisNode(
            id="trend_detection",
            name="추세 감지",
            module="trend_detector",
            depends_on=["time_series"],
        ),
        AnalysisNode(
            id="report",
            name="LLM 상세 보고서",
            module="llm_report",
            params={"report_type": "analysis"},
            depends_on=[
                "load_data",
                "statistics",
                "ragas_eval",
                "retrieval_analysis",
                "nlp_analysis",
                "pattern_detection",
                "causal_analysis",
                "root_cause",
                "priority_summary",
                "multiturn",
                "trend_detection",
            ],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.GENERATE_DETAILED,
        nodes=nodes,
    )


def create_generate_comparison_template() -> AnalysisPipeline:
    """비교 보고서 생성 템플릿."""
    nodes = [
        AnalysisNode(
            id="load_runs",
            name="실행 결과 로드",
            module="run_loader",
            params={"limit": 2, "allow_sample": False},
        ),
        AnalysisNode(
            id="run_metric_comparison",
            name="메트릭 통계 비교",
            module="run_metric_comparator",
            depends_on=["load_runs"],
        ),
        AnalysisNode(
            id="run_change_detection",
            name="변경 사항 탐지",
            module="run_change_detector",
            depends_on=["load_runs"],
        ),
        AnalysisNode(
            id="report",
            name="LLM 비교 보고서",
            module="llm_report",
            params={"report_type": "comparison"},
            depends_on=["load_runs", "run_metric_comparison", "run_change_detection"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.GENERATE_COMPARISON,
        nodes=nodes,
    )


register(AnalysisIntent.GENERATE_HYPOTHESES, create_generate_hypotheses_template)
register(AnalysisIntent.GENERATE_SUMMARY, create_generate_summary_template)
register(AnalysisIntent.GENERATE_DETAILED, create_generate_detailed_template)
register(AnalysisIntent.GENERATE_COMPARISON, create_generate_comparison_template)
