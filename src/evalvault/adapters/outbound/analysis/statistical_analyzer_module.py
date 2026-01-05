"""Phase 14.4: Statistical Analyzer Module.

통계 분석 모듈입니다.
"""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.common import (
    AnalysisDataProcessor,
    BaseAnalysisAdapter,
)
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output
from evalvault.adapters.outbound.analysis.statistical_adapter import (
    StatisticalAnalysisAdapter,
)
from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.analysis import StatisticalAnalysis
from evalvault.domain.entities.result import MetricScore, TestCaseResult


class StatisticalAnalyzerModule(BaseAnalysisModule):
    """통계 분석 모듈.

    메트릭 데이터에 대한 통계 분석을 수행합니다.
    """

    module_id = "statistical_analyzer"
    name = "통계 분석기"
    description = "메트릭 데이터에 대한 통계 분석을 수행합니다."
    input_types = ["metrics"]
    output_types = ["statistics", "summary"]
    requires = ["data_loader"]
    tags = ["analysis", "statistics"]

    def __init__(self, adapter: StatisticalAnalysisAdapter | None = None) -> None:
        self._adapter = adapter or StatisticalAnalysisAdapter()
        self._processor = AnalysisDataProcessor()

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """통계 분석 실행.

        Args:
            inputs: 입력 데이터 (data_loader 출력 포함)
            params: 실행 파라미터

        Returns:
            통계 분석 결과
        """
        data_loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = data_loader_output.get("run")
        metrics = data_loader_output.get("metrics", {})

        analysis = None
        if isinstance(run, EvaluationRun):
            analysis = self._adapter.analyze(run)
        elif metrics:
            pseudo_run = self._build_run_from_metrics(metrics)
            analysis = self._adapter.analyze(pseudo_run)

        if analysis is None:
            return self._empty_output()

        statistics = self._build_statistics(analysis)
        summary = self._build_summary(analysis, statistics)
        processor = self._processor

        return self._build_output(
            analysis,
            summary=summary,
            statistics=statistics,
            insights=analysis.insights,
            extra={
                "correlation_metrics": list(analysis.correlation_metrics),
                "correlation_matrix": list(analysis.correlation_matrix),
                "significant_correlations": processor.to_serializable(
                    analysis.significant_correlations
                ),
                "low_performers": processor.to_serializable(analysis.low_performers),
                "metric_pass_rates": dict(analysis.metric_pass_rates),
            },
        )

    def _build_run_from_metrics(self, metrics: dict[str, list[float]]) -> EvaluationRun:
        """메트릭 딕셔너리를 EvaluationRun으로 변환합니다."""
        run = EvaluationRun(metrics_evaluated=list(metrics.keys()))
        max_len = max(len(values) for values in metrics.values())

        for idx in range(max_len):
            metric_scores: list[MetricScore] = []
            for metric_name, values in metrics.items():
                if idx < len(values):
                    metric_scores.append(MetricScore(name=metric_name, score=values[idx]))
            if metric_scores:
                run.results.append(
                    TestCaseResult(test_case_id=f"auto-{idx}", metrics=metric_scores)
                )

        return run

    def _build_statistics(self, analysis: StatisticalAnalysis) -> dict[str, Any]:
        """메트릭별 통계를 직렬화."""
        processor = self._processor
        return {
            metric: processor.to_serializable(stats)
            for metric, stats in analysis.metrics_summary.items()
        }

    def _build_summary(
        self,
        analysis: StatisticalAnalysis,
        statistics: dict[str, Any],
    ) -> dict[str, Any]:
        """요약 정보를 계산."""
        total_metrics = len(statistics)
        average_score = (
            sum(stat["mean"] for stat in statistics.values()) / total_metrics
            if total_metrics
            else 0.0
        )

        return {
            "total_metrics": total_metrics,
            "average_score": round(average_score, 4),
            "overall_pass_rate": analysis.overall_pass_rate,
        }

    def _empty_output(self) -> dict[str, Any]:
        """데이터가 없을 때의 기본 출력."""
        return self._build_output(
            None,
            summary={},
            statistics={},
            insights=[],
            extra={
                "correlation_metrics": [],
                "correlation_matrix": [],
                "significant_correlations": [],
                "low_performers": [],
                "metric_pass_rates": {},
            },
        )

    def _build_output(
        self,
        analysis: StatisticalAnalysis | None,
        *,
        summary: dict[str, Any],
        statistics: dict[str, Any],
        insights: list[str],
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        """BaseAnalysisAdapter가 없을 때도 동일 포맷으로 출력."""
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
