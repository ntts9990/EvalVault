"""Phase 14.4: Summary Report Module.

요약 보고서 생성 모듈입니다.
"""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule


class SummaryReportModule(BaseAnalysisModule):
    """요약 보고서 모듈.

    통계 분석 결과를 바탕으로 요약 보고서를 생성합니다.
    """

    module_id = "summary_report"
    name = "요약 보고서"
    description = "통계 분석 결과를 바탕으로 요약 보고서를 생성합니다."
    input_types = ["statistics", "summary"]
    output_types = ["report"]
    requires = ["statistical_analyzer"]
    tags = ["report", "summary"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """요약 보고서 생성.

        Args:
            inputs: 입력 데이터 (statistical_analyzer 출력 포함)
            params: 실행 파라미터

        Returns:
            보고서 결과
        """
        stats_output = inputs.get("statistical_analyzer", {})
        statistics = stats_output.get("statistics", {})
        summary = stats_output.get("summary", {})

        # Markdown 보고서 생성
        report_lines = [
            "# 평가 결과 요약 보고서",
            "",
            "## 개요",
            f"- 분석된 메트릭 수: {summary.get('total_metrics', 0)}",
            f"- 전체 평균 점수: {summary.get('average_score', 0):.2%}",
            "",
            "## 메트릭별 통계",
            "",
        ]

        for metric_name, stats in statistics.items():
            report_lines.extend(
                [
                    f"### {metric_name}",
                    f"- 평균: {stats.get('mean', 0):.2%}",
                    f"- 표준편차: {stats.get('std', 0):.4f}",
                    f"- 최소: {stats.get('min', 0):.2%}",
                    f"- 최대: {stats.get('max', 0):.2%}",
                    "",
                ]
            )

        report = "\n".join(report_lines)

        return {
            "report": report,
            "format": "markdown",
            "statistics": statistics,
            "summary": summary,
        }
