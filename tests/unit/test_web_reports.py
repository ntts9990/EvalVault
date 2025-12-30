"""Unit tests for Web UI Reports page components."""

from __future__ import annotations

from datetime import datetime, timedelta

from evalvault.ports.inbound.web_port import RunSummary


def create_sample_run(
    run_id: str = "run-1",
    dataset_name: str = "test-dataset",
    model_name: str = "gpt-5-nano",
    pass_rate: float = 0.85,
    days_ago: int = 0,
) -> RunSummary:
    """테스트용 RunSummary 생성."""
    started_at = datetime.now() - timedelta(days=days_ago)
    return RunSummary(
        run_id=run_id,
        dataset_name=dataset_name,
        model_name=model_name,
        pass_rate=pass_rate,
        total_test_cases=100,
        started_at=started_at,
        finished_at=started_at + timedelta(minutes=5),
        metrics_evaluated=["faithfulness", "answer_relevancy"],
        total_tokens=1000,
        total_cost_usd=0.10,
    )


class TestReportConfig:
    """ReportConfig 컴포넌트 테스트."""

    def test_config_can_be_imported(self):
        """설정 임포트 확인."""
        from evalvault.adapters.inbound.web.components.reports import ReportConfig

        assert ReportConfig is not None

    def test_create_default_config(self):
        """기본 설정 생성."""
        from evalvault.adapters.inbound.web.components.reports import ReportConfig

        config = ReportConfig()

        assert config.output_format == "markdown"
        assert config.include_summary is True
        assert config.include_metrics_detail is True
        assert config.include_charts is True

    def test_create_custom_config(self):
        """커스텀 설정 생성."""
        from evalvault.adapters.inbound.web.components.reports import ReportConfig

        config = ReportConfig(
            output_format="html",
            include_summary=True,
            include_metrics_detail=False,
            include_charts=True,
            include_nlp_analysis=True,
            include_causal_analysis=False,
        )

        assert config.output_format == "html"
        assert config.include_metrics_detail is False
        assert config.include_nlp_analysis is True
        assert config.include_causal_analysis is False

    def test_config_to_dict(self):
        """설정을 딕셔너리로 변환."""
        from evalvault.adapters.inbound.web.components.reports import ReportConfig

        config = ReportConfig(output_format="html", include_charts=False)
        config_dict = config.to_dict()

        assert config_dict["output_format"] == "html"
        assert config_dict["include_charts"] is False

    def test_config_validation(self):
        """설정 검증."""
        from evalvault.adapters.inbound.web.components.reports import ReportConfig

        config = ReportConfig(output_format="markdown")
        assert config.is_valid() is True

        # Invalid format should still work but is_valid returns False
        config_invalid = ReportConfig(output_format="invalid")
        assert config_invalid.is_valid() is False


class TestReportTemplate:
    """ReportTemplate 컴포넌트 테스트."""

    def test_template_can_be_imported(self):
        """템플릿 임포트 확인."""
        from evalvault.adapters.inbound.web.components.reports import ReportTemplate

        assert ReportTemplate is not None

    def test_available_templates(self):
        """사용 가능한 템플릿 목록."""
        from evalvault.adapters.inbound.web.components.reports import ReportTemplate

        templates = ReportTemplate.list_templates()

        assert len(templates) >= 2
        assert "basic" in templates
        assert "detailed" in templates

    def test_get_template_description(self):
        """템플릿 설명 조회."""
        from evalvault.adapters.inbound.web.components.reports import ReportTemplate

        desc = ReportTemplate.get_description("basic")
        assert desc is not None
        assert len(desc) > 0

    def test_render_basic_template(self):
        """기본 템플릿 렌더링."""
        from evalvault.adapters.inbound.web.components.reports import ReportTemplate

        run = create_sample_run()
        metrics = {"faithfulness": 0.85, "answer_relevancy": 0.90}

        template = ReportTemplate(name="basic")
        content = template.render(run=run, metrics=metrics)

        assert run.dataset_name in content
        assert "faithfulness" in content.lower()

    def test_render_detailed_template(self):
        """상세 템플릿 렌더링."""
        from evalvault.adapters.inbound.web.components.reports import ReportTemplate

        run = create_sample_run()
        metrics = {"faithfulness": 0.85, "answer_relevancy": 0.90}

        template = ReportTemplate(name="detailed")
        content = template.render(run=run, metrics=metrics)

        assert run.dataset_name in content
        assert run.model_name in content


