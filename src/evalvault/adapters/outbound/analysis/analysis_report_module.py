"""Phase 14.4: Analysis Report Module.

분석 보고서 생성 모듈입니다.
"""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule


class AnalysisReportModule(BaseAnalysisModule):
    """분석 보고서 모듈.

    분석 결과를 바탕으로 분석 보고서를 생성합니다.
    """

    module_id = "analysis_report"
    name = "분석 보고서"
    description = "분석 결과를 바탕으로 분석 보고서를 생성합니다."
    input_types = ["root_cause", "pattern_detection", "trend_detection"]
    output_types = ["report", "analysis_summary"]
    tags = ["report", "analysis"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """분석 보고서 생성.

        Args:
            inputs: 입력 데이터 (root_cause, pattern_detection 등 포함)
            params: 실행 파라미터

        Returns:
            보고서 결과
        """
        root_cause = inputs.get("root_cause", {})
        pattern_detection = inputs.get("pattern_detection", {})
        trend_detection = inputs.get("trend_detection", {})

        causes = root_cause.get("causes", [])
        recommendations = root_cause.get("recommendations", [])
        patterns = pattern_detection.get("patterns", [])
        trend_items = trend_detection.get("trends", [])

        # Markdown 보고서 생성
        report_lines = [
            "# 분석 보고서",
            "",
            "## 근본 원인 분석",
            "",
        ]

        if causes:
            for cause in causes:
                metric = cause.get("metric", "Unknown")
                reason = cause.get("reason", "Unknown")
                report_lines.append(f"- **{metric}**: {reason}")
        else:
            report_lines.append("- 분석된 원인이 없습니다.")

        report_lines.extend(
            [
                "",
                "## 권장 사항",
                "",
            ]
        )

        if recommendations:
            for rec in recommendations:
                report_lines.append(f"- {rec}")
        else:
            report_lines.append("- 권장 사항이 없습니다.")

        if patterns:
            report_lines.extend(
                [
                    "",
                    "## 패턴 탐지",
                    "",
                ]
            )
            for pattern in patterns[:5]:
                label = pattern.get("label", "Pattern")
                detail = pattern.get("detail", "")
                report_lines.append(f"- {label}: {detail}")
        elif pattern_detection:
            report_lines.extend(["", "## 패턴 탐지", "", "- 탐지된 패턴이 없습니다."])

        if trend_items:
            report_lines.extend(
                [
                    "",
                    "## 추세 분석",
                    "",
                ]
            )
            for trend in trend_items:
                metric = trend.get("metric", "metric")
                direction = trend.get("direction", "flat")
                delta = trend.get("delta", 0)
                report_lines.append(f"- {metric}: {direction} ({delta:+.2f})")
        elif trend_detection:
            report_lines.extend(["", "## 추세 분석", "", "- 탐지된 추세가 없습니다."])

        report = "\n".join(report_lines)

        analysis_summary = {
            "cause_count": len(causes),
            "recommendation_count": len(recommendations),
            "pattern_count": len(patterns),
            "trend_count": len(trend_items),
        }

        return {
            "report": report,
            "analysis_summary": analysis_summary,
            "causes": causes,
            "recommendations": recommendations,
            "patterns": patterns,
            "trends": trend_items,
        }
