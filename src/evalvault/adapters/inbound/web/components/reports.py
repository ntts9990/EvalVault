"""Reports page components."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from evalvault.ports.inbound.web_port import RunSummary


VALID_FORMATS = {"markdown", "html"}

TEMPLATE_DESCRIPTIONS = {
    "basic": "기본 보고서 - 핵심 메트릭과 요약만 포함",
    "detailed": "상세 보고서 - 모든 메트릭, 분석, 권장사항 포함",
    "comparison": "비교 보고서 - 여러 실행 결과 비교 (준비 중)",
}


@dataclass
class ReportConfig:
    """보고서 생성 설정.

    보고서 생성 시 사용할 옵션들을 정의합니다.
    """

    output_format: Literal["markdown", "html"] = "markdown"
    include_summary: bool = True
    include_metrics_detail: bool = True
    include_charts: bool = True
    include_nlp_analysis: bool = False
    include_causal_analysis: bool = False
    template_name: str = "basic"

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환.

        Returns:
            설정 딕셔너리
        """
        return {
            "output_format": self.output_format,
            "include_summary": self.include_summary,
            "include_metrics_detail": self.include_metrics_detail,
            "include_charts": self.include_charts,
            "include_nlp_analysis": self.include_nlp_analysis,
            "include_causal_analysis": self.include_causal_analysis,
            "template_name": self.template_name,
        }

    def is_valid(self) -> bool:
        """설정 유효성 검사.

        Returns:
            유효하면 True
        """
        return self.output_format in VALID_FORMATS


@dataclass
class ReportResult:
    """보고서 생성 결과.

    생성된 보고서 내용과 메타데이터를 포함합니다.
    """

    content: str
    format: Literal["markdown", "html"] = "markdown"
    run_id: str | None = None
    generated_at: datetime | None = None
    has_charts: bool = False

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()

    def get_filename(self) -> str:
        """파일명 생성.

        Returns:
            권장 파일명
        """
        run_part = self.run_id or "report"
        timestamp = self.generated_at.strftime("%Y%m%d_%H%M%S") if self.generated_at else ""
        extension = ".md" if self.format == "markdown" else ".html"
        return f"{run_part}_{timestamp}{extension}"

    def get_mime_type(self) -> str:
        """MIME 타입 조회.

        Returns:
            MIME 타입 문자열
        """
        if self.format == "markdown":
            return "text/markdown"
        return "text/html"


