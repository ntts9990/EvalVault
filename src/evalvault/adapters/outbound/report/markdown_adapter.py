"""Markdown report generation adapter."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evalvault.domain.entities.analysis import (
        AnalysisBundle,
        CausalAnalysis,
        NLPAnalysis,
        StatisticalAnalysis,
    )


class MarkdownReportAdapter:
    """Markdown 형식 보고서 생성 어댑터.

    ReportPort 인터페이스를 구현합니다.
    """

    def generate_markdown(
        self,
        bundle: AnalysisBundle,
        *,
        include_nlp: bool = True,
        include_causal: bool = True,
        include_recommendations: bool = True,
    ) -> str:
        """Markdown 형식 보고서 생성.

        Args:
            bundle: 분석 결과 번들
            include_nlp: NLP 분석 포함 여부
            include_causal: 인과 분석 포함 여부
            include_recommendations: 권장사항 포함 여부

        Returns:
            Markdown 형식의 보고서 문자열
        """
        sections = []

        # 헤더
        sections.append(self._generate_header(bundle))

        # 요약
        sections.append(self._generate_summary(bundle))

        # 통계 분석
        if bundle.statistical:
            sections.append(self._generate_statistical_section(bundle.statistical))

        # NLP 분석
        if include_nlp and bundle.has_nlp and bundle.nlp:
            sections.append(self._generate_nlp_section(bundle.nlp))

        # 인과 분석
        if include_causal and bundle.has_causal and bundle.causal:
            sections.append(self._generate_causal_section(bundle.causal))

        # 권장사항
        if include_recommendations:
            sections.append(self._generate_recommendations(bundle))

        # 푸터
        sections.append(self._generate_footer())

        return "\n\n".join(sections)

    def generate_html(
        self,
        bundle: AnalysisBundle,
        *,
        include_nlp: bool = True,
        include_causal: bool = True,
        include_recommendations: bool = True,
    ) -> str:
        """HTML 형식 보고서 생성.

        Markdown을 HTML로 변환합니다.

        Args:
            bundle: 분석 결과 번들
            include_nlp: NLP 분석 포함 여부
            include_causal: 인과 분석 포함 여부
            include_recommendations: 권장사항 포함 여부

        Returns:
            HTML 형식의 보고서 문자열
        """
        markdown_content = self.generate_markdown(
            bundle,
            include_nlp=include_nlp,
            include_causal=include_causal,
            include_recommendations=include_recommendations,
        )

        # 간단한 Markdown to HTML 변환
        html_body = self._markdown_to_html(markdown_content)

        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EvalVault 분석 리포트 - {bundle.run_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .pass {{ color: #27ae60; font-weight: bold; }}
        .fail {{ color: #e74c3c; font-weight: bold; }}
        .insight {{ background-color: #ecf0f1; padding: 10px; border-left: 4px solid #3498db; margin: 10px 0; }}
        .recommendation {{ background-color: #fdf2e9; padding: 10px; border-left: 4px solid #e67e22; margin: 10px 0; }}
        code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 0.9em; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    def _generate_header(self, bundle: AnalysisBundle) -> str:
        """보고서 헤더 생성."""
        return f"""# EvalVault 분석 리포트

