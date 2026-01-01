"""Phase 14.4: Statistical Analyzer Module.

통계 분석 모듈입니다.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
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
        data_loader_output = inputs.get("data_loader", {})
        run = data_loader_output.get("run")
        metrics = data_loader_output.get("metrics", {})

        analysis = None
        if isinstance(run, EvaluationRun):
            analysis = self._adapter.analyze(run)
        elif metrics:
            pseudo_run = self._build_run_from_metrics(metrics)
            analysis = self._adapter.analyze(pseudo_run)

        if analysis is None:
            return {
                "statistics": {},
                "summary": {"total_metrics": 0, "average_score": 0.0},
                "analysis": None,
            }

        output = self._serialize_analysis(analysis)
        output["analysis"] = analysis
        return output

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

    def _serialize_analysis(self, analysis: StatisticalAnalysis) -> dict[str, Any]:
        """StatisticalAnalysis 객체를 파이프라인 출력 형태로 직렬화."""
        statistics = {metric: asdict(stats) for metric, stats in analysis.metrics_summary.items()}
        total_metrics = len(statistics)
        average_score = (
            sum(stat["mean"] for stat in statistics.values()) / total_metrics
            if total_metrics
            else 0.0
        )

        return {
            "analysis_id": analysis.analysis_id,
            "run_id": analysis.run_id,
            "statistics": statistics,
            "summary": {
                "total_metrics": total_metrics,
                "average_score": round(average_score, 4),
                "overall_pass_rate": analysis.overall_pass_rate,
            },
            "correlation_metrics": analysis.correlation_metrics,
            "correlation_matrix": analysis.correlation_matrix,
            "significant_correlations": [asdict(c) for c in analysis.significant_correlations],
            "low_performers": [asdict(lp) for lp in analysis.low_performers],
            "insights": list(analysis.insights),
            "metric_pass_rates": analysis.metric_pass_rates,
        }
