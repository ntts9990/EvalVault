"""``verify_/compare_/analyze_/generate_`` 접두어에 속하지 않는 빌더.

분류 근거:
- :data:`AnalysisIntent.DETECT_ANOMALIES` — 이상 탐지(detect_).
- :data:`AnalysisIntent.FORECAST_PERFORMANCE` — 시계열 예측(forecast_).
- :data:`AnalysisIntent.BENCHMARK_RETRIEVAL` — 검색 벤치마크(benchmark_).

세 빌더 모두 4-그룹 명명 규칙에 어울리지 않아 분리된 모듈에 모았습니다.
"""

from __future__ import annotations

from evalvault.domain.entities.analysis_pipeline import (
    AnalysisIntent,
    AnalysisNode,
    AnalysisPipeline,
)
from evalvault.domain.services.pipeline_templates import register


def create_detect_anomalies_template() -> AnalysisPipeline:
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


def create_forecast_performance_template() -> AnalysisPipeline:
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


def create_benchmark_retrieval_template() -> AnalysisPipeline:
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


register(AnalysisIntent.DETECT_ANOMALIES, create_detect_anomalies_template)
register(AnalysisIntent.FORECAST_PERFORMANCE, create_forecast_performance_template)
register(AnalysisIntent.BENCHMARK_RETRIEVAL, create_benchmark_retrieval_template)
