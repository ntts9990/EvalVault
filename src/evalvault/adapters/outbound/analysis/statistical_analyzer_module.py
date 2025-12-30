"""Phase 14.4: Statistical Analyzer Module.

통계 분석 모듈입니다.
"""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule


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
        # data_loader 출력에서 메트릭 데이터 가져오기
        data_loader_output = inputs.get("data_loader", {})
        metrics = data_loader_output.get("metrics", {})

        statistics = {}
        total_mean = 0.0
        metric_count = 0

        for metric_name, values in metrics.items():
            if not values:
                continue

            # 기본 통계 계산
            n = len(values)
            mean = sum(values) / n
            sorted_values = sorted(values)
            median = (
                sorted_values[n // 2]
                if n % 2 == 1
                else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
            )
            min_val = min(values)
            max_val = max(values)

            # 표준편차 계산
            variance = sum((x - mean) ** 2 for x in values) / n
            std = variance**0.5

            statistics[metric_name] = {
                "count": n,
                "mean": round(mean, 4),
                "median": round(median, 4),
                "std": round(std, 4),
                "min": round(min_val, 4),
                "max": round(max_val, 4),
            }

            total_mean += mean
            metric_count += 1

        summary = {
            "total_metrics": metric_count,
            "average_score": round(total_mean / metric_count, 4) if metric_count > 0 else 0.0,
        }

        return {
            "statistics": statistics,
            "summary": summary,
        }
