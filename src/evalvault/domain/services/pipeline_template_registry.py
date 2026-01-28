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
        self._templates[AnalysisIntent.ANALYZE_STATISTICAL] = (
            self._create_analyze_statistical_template()
        )
        self._templates[AnalysisIntent.ANALYZE_NLP] = self._create_analyze_nlp_template()
        self._templates[AnalysisIntent.ANALYZE_DATASET_FEATURES] = (
            self._create_analyze_dataset_features_template()
        )
        self._templates[AnalysisIntent.ANALYZE_CAUSAL] = self._create_analyze_causal_template()
        self._templates[AnalysisIntent.ANALYZE_NETWORK] = self._create_analyze_network_template()
        self._templates[AnalysisIntent.ANALYZE_PLAYBOOK] = self._create_analyze_playbook_template()
        self._templates[AnalysisIntent.DETECT_ANOMALIES] = self._create_detect_anomalies_template()
        self._templates[AnalysisIntent.FORECAST_PERFORMANCE] = (
            self._create_forecast_performance_template()
        )
        self._templates[AnalysisIntent.GENERATE_HYPOTHESES] = (
            self._create_generate_hypotheses_template()
        )
        self._templates[AnalysisIntent.BENCHMARK_RETRIEVAL] = (
            self._create_benchmark_retrieval_template()
        )
        # 보고서 템플릿
        self._templates[AnalysisIntent.GENERATE_SUMMARY] = self._create_generate_summary_template()
        self._templates[AnalysisIntent.GENERATE_DETAILED] = (
            self._create_generate_detailed_template()
        )
        self._templates[AnalysisIntent.GENERATE_COMPARISON] = (
            self._create_generate_comparison_template()
        )

    def get_template(self, intent: AnalysisIntent) -> AnalysisPipeline | None:
        """의도에 대응하는 파이프라인 템플릿 조회."""
        return self._templates.get(intent)

    def list_all(self) -> list[tuple[AnalysisIntent, AnalysisPipeline]]:
        return list(self._templates.items())

    # =========================================================================
    # Verification Templates
    # =========================================================================

    def _create_verify_morpheme_template(self) -> AnalysisPipeline:
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

    def _create_analyze_statistical_template(self) -> AnalysisPipeline:
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

    def _create_analyze_nlp_template(self) -> AnalysisPipeline:
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

    def _create_analyze_dataset_features_template(self) -> AnalysisPipeline:
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

    def _create_analyze_causal_template(self) -> AnalysisPipeline:
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

    def _create_analyze_network_template(self) -> AnalysisPipeline:
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

    def _create_analyze_playbook_template(self) -> AnalysisPipeline:
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

    def _create_detect_anomalies_template(self) -> AnalysisPipeline:
        nodes = [
            AnalysisNode(
                id="load_runs",
                name="실행 기록 로드",
                module="run_loader",
            ),
            AnalysisNode(
                id="anomaly_detection",
                name="이상 탐지",
                module="timeseries_advanced",
                params={"mode": "anomaly"},
                depends_on=["load_runs"],
            ),
        ]
        return AnalysisPipeline(
            intent=AnalysisIntent.DETECT_ANOMALIES,
            nodes=nodes,
        )

    def _create_forecast_performance_template(self) -> AnalysisPipeline:
        nodes = [
            AnalysisNode(
                id="load_runs",
                name="실행 기록 로드",
                module="run_loader",
            ),
            AnalysisNode(
                id="forecast",
                name="성능 예측",
                module="timeseries_advanced",
                params={"mode": "forecast"},
                depends_on=["load_runs"],
            ),
        ]
        return AnalysisPipeline(
            intent=AnalysisIntent.FORECAST_PERFORMANCE,
            nodes=nodes,
        )

    def _create_generate_hypotheses_template(self) -> AnalysisPipeline:
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

    def _create_benchmark_retrieval_template(self) -> AnalysisPipeline:
        """검색 벤치마크 템플릿."""
        nodes = [
            AnalysisNode(
                id="retrieval_benchmark",
                name="검색 벤치마크",
                module="retrieval_benchmark",
            )
        ]
        return AnalysisPipeline(
            intent=AnalysisIntent.BENCHMARK_RETRIEVAL,
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

    def _create_generate_detailed_template(self) -> AnalysisPipeline:
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

    def _create_generate_comparison_template(self) -> AnalysisPipeline:
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
