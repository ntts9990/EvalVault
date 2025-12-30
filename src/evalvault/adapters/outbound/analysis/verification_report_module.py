"""Phase 14.4: Verification Report Module.

검증 보고서 생성 모듈입니다.
"""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule


class VerificationReportModule(BaseAnalysisModule):
    """검증 보고서 모듈.

    검증 결과를 바탕으로 검증 보고서를 생성합니다.
    """

    module_id = "verification_report"
    name = "검증 보고서"
    description = "검증 결과를 바탕으로 검증 보고서를 생성합니다."
    input_types = ["quality_check"]
    output_types = ["report", "verification_status"]
    tags = ["report", "verification"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """검증 보고서 생성.

        Args:
            inputs: 입력 데이터 (quality_check 출력 포함)
            params: 실행 파라미터

        Returns:
            보고서 결과
        """
        quality_check = inputs.get("quality_check", {})
        passed = quality_check.get("passed", False)
        checks = quality_check.get("checks", [])

        # 검증 상태 결정
        verification_status = "passed" if passed else "failed"

        # Markdown 보고서 생성
        report_lines = [
            "# 검증 보고서",
            "",
            f"## 검증 결과: {'통과 ✅' if passed else '실패 ❌'}",
            "",
            "## 검증 항목",
            "",
        ]

        for check in checks:
            status_icon = "✅" if check.get("status") == "pass" else "❌"
            report_lines.append(f"- {check.get('name', 'Unknown')}: {status_icon}")

        report = "\n".join(report_lines)

        return {
            "report": report,
            "verification_status": verification_status,
            "checks": checks,
        }
