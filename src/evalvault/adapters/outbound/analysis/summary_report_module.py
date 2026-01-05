"""Phase 14.4: Summary Report Module.

요약 보고서 생성 모듈입니다.
"""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output
from evalvault.domain.entities.analysis import StatisticalAnalysis


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
        stats_output = get_upstream_output(inputs, "statistical_analyzer", "statistics") or {}
        statistics = stats_output.get("statistics", {})
        summary = stats_output.get("summary", {}) or {}
        analysis_id = stats_output.get("analysis_id")
        insights = stats_output.get("insights", [])
        metric_pass_rates = stats_output.get("metric_pass_rates", {})
        low_performers = stats_output.get("low_performers", [])
        analysis: StatisticalAnalysis | None = stats_output.get("analysis")

        overall_pass_rate = summary.get("overall_pass_rate", 0.0)

        # Markdown 보고서 생성
        report_lines = [
            "# 평가 결과 요약 보고서",
        ]

        if analysis_id:
            report_lines.extend(["", f"- 분석 ID: `{analysis_id}`"])

        report_lines.extend(
            [
                "",
                "## 개요",
                f"- 분석된 메트릭 수: {summary.get('total_metrics', 0)}",
                f"- 전체 평균 점수: {summary.get('average_score', 0):.2%}",
                f"- 전체 통과율: {overall_pass_rate:.2%}",
                "",
                "## 메트릭별 통계",
                "",
            ]
        )

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

        if metric_pass_rates:
            report_lines.extend(
                [
                    "## 메트릭 통과율",
                    "",
                ]
            )
            for metric, rate in metric_pass_rates.items():
                report_lines.append(f"- {metric}: {rate:.2%}")
            report_lines.append("")

        if insights:
            report_lines.extend(["## 주요 인사이트", ""])
            for insight in insights:
                report_lines.append(f"- {insight}")
            report_lines.append("")

        if low_performers:
            report_lines.extend(["## 주의가 필요한 테스트 케이스", ""])
            for lp in low_performers[:5]:
                report_lines.append(
                    f"- {lp.get('test_case_id', 'unknown')} ({lp.get('metric_name')}): "
                    f"{lp.get('score', 0):.2%} / threshold {lp.get('threshold', 0):.2%}"
                )
            report_lines.append("")

        report = "\n".join(report_lines)

        return {
            "report": report,
            "format": "markdown",
            "analysis_id": analysis_id,
            "statistics": statistics,
            "summary": summary,
            "insights": insights,
            "metric_pass_rates": metric_pass_rates,
            "low_performers": low_performers,
            "analysis": analysis,
        }
