"""Phase 14.4: Causal Analyzer Module.

CausalAnalysisAdapter를 파이프라인 노드로 연결합니다.
"""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.causal_adapter import CausalAnalysisAdapter
from evalvault.adapters.outbound.analysis.common import (
    AnalysisDataProcessor,
    BaseAnalysisAdapter,
)
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output
from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.analysis import CausalAnalysis, FactorImpact


class CausalAnalyzerModule(BaseAnalysisModule):
    """인과 분석 모듈.

    테스트 케이스 요인을 분석하여 메트릭에 대한 영향과 근본 원인을 파악합니다.
    """

    module_id = "causal_analyzer"
    name = "인과 분석기"
    description = "질문/답변 특성과 메트릭 간 인과 관계를 분석합니다."
    input_types = ["run"]
    output_types = ["causal_analysis", "insights"]
    requires = ["data_loader"]
    optional_requires = ["statistical_analyzer"]
    tags = ["analysis", "causal"]

    def __init__(self, adapter: CausalAnalysisAdapter | None = None) -> None:
        self._adapter = adapter or CausalAnalysisAdapter()
        self._processor = AnalysisDataProcessor()

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """인과 분석 실행."""
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")

        if not isinstance(run, EvaluationRun):
            return self._empty_output()

        params = params or {}
        analysis = self._adapter.analyze(
            run,
            min_samples=params.get("min_samples", 10),
            significance_level=params.get("significance_level", 0.05),
        )

        factor_stats = self._serialize_factor_stats(analysis)
        significant_impacts = self._serialize_impacts(
            analysis.significant_impacts[: params.get("top_impacts", 5)]
        )
        processor = self._processor
        root_causes = processor.to_serializable(analysis.root_causes)
        interventions = processor.to_serializable(analysis.interventions)
        statistics = self._build_statistics(
            analysis,
            factor_stats=factor_stats,
            significant_impacts=significant_impacts,
            root_causes=root_causes,
            interventions=interventions,
        )

        return self._build_output(
            analysis,
            summary=self._build_summary(analysis),
            statistics=statistics,
            insights=analysis.insights,
            extra={
                "factor_stats": factor_stats,
                "significant_impacts": significant_impacts,
                "root_causes": root_causes,
                "interventions": interventions,
            },
        )

    def _empty_output(self) -> dict[str, Any]:
        """입력 데이터가 없을 때의 기본 출력."""
        return self._build_output(
            None,
            summary={},
            statistics={},
            insights=[],
            extra={
                "factor_stats": {},
                "significant_impacts": [],
                "root_causes": [],
                "interventions": [],
            },
        )

    def _build_summary(self, analysis: CausalAnalysis) -> dict[str, Any]:
        """핵심 요약 정보 생성."""
        summary: dict[str, Any] = {
            "run_id": analysis.run_id,
            "factor_count": len(analysis.factor_stats),
            "significant_impact_count": len(analysis.significant_impacts),
            "root_cause_count": len(analysis.root_causes),
        }

        if analysis.significant_impacts:
            summary["top_metrics"] = list(
                {impact.metric_name for impact in analysis.significant_impacts[:3]}
            )

        if analysis.interventions:
            summary["recommended_interventions"] = [
                intervention.intervention for intervention in analysis.interventions[:3]
            ]

        return summary

    def _serialize_factor_stats(self, analysis: CausalAnalysis) -> dict[str, Any]:
        """요인별 통계를 직렬화."""
        processor = self._processor
        serialized: dict[str, Any] = {}
        for factor_type, stats in analysis.factor_stats.items():
            serialized[factor_type.value] = processor.to_serializable(stats)
        return serialized

    def _serialize_impacts(self, impacts: list[FactorImpact]) -> list[dict[str, Any]]:
        """주요 요인 영향 정보를 직렬화."""
        processor = self._processor
        serialized = []
        for impact in impacts:
            serialized.append(processor.to_serializable(impact))
        return serialized

    def _build_statistics(
        self,
        analysis: CausalAnalysis,
        *,
        factor_stats: dict[str, Any],
        significant_impacts: list[dict[str, Any]],
        root_causes: list[dict[str, Any]] | None,
        interventions: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        """분석 결과를 statistics 섹션으로 묶기."""
        processor = self._processor
        statistics: dict[str, Any] = {}
        if factor_stats:
            statistics["factor_stats"] = factor_stats
        if significant_impacts:
            statistics["significant_impacts"] = significant_impacts
        if analysis.causal_relationships:
            statistics["causal_relationships"] = processor.to_serializable(
                analysis.causal_relationships
            )
        if root_causes:
            statistics["root_causes"] = root_causes
        if interventions:
            statistics["interventions"] = interventions
        return statistics

    def _build_output(
        self,
        analysis: CausalAnalysis | None,
        *,
        summary: dict[str, Any],
        statistics: dict[str, Any],
        insights: list[str],
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        """어댑터 mock 환경에서도 공통 포맷 유지."""
        if isinstance(self._adapter, BaseAnalysisAdapter):
            return self._adapter.build_module_output(
                analysis,
                summary=summary,
                statistics=statistics,
                insights=insights,
                extra=extra,
            )
        return self._processor.build_output_payload(
            analysis,
            summary=summary,
            statistics=statistics,
            insights=insights,
            extra=extra,
        )