class TestReportGenerator:
    """ReportGenerator 컴포넌트 테스트."""

    def test_generator_can_be_imported(self):
        """생성기 임포트 확인."""
        from evalvault.adapters.inbound.web.components.reports import ReportGenerator

        assert ReportGenerator is not None

    def test_generate_markdown_report(self):
        """마크다운 보고서 생성."""
        from evalvault.adapters.inbound.web.components.reports import (
            ReportConfig,
            ReportGenerator,
        )

        run = create_sample_run()
        metrics = {"faithfulness": 0.85, "answer_relevancy": 0.90}
        config = ReportConfig(output_format="markdown")

        generator = ReportGenerator(config=config)
        report = generator.generate(run=run, metrics=metrics)

        assert report.content is not None
        assert len(report.content) > 0
        assert report.format == "markdown"

    def test_generate_html_report(self):
        """HTML 보고서 생성."""
        from evalvault.adapters.inbound.web.components.reports import (
            ReportConfig,
            ReportGenerator,
        )

        run = create_sample_run()
        metrics = {"faithfulness": 0.85, "answer_relevancy": 0.90}
        config = ReportConfig(output_format="html")

        generator = ReportGenerator(config=config)
        report = generator.generate(run=run, metrics=metrics)

        assert report.content is not None
        assert "<html" in report.content.lower() or "<div" in report.content.lower()
        assert report.format == "html"

    def test_report_includes_summary(self):
        """보고서에 요약 포함."""
        from evalvault.adapters.inbound.web.components.reports import (
            ReportConfig,
            ReportGenerator,
        )

        run = create_sample_run(pass_rate=0.85)
        metrics = {"faithfulness": 0.85}
        config = ReportConfig(include_summary=True)

        generator = ReportGenerator(config=config)
        report = generator.generate(run=run, metrics=metrics)

        # Summary section should include pass rate or key stats
        assert "85" in report.content or "0.85" in report.content

    def test_report_excludes_charts_when_disabled(self):
        """차트 비활성화 시 차트 미포함."""
        from evalvault.adapters.inbound.web.components.reports import (
            ReportConfig,
            ReportGenerator,
        )

        run = create_sample_run()
        metrics = {"faithfulness": 0.85}
        config = ReportConfig(include_charts=False)

        generator = ReportGenerator(config=config)
        report = generator.generate(run=run, metrics=metrics)

        assert report.has_charts is False


class TestReportResult:
    """ReportResult 데이터클래스 테스트."""

    def test_result_can_be_imported(self):
        """결과 임포트 확인."""
        from evalvault.adapters.inbound.web.components.reports import ReportResult

        assert ReportResult is not None

    def test_create_result(self):
        """결과 생성."""
        from evalvault.adapters.inbound.web.components.reports import ReportResult

        result = ReportResult(
            content="# Report",
            format="markdown",
            generated_at=datetime.now(),
        )

        assert result.content == "# Report"
        assert result.format == "markdown"

    def test_result_get_filename(self):
        """파일명 생성."""
        from evalvault.adapters.inbound.web.components.reports import ReportResult

        result = ReportResult(
            content="# Report",
            format="markdown",
            run_id="run-123",
        )

        filename = result.get_filename()
        assert "run-123" in filename
        assert filename.endswith(".md")

    def test_result_get_filename_html(self):
        """HTML 파일명 생성."""
        from evalvault.adapters.inbound.web.components.reports import ReportResult

        result = ReportResult(
            content="<html></html>",
            format="html",
            run_id="run-456",
        )

        filename = result.get_filename()
        assert "run-456" in filename
        assert filename.endswith(".html")

    def test_result_get_mime_type(self):
        """MIME 타입 조회."""
        from evalvault.adapters.inbound.web.components.reports import ReportResult

        md_result = ReportResult(content="", format="markdown")
        assert md_result.get_mime_type() == "text/markdown"

        html_result = ReportResult(content="", format="html")
        assert html_result.get_mime_type() == "text/html"


class TestReportDownloader:
    """ReportDownloader 컴포넌트 테스트."""

    def test_downloader_can_be_imported(self):
        """다운로더 임포트 확인."""
        from evalvault.adapters.inbound.web.components.reports import ReportDownloader

        assert ReportDownloader is not None

    def test_prepare_download_markdown(self):
        """마크다운 다운로드 준비."""
        from evalvault.adapters.inbound.web.components.reports import (
            ReportDownloader,
            ReportResult,
        )

        result = ReportResult(
            content="# Test Report\n\nContent here.",
            format="markdown",
            run_id="run-123",
        )

        downloader = ReportDownloader(result=result)
        download_data = downloader.prepare_download()

        assert download_data["data"] == result.content
        assert download_data["filename"].endswith(".md")
        assert download_data["mime_type"] == "text/markdown"

    def test_prepare_download_html(self):
        """HTML 다운로드 준비."""
        from evalvault.adapters.inbound.web.components.reports import (
            ReportDownloader,
            ReportResult,
        )

        result = ReportResult(
            content="<html><body>Test</body></html>",
            format="html",
            run_id="run-456",
        )

        downloader = ReportDownloader(result=result)
        download_data = downloader.prepare_download()

        assert download_data["data"] == result.content
        assert download_data["filename"].endswith(".html")
        assert download_data["mime_type"] == "text/html"

    def test_get_download_options(self):
        """다운로드 옵션 조회."""
        from evalvault.adapters.inbound.web.components.reports import ReportDownloader

        options = ReportDownloader.get_available_formats()

        assert "markdown" in options
        assert "html" in options


