"""Phase 14.4: Comparison Report Module.

비교 보고서 생성 모듈입니다.
"""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule


class ComparisonReportModule(BaseAnalysisModule):
    """비교 보고서 모듈.

    비교 결과를 바탕으로 비교 보고서를 생성합니다.
    """

    module_id = "comparison_report"
    name = "비교 보고서"
    description = "비교 결과를 바탕으로 비교 보고서를 생성합니다."
    input_types = ["comparison"]
    output_types = ["report", "comparison_summary"]
    tags = ["report", "comparison"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """비교 보고서 생성.

        Args:
            inputs: 입력 데이터 (comparison 출력 포함)
            params: 실행 파라미터

        Returns:
            보고서 결과
        """
        # comparison 또는 statistical_comparator 출력에서 데이터 가져오기
        comparison = inputs.get("comparison", {})
        if not comparison:
            comparison = inputs.get("statistical_comparator", {})
        if not comparison:
            comparison = inputs.get("statistical_comparison", {})
        if not comparison:
            comparison = inputs.get("run_comparison", {})

        winner = comparison.get("winner", "N/A")

        # Markdown 보고서 생성
        report_lines = [
            "# 비교 보고서",
            "",
            "## 비교 결과",
            "",
        ]

        # 각 방식/모델의 점수 나열
        for key, value in comparison.items():
            if key == "winner":
                continue
            if isinstance(value, dict) and "score" in value:
                report_lines.append(f"- {key}: {value['score']:.2%}")

        report_lines.extend(
            [
                "",
                f"## 우승: {winner}",
            ]
        )

        report = "\n".join(report_lines)

        comparison_summary = {
            "winner": winner,
            "methods": [k for k in comparison if k != "winner"],
        }

        return {
            "report": report,
            "comparison_summary": comparison_summary,
        }
