"""``ANALYZE_*`` 의도에 대응하는 파이프라인 템플릿 빌더."""

from __future__ import annotations

from evalvault.domain.entities.analysis_pipeline import (
    AnalysisIntent,
    AnalysisNode,
    AnalysisPipeline,
)
from evalvault.domain.services.pipeline_templates import register


def create_analyze_low_metrics_template() -> AnalysisPipeline:
    """낮은 메트릭 원인 분석 템플릿."""
    nodes = [
        AnalysisNode(
            id="load_data",
            name="데이터 로드",
            module="data_loader",
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
            params={"threshold": 0.5},
            depends_on=["ragas_eval"],
        ),
        AnalysisNode(
            id="diagnostic",
            name="진단 분석",
            module="diagnostic_playbook",
            depends_on=["load_data", "ragas_eval"],
        ),
        AnalysisNode(
            id="causal",
            name="인과 분석",
            module="causal_analyzer",
            depends_on=["load_data", "ragas_eval"],
        ),
        AnalysisNode(
            id="root_cause",
            name="근본 원인 분석",
            module="root_cause_analyzer",
            depends_on=["low_samples", "diagnostic", "causal"],
        ),
        AnalysisNode(
            id="priority_summary",
            name="우선순위 요약",
            module="priority_summary",
            depends_on=["load_data", "ragas_eval"],
        ),
        AnalysisNode(
            id="report",
            name="LLM 분석 보고서",
            module="llm_report",
            params={"report_type": "analysis"},
            depends_on=["load_data", "root_cause"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.ANALYZE_LOW_METRICS,
        nodes=nodes,
    )


def create_analyze_patterns_template() -> AnalysisPipeline:
    """패턴 분석 템플릿."""
    nodes = [
        AnalysisNode(
            id="load_data",
            name="데이터 로드",
            module="data_loader",
        ),
        AnalysisNode(
            id="nlp_analysis",
            name="NLP 분석",
            module="nlp_analyzer",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="pattern_detection",
            name="패턴 탐지",
            module="pattern_detector",
            depends_on=["nlp_analysis"],
        ),
        AnalysisNode(
            id="priority_summary",
            name="우선순위 요약",
            module="priority_summary",
            depends_on=["load_data"],
        ),
        AnalysisNode(
            id="report",
            name="LLM 분석 보고서",
            module="llm_report",
            params={"report_type": "analysis"},
            depends_on=["load_data", "pattern_detection"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.ANALYZE_PATTERNS,
        nodes=nodes,
    )


def create_analyze_trends_template() -> AnalysisPipeline:
    """추세 분석 템플릿."""
    nodes = [
        AnalysisNode(
            id="load_runs",
            name="실행 기록 로드",
            module="run_loader",
        ),
        AnalysisNode(
            id="time_series",
            name="시계열 분석",
            module="time_series_analyzer",
            depends_on=["load_runs"],
        ),
        AnalysisNode(
            id="trend_detection",
            name="추세 탐지",
            module="trend_detector",
            depends_on=["time_series"],
        ),
        AnalysisNode(
            id="report",
            name="LLM 분석 보고서",
            module="llm_report",
            params={"report_type": "trend"},
            depends_on=["load_runs", "trend_detection"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.ANALYZE_TRENDS,
        nodes=nodes,
    )


def create_analyze_statistical_template() -> AnalysisPipeline:
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
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.ANALYZE_STATISTICAL,
        nodes=nodes,
    )


def create_analyze_nlp_template() -> AnalysisPipeline:
    nodes = [
        AnalysisNode(
            id="load_data",
            name="데이터 로드",
            module="data_loader",
        ),
        AnalysisNode(
            id="nlp_analysis",
            name="NLP 분석",
            module="nlp_analyzer",
            depends_on=["load_data"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.ANALYZE_NLP,
        nodes=nodes,
    )


def create_analyze_dataset_features_template() -> AnalysisPipeline:
    nodes = [
        AnalysisNode(
            id="load_data",
            name="데이터 로드",
            module="data_loader",
        ),
        AnalysisNode(
            id="dataset_feature_analysis",
            name="데이터셋 특성 분석",
            module="dataset_feature_analyzer",
            depends_on=["load_data"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.ANALYZE_DATASET_FEATURES,
        nodes=nodes,
    )


def create_analyze_causal_template() -> AnalysisPipeline:
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
            id="causal_analysis",
            name="인과 분석",
            module="causal_analyzer",
            depends_on=["load_data", "statistics"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.ANALYZE_CAUSAL,
        nodes=nodes,
    )


def create_analyze_network_template() -> AnalysisPipeline:
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
            id="network_analysis",
            name="네트워크 분석",
            module="network_analyzer",
            depends_on=["statistics"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.ANALYZE_NETWORK,
        nodes=nodes,
    )


def create_analyze_playbook_template() -> AnalysisPipeline:
    nodes = [
        AnalysisNode(
            id="load_data",
            name="데이터 로드",
            module="data_loader",
        ),
        AnalysisNode(
            id="diagnostic",
            name="진단 분석",
            module="diagnostic_playbook",
            depends_on=["load_data"],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.ANALYZE_PLAYBOOK,
        nodes=nodes,
    )


register(AnalysisIntent.ANALYZE_LOW_METRICS, create_analyze_low_metrics_template)
register(AnalysisIntent.ANALYZE_PATTERNS, create_analyze_patterns_template)
register(AnalysisIntent.ANALYZE_TRENDS, create_analyze_trends_template)
register(AnalysisIntent.ANALYZE_STATISTICAL, create_analyze_statistical_template)
register(AnalysisIntent.ANALYZE_NLP, create_analyze_nlp_template)
register(AnalysisIntent.ANALYZE_DATASET_FEATURES, create_analyze_dataset_features_template)
register(AnalysisIntent.ANALYZE_CAUSAL, create_analyze_causal_template)
register(AnalysisIntent.ANALYZE_NETWORK, create_analyze_network_template)
register(AnalysisIntent.ANALYZE_PLAYBOOK, create_analyze_playbook_template)
