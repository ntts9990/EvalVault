"""Detailed report module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output


class DetailedReportModule(BaseAnalysisModule):
    """Generate a detailed markdown report from multiple analyses."""

    module_id = "detailed_report"
    name = "Detailed Report"
    description = "Compose a detailed markdown report from stats/NLP/causal outputs."
    input_types = ["statistics", "nlp_analysis", "causal_analysis"]
    output_types = ["report"]
    requires = ["statistical_analyzer", "nlp_analyzer", "causal_analyzer"]
    tags = ["report", "detailed"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        stats_output = get_upstream_output(inputs, "statistics", "statistical_analyzer") or {}
        nlp_output = get_upstream_output(inputs, "nlp_analysis", "nlp_analyzer") or {}
        causal_output = get_upstream_output(inputs, "causal_analysis", "causal_analyzer") or {}

        stats_summary = stats_output.get("summary", {}) or {}
        stats_metrics = stats_output.get("statistics", {}) or {}
        top_keywords = nlp_output.get("top_keywords", [])
        question_types = nlp_output.get("question_types", [])
        root_causes = causal_output.get("root_causes", [])
        interventions = causal_output.get("interventions", [])

        report_lines = [
            "# 상세 보고서",
            "",
            "## 통계 요약",
            f"- 분석된 메트릭 수: {stats_summary.get('total_metrics', 0)}",
            f"- 평균 점수: {stats_summary.get('average_score', 0):.2%}",
            f"- 전체 통과율: {stats_summary.get('overall_pass_rate', 0):.2%}",
            "",
            "## 메트릭 하이라이트",
            "",
        ]

        metric_means = []
        for metric, stats in stats_metrics.items():
            if isinstance(stats, dict) and "mean" in stats:
                metric_means.append((metric, stats["mean"]))
        metric_means.sort(key=lambda item: item[1], reverse=True)

        if metric_means:
            for metric, mean in metric_means[:5]:
                report_lines.append(f"- {metric}: {mean:.2%}")
        else:
            report_lines.append("- 메트릭 요약 정보가 없습니다.")

        report_lines.extend(["", "## 질문/키워드 패턴", ""])
        if top_keywords:
            report_lines.append(
                "- 주요 키워드: " + ", ".join(kw.get("keyword", "") for kw in top_keywords[:5])
            )
        if question_types:
            report_lines.append(
                "- 주요 질문 유형: "
                + ", ".join(qt.get("question_type", "") for qt in question_types[:3])
            )
        if not top_keywords and not question_types:
            report_lines.append("- NLP 요약 정보가 없습니다.")

        report_lines.extend(["", "## 인과 분석 요약", ""])
        if root_causes:
            for cause in root_causes[:3]:
                if isinstance(cause, dict):
                    report_lines.append(f"- {cause.get('description', 'Root cause')} ")
        else:
            report_lines.append("- 인과 분석 결과가 없습니다.")

        if interventions:
            report_lines.extend(["", "## 권장 사항", ""])
            for intervention in interventions[:5]:
                if isinstance(intervention, dict):
                    report_lines.append(f"- {intervention.get('intervention', '')}")
                elif isinstance(intervention, str):
                    report_lines.append(f"- {intervention}")

        report = "\n".join(report_lines)

        return {
            "report": report,
            "format": "markdown",
        }
