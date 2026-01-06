"""Phase 14.2: Pipeline Template Registry.

의도별 분석 파이프라인 템플릿을 관리하는 레지스트리입니다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from evalvault.domain.entities.analysis_pipeline import (
    AnalysisIntent,
    AnalysisNode,
    AnalysisPipeline,
)

# =============================================================================
# PipelineTemplateRegistry
# =============================================================================


@dataclass
class PipelineTemplateRegistry:
    """파이프라인 템플릿 레지스트리.

    각 분석 의도에 대한 기본 파이프라인 템플릿을 관리합니다.
    """

    _templates: dict[AnalysisIntent, AnalysisPipeline] = field(default_factory=dict)

    def __post_init__(self):
        """기본 템플릿 등록."""
        self._register_default_templates()

    def _register_default_templates(self):
        """의도별 기본 파이프라인 템플릿 등록."""
        # 검증 템플릿
        self._templates[AnalysisIntent.VERIFY_MORPHEME] = self._create_verify_morpheme_template()
        self._templates[AnalysisIntent.VERIFY_EMBEDDING] = self._create_verify_embedding_template()
        self._templates[AnalysisIntent.VERIFY_RETRIEVAL] = self._create_verify_retrieval_template()

        # 비교 템플릿
        self._templates[AnalysisIntent.COMPARE_SEARCH_METHODS] = (
            self._create_compare_search_template()
        )
        self._templates[AnalysisIntent.COMPARE_MODELS] = self._create_compare_models_template()
        self._templates[AnalysisIntent.COMPARE_RUNS] = self._create_compare_runs_template()

        # 분석 템플릿
        self._templates[AnalysisIntent.ANALYZE_LOW_METRICS] = (
            self._create_analyze_low_metrics_template()
        )
        self._templates[AnalysisIntent.ANALYZE_PATTERNS] = self._create_analyze_patterns_template()
        self._templates[AnalysisIntent.ANALYZE_TRENDS] = self._create_analyze_trends_template()

        # 보고서 템플릿
        self._templates[AnalysisIntent.GENERATE_SUMMARY] = self._create_generate_summary_template()
        self._templates[AnalysisIntent.GENERATE_DETAILED] = (
            self._create_generate_detailed_template()
        )
        self._templates[AnalysisIntent.GENERATE_COMPARISON] = (
            self._create_generate_comparison_template()
        )

    def get_template(self, intent: AnalysisIntent) -> AnalysisPipeline | None:
        """의도에 대한 템플릿 조회.

        Args:
            intent: 분석 의도

        Returns:
            파이프라인 템플릿 또는 None
        """
        return self._templates.get(intent)

    def list_all(self) -> list[tuple[AnalysisIntent, AnalysisPipeline]]:
        """모든 템플릿 목록.

        Returns:
            (의도, 템플릿) 튜플 목록
        """
        return list(self._templates.items())

    # =========================================================================
    # Verification Templates
    # =========================================================================

    def _create_verify_morpheme_template(self) -> AnalysisPipeline:
        """형태소 분석 검증 템플릿."""
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
                name="품질 검사",
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

    def _create_verify_embedding_template(self) -> AnalysisPipeline:
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
                id="distribution_check",
                name="분포 검사",
                module="embedding_distribution",
                depends_on=["embedding_analysis"],
            ),
            AnalysisNode(
                id="report",
                name="검증 보고서",
                module="verification_report",
                depends_on=["distribution_check"],
            ),
        ]
        return AnalysisPipeline(
            intent=AnalysisIntent.VERIFY_EMBEDDING,
            nodes=nodes,
        )

    def _create_verify_retrieval_template(self) -> AnalysisPipeline:
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
                name="품질 검사",
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

    # =========================================================================
    # Comparison Templates
    # =========================================================================

    def _create_compare_search_template(self) -> AnalysisPipeline:
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

    def _create_compare_models_template(self) -> AnalysisPipeline:
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

    def _create_compare_runs_template(self) -> AnalysisPipeline:
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

    # =========================================================================
    # Analysis Templates
    # =========================================================================

    def _create_analyze_low_metrics_template(self) -> AnalysisPipeline:
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
                depends_on=["ragas_eval"],
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

    def _create_analyze_patterns_template(self) -> AnalysisPipeline:
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

    def _create_analyze_trends_template(self) -> AnalysisPipeline:
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

    # =========================================================================
    # Report Templates
    # =========================================================================

    def _create_generate_summary_template(self) -> AnalysisPipeline:
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
                depends_on=["load_data", "statistics"],
            ),
        ]
        return AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_SUMMARY,
            nodes=nodes,
        )

    def _create_generate_detailed_template(self) -> AnalysisPipeline:
        """상세 보고서 생성 템플릿."""
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
                id="nlp_analysis",
                name="NLP 분석",
                module="nlp_analyzer",
                depends_on=["load_data"],
            ),
            AnalysisNode(
                id="causal_analysis",
                name="인과 분석",
                module="causal_analyzer",
                depends_on=["load_data", "statistics"],
            ),
            AnalysisNode(
                id="priority_summary",
                name="우선순위 요약",
                module="priority_summary",
                depends_on=["load_data"],
            ),
            AnalysisNode(
                id="report",
                name="LLM 상세 보고서",
                module="llm_report",
                params={"report_type": "detailed"},
                depends_on=["load_data", "statistics", "nlp_analysis", "causal_analysis"],
            ),
        ]
        return AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_DETAILED,
            nodes=nodes,
        )

    def _create_generate_comparison_template(self) -> AnalysisPipeline:
        """비교 보고서 생성 템플릿."""
        nodes = [
            AnalysisNode(
                id="load_runs",
                name="실행 결과 로드",
                module="run_loader",
            ),
            AnalysisNode(
                id="run_comparison",
                name="실행 비교",
                module="run_comparator",
                depends_on=["load_runs"],
            ),
            AnalysisNode(
                id="report",
                name="LLM 비교 보고서",
                module="llm_report",
                params={"report_type": "comparison"},
                depends_on=["load_runs", "run_comparison"],
            ),
        ]
        return AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_COMPARISON,
            nodes=nodes,
        )