**실행 ID:** `{bundle.run_id}`
**생성 시각:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""

    def _generate_summary(self, bundle: AnalysisBundle) -> str:
        """요약 섹션 생성."""
        lines = ["## 요약"]

        if bundle.statistical:
            stat = bundle.statistical
            pass_rate = stat.overall_pass_rate
            status = "통과" if pass_rate >= 0.7 else "실패"
            status_emoji = "✅" if pass_rate >= 0.7 else "❌"

            lines.append(f"\n**전체 상태:** {status_emoji} {status}")
            lines.append(f"**통과율:** {pass_rate:.1%}")

            if stat.metric_pass_rates:
                lines.append("\n### 메트릭 통과율")
                lines.append("| 메트릭 | 통과율 |")
                lines.append("|--------|-----------|")
                for metric, rate in sorted(stat.metric_pass_rates.items()):
                    lines.append(f"| {metric} | {rate:.1%} |")

        return "\n".join(lines)

    def _generate_statistical_section(self, stat: StatisticalAnalysis) -> str:
        """통계 분석 섹션 생성."""
        lines = ["## 통계 분석"]

        # 메트릭 통계
        if stat.metrics_summary:
            lines.append("\n### 메트릭 통계")
            lines.append("| 메트릭 | 평균 | 표준편차 | 최소 | 최대 |")
            lines.append("|--------|------|---------|-----|-----|")

            for name, stats in sorted(stat.metrics_summary.items()):
                lines.append(
                    f"| {name} | {stats.mean:.3f} | {stats.std:.3f} | "
                    f"{stats.min:.3f} | {stats.max:.3f} |"
                )

        # 상관관계
        if stat.significant_correlations:
            lines.append("\n### 유의미한 상관관계")
            for corr in stat.significant_correlations[:5]:
                direction = "양(+)" if corr.correlation > 0 else "음(-)"
                lines.append(
                    f"- **{corr.variable1}** ↔ **{corr.variable2}**: "
                    f"{corr.correlation:.2f} ({direction})"
                )

        # 낮은 성능 케이스
        if stat.low_performers:
            lines.append("\n### 낮은 성능 케이스")
            lines.append("| 테스트 케이스 | 질문 | 메트릭 | 점수 |")
            lines.append("|-------------|------|--------|------|")

            for lp in stat.low_performers[:5]:
                question_preview = (
                    lp.question_preview[:40] + "..."
                    if len(lp.question_preview) > 40
                    else lp.question_preview
                )
                lines.append(
                    f"| {lp.test_case_id} | {question_preview} | "
                    f"{lp.metric_name} | {lp.score:.2f} |"
                )

        # 인사이트
        if stat.insights:
            lines.append("\n### 인사이트")
            for insight in stat.insights:
                lines.append(f"- {insight}")

        return "\n".join(lines)

    def _generate_nlp_section(self, nlp: NLPAnalysis) -> str:
        """NLP 분석 섹션 생성."""
        lines = ["## NLP 분석"]

        # 텍스트 통계
        if nlp.question_stats:
            stats = nlp.question_stats
            lines.append("\n### 텍스트 통계 (질문)")
            lines.append(f"- **총 단어 수:** {stats.word_count:,}")
            lines.append(f"- **총 문장 수:** {stats.sentence_count:,}")
            lines.append(f"- **평균 단어 길이:** {stats.avg_word_length:.1f}")
            lines.append(f"- **어휘 다양성:** {stats.unique_word_ratio:.1%}")

        # 질문 유형
        if nlp.question_types:
            lines.append("\n### 질문 유형 분포")
            lines.append("| 유형 | 개수 | 비율 |")
            lines.append("|------|------|------|")

            for qt in nlp.question_types:
                lines.append(
                    f"| {qt.question_type.value.capitalize()} | {qt.count} | {qt.percentage:.1%} |"
                )

        # 키워드
        if nlp.top_keywords:
            lines.append("\n### 상위 키워드")
            keywords = [kw.keyword for kw in nlp.top_keywords[:10]]
            lines.append(f"`{', '.join(keywords)}`")

        # 토픽 클러스터
        if nlp.topic_clusters:
            lines.append("\n### 토픽 클러스터")
            for cluster in nlp.topic_clusters[:5]:
                keywords_str = ", ".join(cluster.keywords[:5])
                lines.append(
                    f"- **클러스터 {cluster.cluster_id}** "
                    f"({cluster.document_count}개 질문): {keywords_str}"
                )

        # NLP 인사이트
        if nlp.insights:
            lines.append("\n### NLP 인사이트")
            for insight in nlp.insights:
                lines.append(f"- {insight}")

        return "\n".join(lines)

    def _generate_causal_section(self, causal: CausalAnalysis) -> str:
        """인과 분석 섹션 생성."""
        lines = ["## 인과 분석"]

        # 유의미한 요인 영향
        significant_impacts = causal.significant_impacts
        if significant_impacts:
            lines.append("\n### 유의미한 요인 영향")
            lines.append("| 요인 | 메트릭 | 방향 | 강도 | 상관계수 |")
            lines.append("|------|--------|------|------|---------|")

            for impact in significant_impacts[:10]:
                direction_symbol = "↑" if impact.direction.value == "positive" else "↓"
                direction_label = "증가" if impact.direction.value == "positive" else "감소"
                lines.append(
                    f"| {impact.factor_type.value} | {impact.metric_name} | "
                    f"{direction_symbol} {direction_label} | {impact.strength.value} | "
                    f"{impact.correlation:.3f} |"
                )

        # 강한 인과 관계
        strong_rels = causal.strong_relationships
        if strong_rels:
            lines.append("\n### 강한 인과 관계")
            for rel in strong_rels[:5]:
                direction = "증가" if rel.direction.value == "positive" else "감소"
                lines.append(
                    f"- **{rel.cause.value}** → **{rel.effect_metric}**: "
                    f"값이 높을수록 점수 {direction} (신뢰도: {rel.confidence:.2f})"
                )

        # 근본 원인 분석
        if causal.root_causes:
            lines.append("\n### 근본 원인 분석")
            for rc in causal.root_causes:
                primary = ", ".join(f.value for f in rc.primary_causes)
                lines.append(f"- **{rc.metric_name}**: 주요 원인 - {primary}")
                if rc.explanation:
                    lines.append(f"  - {rc.explanation}")

        # 개선 제안
        if causal.interventions:
            lines.append("\n### 권장 개입")
            for intervention in causal.interventions[:5]:
                priority_emoji = {1: "🔴", 2: "🟡", 3: "🟢"}.get(intervention.priority, "⚪")
                lines.append(
                    f"- {priority_emoji} **{intervention.target_metric}**: "
                    f"{intervention.intervention}"
                )
                lines.append(f"  - 기대 효과: {intervention.expected_impact}")

        # 인과 분석 인사이트
        if causal.insights:
            lines.append("\n### 인과 인사이트")
            for insight in causal.insights:
                lines.append(f"- {insight}")

        return "\n".join(lines)

    def _generate_recommendations(self, bundle: AnalysisBundle) -> str:
        """권장사항 섹션 생성."""
        lines = ["## 권장사항"]
        recommendations = []

        if bundle.statistical:
            stat = bundle.statistical

            # Pass rate 기반 권장사항
            if stat.overall_pass_rate < 0.5:
                recommendations.append(
                    "**중요:** 전체 통과율이 50% 미만입니다. "
                    "평가 파이프라인과 데이터 품질을 점검하세요."
                )
            elif stat.overall_pass_rate < 0.7:
                recommendations.append(
                    "**경고:** 통과율이 70% 미만입니다. 성능이 낮은 메트릭 개선에 집중하세요."
                )

            # 낮은 성능 메트릭 권장사항
            for metric, rate in stat.metric_pass_rates.items():
                if rate < 0.6:
                    recommendations.append(
                        f"**{metric} 개선:** 통과율이 {rate:.1%}입니다. "
                        "컨텍스트 품질과 답변 생성 품질을 점검하세요."
                    )

            # 낮은 성능 케이스 권장사항
            if len(stat.low_performers) > 5:
                recommendations.append(
                    f"**저성능 케이스 점검:** {len(stat.low_performers)}건이 "
                    "저조합니다. 프롬프트 조정 또는 재학습을 고려하세요."
                )

        if bundle.has_nlp and bundle.nlp:
            nlp = bundle.nlp

            # 어휘 다양성 권장사항
            if nlp.question_stats and nlp.question_stats.unique_word_ratio < 0.5:
                recommendations.append(
                    "**어휘 다양성이 낮음:** "
                    "질문이 반복적일 수 있습니다. 테스트 케이스를 다양화하세요."
                )

        if not recommendations:
            recommendations.append("중요 이슈가 없습니다. 메트릭을 계속 모니터링하세요.")

        for rec in recommendations:
            lines.append(f"\n> {rec}")

        return "\n".join(lines)

    def _generate_footer(self) -> str:
        """푸터 생성."""
        return f"""---

*EvalVault가 생성한 리포트: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*"""

    def _markdown_to_html(self, markdown: str) -> str:
        """간단한 Markdown to HTML 변환."""
        import re

        html = markdown

        # Headers
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)

        # Bold
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)

        # Code
        html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)

        # Tables
        lines = html.split("\n")
        in_table = False
        new_lines = []

        for line in lines:
            if line.startswith("|") and not in_table:
                in_table = True
                new_lines.append("<table>")

            if in_table:
                if not line.startswith("|"):
                    in_table = False
                    new_lines.append("</table>")
                    new_lines.append(line)
                elif line.startswith("|---"):
                    continue  # Skip separator
                else:
                    cells = [c.strip() for c in line.split("|")[1:-1]]
                    if new_lines[-1] == "<table>":
                        row = "<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>"
                    else:
                        row = "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"
                    new_lines.append(row)
            else:
                new_lines.append(line)

        if in_table:
            new_lines.append("</table>")

        html = "\n".join(new_lines)

        # Lists
        html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)

        # Blockquotes (recommendations)
        html = re.sub(
            r"^> (.+)$", r'<div class="recommendation">\1</div>', html, flags=re.MULTILINE
        )

        # Line breaks for paragraphs
        html = re.sub(r"\n\n", r"</p><p>", html)
        html = f"<p>{html}</p>"

        # Clean up empty paragraphs
        html = re.sub(r"<p>\s*</p>", "", html)
        html = re.sub(r"<p>(<h[123]>)", r"\1", html)
        html = re.sub(r"(</h[123]>)</p>", r"\1", html)
        html = re.sub(r"<p>(<table>)", r"\1", html)
        html = re.sub(r"(</table>)</p>", r"\1", html)

        return html