@dataclass
class ReportTemplate:
    """보고서 템플릿.

    보고서 렌더링에 사용할 템플릿을 정의합니다.
    """

    name: str = "basic"

    @staticmethod
    def list_templates() -> list[str]:
        """사용 가능한 템플릿 목록.

        Returns:
            템플릿 이름 목록
        """
        return list(TEMPLATE_DESCRIPTIONS.keys())

    @staticmethod
    def get_description(name: str) -> str | None:
        """템플릿 설명 조회.

        Args:
            name: 템플릿 이름

        Returns:
            템플릿 설명
        """
        return TEMPLATE_DESCRIPTIONS.get(name)

    def render(
        self,
        run: RunSummary,
        metrics: dict[str, float],
        *,
        include_charts: bool = False,
    ) -> str:
        """템플릿 렌더링.

        Args:
            run: 평가 실행 요약
            metrics: 메트릭 점수
            include_charts: 차트 포함 여부

        Returns:
            렌더링된 보고서 문자열
        """
        if self.name == "detailed":
            return self._render_detailed(run, metrics, include_charts)
        return self._render_basic(run, metrics)

    def _render_basic(self, run: RunSummary, metrics: dict[str, float]) -> str:
        """기본 템플릿 렌더링."""
        lines = [
            f"# 평가 보고서: {run.dataset_name}",
            "",
            "## 요약",
            "",
            f"- **실행 ID**: {run.run_id}",
            f"- **모델**: {run.model_name}",
            f"- **통과율**: {run.pass_rate:.1%}",
            f"- **테스트 케이스**: {run.total_test_cases}개",
            "",
            "## 메트릭 결과",
            "",
        ]

        for metric_name, score in metrics.items():
            lines.append(f"- **{metric_name}**: {score:.3f}")

        lines.append("")
        lines.append(f"*생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)

    def _render_detailed(
        self,
        run: RunSummary,
        metrics: dict[str, float],
        include_charts: bool,
    ) -> str:
        """상세 템플릿 렌더링."""
        duration = ""
        if run.finished_at and run.started_at:
            seconds = (run.finished_at - run.started_at).total_seconds()
            duration = f"{seconds:.1f}초"

        lines = [
            f"# 상세 평가 보고서: {run.dataset_name}",
            "",
            "## 1. 실행 정보",
            "",
            "| 항목 | 값 |",
            "|------|-----|",
            f"| 실행 ID | {run.run_id} |",
            f"| 데이터셋 | {run.dataset_name} |",
            f"| 모델 | {run.model_name} |",
            f"| 시작 시간 | {run.started_at.strftime('%Y-%m-%d %H:%M:%S') if run.started_at else 'N/A'} |",
            f"| 종료 시간 | {run.finished_at.strftime('%Y-%m-%d %H:%M:%S') if run.finished_at else 'N/A'} |",
            f"| 소요 시간 | {duration or 'N/A'} |",
            "",
            "## 2. 성능 요약",
            "",
            f"- **통과율**: {run.pass_rate:.1%}",
            f"- **총 테스트 케이스**: {run.total_test_cases}개",
            f"- **총 토큰 사용량**: {run.total_tokens:,}",
            f"- **총 비용**: ${run.total_cost_usd:.4f}"
            if run.total_cost_usd
            else "- **총 비용**: N/A",
            "",
            "## 3. 메트릭 상세",
            "",
            "| 메트릭 | 점수 | 상태 |",
            "|--------|------|------|",
        ]

        for metric_name, score in metrics.items():
            status = "✅ 양호" if score >= 0.7 else "⚠️ 개선 필요" if score >= 0.5 else "❌ 주의"
            lines.append(f"| {metric_name} | {score:.3f} | {status} |")

        lines.extend(
            [
                "",
                "## 4. 권장사항",
                "",
            ]
        )

        # 낮은 메트릭에 대한 권장사항
        low_metrics = [m for m, s in metrics.items() if s < 0.7]
        if low_metrics:
            lines.append("다음 메트릭의 개선이 필요합니다:")
            lines.append("")
            for metric in low_metrics:
                lines.append(f"- **{metric}**: 관련 로직 검토 필요")
        else:
            lines.append("모든 메트릭이 기준치를 충족합니다.")

        lines.extend(
            [
                "",
                "---",
                f"*보고서 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ]
        )

        return "\n".join(lines)


@dataclass
class ReportGenerator:
    """보고서 생성기.

    설정에 따라 보고서를 생성합니다.
    """

    config: ReportConfig = field(default_factory=ReportConfig)

    def generate(
        self,
        run: RunSummary,
        metrics: dict[str, float],
    ) -> ReportResult:
        """보고서 생성.

        Args:
            run: 평가 실행 요약
            metrics: 메트릭 점수

        Returns:
            생성된 보고서 결과
        """
        template = ReportTemplate(name=self.config.template_name)
        content = template.render(
            run=run,
            metrics=metrics,
            include_charts=self.config.include_charts,
        )

        # HTML 포맷인 경우 변환
        if self.config.output_format == "html":
            content = self._convert_to_html(content, run)

        return ReportResult(
            content=content,
            format=self.config.output_format,
            run_id=run.run_id,
            has_charts=self.config.include_charts,
        )

    def _convert_to_html(self, markdown_content: str, run: RunSummary) -> str:
        """마크다운을 HTML로 변환.

        Args:
            markdown_content: 마크다운 콘텐츠
            run: 평가 실행 요약

        Returns:
            HTML 문자열
        """
        # 간단한 마크다운 -> HTML 변환
        html_content = markdown_content

        # 제목 변환
        lines = html_content.split("\n")
        converted_lines = []

        for line in lines:
            if line.startswith("# "):
                converted_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                converted_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                converted_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("- "):
                converted_lines.append(f"<li>{line[2:]}</li>")
            elif line.startswith("| "):
                # 테이블 행
                cells = [c.strip() for c in line.split("|")[1:-1]]
                row = "".join(f"<td>{c}</td>" for c in cells)
                converted_lines.append(f"<tr>{row}</tr>")
            elif line.startswith("|---"):
                continue  # 테이블 구분선 스킵
            elif line.strip():
                converted_lines.append(f"<p>{line}</p>")
            else:
                converted_lines.append("")

        body = "\n".join(converted_lines)

        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>평가 보고서: {run.dataset_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        td, th {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        li {{ margin: 5px 0; }}
    </style>
</head>
<body>
{body}
</body>
</html>"""


@dataclass
class ReportDownloader:
    """보고서 다운로더.

    보고서를 다운로드 가능한 형태로 준비합니다.
    """

    result: ReportResult

    @staticmethod
    def get_available_formats() -> list[str]:
        """사용 가능한 포맷 목록.

        Returns:
            포맷 이름 목록
        """
        return list(VALID_FORMATS)

    def prepare_download(self) -> dict[str, Any]:
        """다운로드 준비.

        Returns:
            다운로드에 필요한 데이터
        """
        return {
            "data": self.result.content,
            "filename": self.result.get_filename(),
            "mime_type": self.result.get_mime_type(),
        }


@dataclass
class RunSelector:
    """실행 선택기.

    보고서 생성 대상 실행을 선택하는 컴포넌트입니다.
    """

    runs: list[RunSummary] = field(default_factory=list)

    def format_option(self, run: RunSummary) -> str:
        """실행 옵션 포맷.

        Args:
            run: 평가 실행 요약

        Returns:
            포맷된 옵션 문자열
        """
        pass_rate_pct = int(run.pass_rate * 100)
        date_str = run.started_at.strftime("%Y-%m-%d") if run.started_at else "N/A"
        return f"{run.run_id} | {run.dataset_name} | {pass_rate_pct}% | {date_str}"

    def get_by_id(self, run_id: str) -> RunSummary | None:
        """ID로 실행 조회.

        Args:
            run_id: 실행 ID

        Returns:
            실행 요약 또는 None
        """
        for run in self.runs:
            if run.run_id == run_id:
                return run
        return None

    def get_options(self) -> list[str]:
        """옵션 목록 조회.

        Returns:
            포맷된 옵션 목록
        """
        return [self.format_option(run) for run in self.runs]


@dataclass
class ReportPreview:
    """보고서 미리보기.

    생성된 보고서의 미리보기를 제공합니다.
    """

    result: ReportResult
    max_length: int = 5000

    def get_preview(self) -> str:
        """미리보기 콘텐츠.

        Returns:
            미리보기 문자열
        """
        content = self.result.content

        if len(content) > self.max_length:
            return content[: self.max_length] + "\n\n... (내용 생략)"

        return content

    def get_stats(self) -> dict[str, int]:
        """콘텐츠 통계.

        Returns:
            통계 딕셔너리
        """
        content = self.result.content
        return {
            "char_count": len(content),
            "line_count": content.count("\n") + 1,
            "word_count": len(content.split()),
        }