class TestRunSelector:
    """RunSelector 컴포넌트 테스트."""

    def test_selector_can_be_imported(self):
        """선택기 임포트 확인."""
        from evalvault.adapters.inbound.web.components.reports import RunSelector

        assert RunSelector is not None

    def test_format_run_option(self):
        """실행 옵션 포맷."""
        from evalvault.adapters.inbound.web.components.reports import RunSelector

        run = create_sample_run(
            run_id="run-123",
            dataset_name="insurance-qa",
            pass_rate=0.85,
        )

        selector = RunSelector(runs=[run])
        formatted = selector.format_option(run)

        assert "run-123" in formatted
        assert "insurance-qa" in formatted
        assert "85" in formatted  # pass rate

    def test_get_run_by_id(self):
        """ID로 실행 조회."""
        from evalvault.adapters.inbound.web.components.reports import RunSelector

        runs = [
            create_sample_run(run_id="run-1"),
            create_sample_run(run_id="run-2"),
            create_sample_run(run_id="run-3"),
        ]

        selector = RunSelector(runs=runs)
        result = selector.get_by_id("run-2")

        assert result is not None
        assert result.run_id == "run-2"

    def test_get_run_by_id_not_found(self):
        """존재하지 않는 ID 조회."""
        from evalvault.adapters.inbound.web.components.reports import RunSelector

        runs = [create_sample_run(run_id="run-1")]

        selector = RunSelector(runs=runs)
        result = selector.get_by_id("nonexistent")

        assert result is None

    def test_get_options_list(self):
        """옵션 목록 조회."""
        from evalvault.adapters.inbound.web.components.reports import RunSelector

        runs = [
            create_sample_run(run_id="run-1"),
            create_sample_run(run_id="run-2"),
        ]

        selector = RunSelector(runs=runs)
        options = selector.get_options()

        assert len(options) == 2
        assert all("run-" in opt for opt in options)


class TestReportPreview:
    """ReportPreview 컴포넌트 테스트."""

    def test_preview_can_be_imported(self):
        """프리뷰 임포트 확인."""
        from evalvault.adapters.inbound.web.components.reports import ReportPreview

        assert ReportPreview is not None

    def test_preview_markdown(self):
        """마크다운 프리뷰."""
        from evalvault.adapters.inbound.web.components.reports import (
            ReportPreview,
            ReportResult,
        )

        result = ReportResult(
            content="# Test Report\n\n## Summary\n\nTest content.",
            format="markdown",
        )

        preview = ReportPreview(result=result)
        preview_content = preview.get_preview()

        assert preview_content is not None
        assert "Test Report" in preview_content

    def test_preview_html(self):
        """HTML 프리뷰."""
        from evalvault.adapters.inbound.web.components.reports import (
            ReportPreview,
            ReportResult,
        )

        result = ReportResult(
            content="<html><body><h1>Test</h1></body></html>",
            format="html",
        )

        preview = ReportPreview(result=result)
        preview_content = preview.get_preview()

        assert preview_content is not None

    def test_preview_truncation(self):
        """긴 내용 미리보기 잘림."""
        from evalvault.adapters.inbound.web.components.reports import (
            ReportPreview,
            ReportResult,
        )

        long_content = "# Report\n\n" + ("Lorem ipsum. " * 1000)
        result = ReportResult(content=long_content, format="markdown")

        preview = ReportPreview(result=result, max_length=500)
        preview_content = preview.get_preview()

        assert len(preview_content) <= 520  # max_length + some buffer for truncation indicator

    def test_preview_get_stats(self):
        """프리뷰 통계."""
        from evalvault.adapters.inbound.web.components.reports import (
            ReportPreview,
            ReportResult,
        )

        result = ReportResult(
            content="# Report\n\n## Section 1\n\nParagraph here.\n\n## Section 2\n\nMore content.",
            format="markdown",
        )

        preview = ReportPreview(result=result)
        stats = preview.get_stats()

        assert "char_count" in stats
        assert "line_count" in stats
        assert stats["char_count"] > 0
        assert stats["line_count"] > 0
