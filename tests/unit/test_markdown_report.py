"""Tests for MarkdownReportAdapter."""

from __future__ import annotations

import pytest

from evalvault.adapters.outbound.report import MarkdownReportAdapter
from evalvault.domain.entities.analysis import (
    AnalysisBundle,
    CorrelationInsight,
    KeywordInfo,
    LowPerformerInfo,
    MetricStats,
    NLPAnalysis,
    QuestionType,
    QuestionTypeStats,
    StatisticalAnalysis,
    TextStats,
    TopicCluster,
)


@pytest.fixture
def statistical_analysis() -> StatisticalAnalysis:
    """Create sample statistical analysis."""
    return StatisticalAnalysis(
        run_id="run-123",
        overall_pass_rate=0.75,
        metric_pass_rates={
            "faithfulness": 0.8,
            "answer_relevancy": 0.7,
            "context_precision": 0.75,
        },
        metrics_summary={
            "faithfulness": MetricStats(
                mean=0.82,
                std=0.1,
                min=0.5,
                max=1.0,
                median=0.85,
                percentile_25=0.7,
                percentile_75=0.9,
                count=100,
            ),
            "answer_relevancy": MetricStats(
                mean=0.72,
                std=0.15,
                min=0.3,
                max=0.95,
                median=0.75,
                percentile_25=0.6,
                percentile_75=0.85,
                count=100,
            ),
        },
        significant_correlations=[
            CorrelationInsight(
                variable1="faithfulness",
                variable2="answer_relevancy",
                correlation=0.65,
                p_value=0.01,
                is_significant=True,
            ),
        ],
        low_performers=[
            LowPerformerInfo(
                test_case_id="tc-001",
                metric_name="context_precision",
                score=0.45,
                threshold=0.7,
                question_preview="What is the coverage amount for this insurance policy?",
            ),
            LowPerformerInfo(
                test_case_id="tc-002",
                metric_name="faithfulness",
                score=0.35,
                threshold=0.7,
                question_preview="How do I file a claim?",
            ),
        ],
        insights=[
            "Overall pass rate is above threshold",
            "Strong correlation between faithfulness and answer_relevancy",
        ],
    )


@pytest.fixture
def nlp_analysis() -> NLPAnalysis:
    """Create sample NLP analysis."""
    return NLPAnalysis(
        run_id="run-123",
        question_stats=TextStats(
            char_count=2500,
            word_count=500,
            sentence_count=100,
            avg_word_length=5.2,
            unique_word_ratio=0.65,
        ),
        answer_stats=TextStats(
            char_count=7500,
            word_count=1500,
            sentence_count=200,
            avg_word_length=5.5,
            unique_word_ratio=0.55,
        ),
        question_types=[
            QuestionTypeStats(
                question_type=QuestionType.FACTUAL,
                count=40,
                percentage=0.4,
            ),
            QuestionTypeStats(
                question_type=QuestionType.REASONING,
                count=30,
                percentage=0.3,
            ),
            QuestionTypeStats(
                question_type=QuestionType.OPINION,
                count=30,
                percentage=0.3,
            ),
        ],
        top_keywords=[
            KeywordInfo(keyword="insurance", frequency=50, tfidf_score=0.8),
            KeywordInfo(keyword="coverage", frequency=30, tfidf_score=0.7),
            KeywordInfo(keyword="claim", frequency=25, tfidf_score=0.65),
        ],
        topic_clusters=[
            TopicCluster(
                cluster_id=0,
                keywords=["insurance", "coverage", "policy"],
                document_count=40,
            ),
            TopicCluster(
                cluster_id=1,
                keywords=["claim", "process", "file"],
                document_count=35,
            ),
        ],
        insights=[
            "Questions are predominantly FACTUAL type",
            "High vocabulary diversity in questions",
        ],
    )


@pytest.fixture
def analysis_bundle(
    statistical_analysis: StatisticalAnalysis,
    nlp_analysis: NLPAnalysis,
) -> AnalysisBundle:
    """Create sample analysis bundle."""
    return AnalysisBundle(
        run_id="run-123",
        statistical=statistical_analysis,
        nlp=nlp_analysis,
    )


@pytest.fixture
def bundle_without_nlp(
    statistical_analysis: StatisticalAnalysis,
) -> AnalysisBundle:
    """Create analysis bundle without NLP."""
    return AnalysisBundle(
        run_id="run-456",
        statistical=statistical_analysis,
        nlp=None,
    )


class TestMarkdownReportAdapter:
    """Tests for MarkdownReportAdapter."""

    def test_generate_markdown_full_report(self, analysis_bundle: AnalysisBundle) -> None:
        """Test generating full markdown report with all sections."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_markdown(analysis_bundle)

        # Check header
        assert "# EvalVault 분석 리포트" in result
        assert "run-123" in result

        # Check summary
        assert "## 요약" in result
        assert "75.0%" in result  # pass rate

        # Check statistical section
        assert "## 통계 분석" in result
        assert "faithfulness" in result
        assert "answer_relevancy" in result

        # Check NLP section
        assert "## NLP 분석" in result
        assert "500" in result  # word count
        assert "insurance" in result  # keyword

        # Check recommendations
        assert "## 권장사항" in result

    def test_generate_markdown_without_nlp(self, bundle_without_nlp: AnalysisBundle) -> None:
        """Test generating markdown report without NLP section."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_markdown(bundle_without_nlp)

        assert "## 통계 분석" in result
        assert "## NLP 분석" not in result

    def test_generate_markdown_exclude_nlp(self, analysis_bundle: AnalysisBundle) -> None:
        """Test excluding NLP section via parameter."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_markdown(analysis_bundle, include_nlp=False)

        assert "## 통계 분석" in result
        assert "## NLP 분석" not in result

    def test_generate_markdown_exclude_recommendations(
        self, analysis_bundle: AnalysisBundle
    ) -> None:
        """Test excluding recommendations section."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_markdown(analysis_bundle, include_recommendations=False)

        assert "## 통계 분석" in result
        assert "## 권장사항" not in result

    def test_generate_markdown_metric_pass_rates_table(
        self, analysis_bundle: AnalysisBundle
    ) -> None:
        """Test metric pass rates table generation."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_markdown(analysis_bundle)

        assert "| 메트릭 | 통과율 |" in result
        assert "| faithfulness | 80.0% |" in result
        assert "| answer_relevancy | 70.0% |" in result

    def test_generate_markdown_correlations(self, analysis_bundle: AnalysisBundle) -> None:
        """Test significant correlations section."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_markdown(analysis_bundle)

        assert "### 유의미한 상관관계" in result
        assert "faithfulness" in result
        assert "answer_relevancy" in result
        assert "0.65" in result

    def test_generate_markdown_low_performers(self, analysis_bundle: AnalysisBundle) -> None:
        """Test low performers section."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_markdown(analysis_bundle)

        assert "### 낮은 성능 케이스" in result
        assert "tc-001" in result
        assert "tc-002" in result

    def test_generate_markdown_nlp_question_types(self, analysis_bundle: AnalysisBundle) -> None:
        """Test NLP question type distribution."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_markdown(analysis_bundle)

        assert "### 질문 유형 분포" in result
        assert "Factual" in result
        assert "Reasoning" in result

    def test_generate_markdown_nlp_keywords(self, analysis_bundle: AnalysisBundle) -> None:
        """Test NLP top keywords section."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_markdown(analysis_bundle)

        assert "### 상위 키워드" in result
        assert "insurance" in result
        assert "coverage" in result

    def test_generate_markdown_topic_clusters(self, analysis_bundle: AnalysisBundle) -> None:
        """Test NLP topic clusters section."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_markdown(analysis_bundle)

        assert "### 토픽 클러스터" in result
        assert "클러스터 0" in result
        assert "클러스터 1" in result


class TestMarkdownReportAdapterHTML:
    """Tests for HTML report generation."""

    def test_generate_html_structure(self, analysis_bundle: AnalysisBundle) -> None:
        """Test HTML report has proper structure."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_html(analysis_bundle)

        assert "<!DOCTYPE html>" in result
        assert '<html lang="ko">' in result
        assert "<head>" in result
        assert "<body>" in result
        assert "</html>" in result

    def test_generate_html_title(self, analysis_bundle: AnalysisBundle) -> None:
        """Test HTML report title contains run ID."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_html(analysis_bundle)

        assert "<title>EvalVault 분석 리포트 - run-123</title>" in result

    def test_generate_html_styles(self, analysis_bundle: AnalysisBundle) -> None:
        """Test HTML report includes CSS styles."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_html(analysis_bundle)

        assert "<style>" in result
        assert "font-family" in result
        assert ".pass" in result
        assert ".fail" in result

    def test_generate_html_headers_converted(self, analysis_bundle: AnalysisBundle) -> None:
        """Test markdown headers converted to HTML."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_html(analysis_bundle)

        assert "<h1>EvalVault 분석 리포트</h1>" in result
        assert "<h2>요약</h2>" in result

    def test_generate_html_tables_converted(self, analysis_bundle: AnalysisBundle) -> None:
        """Test markdown tables converted to HTML."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_html(analysis_bundle)

        assert "<table>" in result
        assert "<th>" in result
        assert "<td>" in result

    def test_generate_html_bold_converted(self, analysis_bundle: AnalysisBundle) -> None:
        """Test bold text converted to HTML."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_html(analysis_bundle)

        assert "<strong>" in result

    def test_generate_html_code_converted(self, analysis_bundle: AnalysisBundle) -> None:
        """Test code converted to HTML."""
        adapter = MarkdownReportAdapter()

        result = adapter.generate_html(analysis_bundle)

        assert "<code>" in result


class TestMarkdownReportAdapterRecommendations:
    """Tests for recommendations generation."""

    def test_critical_recommendation_low_pass_rate(self) -> None:
        """Test critical recommendation for very low pass rate."""
        adapter = MarkdownReportAdapter()
        bundle = AnalysisBundle(
            run_id="run-low",
            statistical=StatisticalAnalysis(
                run_id="run-low",
                overall_pass_rate=0.4,
                metric_pass_rates={"faithfulness": 0.4},
            ),
            nlp=None,
        )

        result = adapter.generate_markdown(bundle)

        assert "**중요:**" in result
        assert "50% 미만" in result

    def test_warning_recommendation_medium_pass_rate(self) -> None:
        """Test warning recommendation for medium pass rate."""
        adapter = MarkdownReportAdapter()
        bundle = AnalysisBundle(
            run_id="run-medium",
            statistical=StatisticalAnalysis(
                run_id="run-medium",
                overall_pass_rate=0.6,
                metric_pass_rates={"faithfulness": 0.8},
            ),
            nlp=None,
        )

        result = adapter.generate_markdown(bundle)

        assert "**경고:**" in result
        assert "70% 미만" in result

    def test_metric_improvement_recommendation(self) -> None:
        """Test recommendation for low-performing metric."""
        adapter = MarkdownReportAdapter()
        bundle = AnalysisBundle(
            run_id="run-metric",
            statistical=StatisticalAnalysis(
                run_id="run-metric",
                overall_pass_rate=0.8,
                metric_pass_rates={
                    "faithfulness": 0.9,
                    "answer_relevancy": 0.5,  # Low
                },
            ),
            nlp=None,
        )

        result = adapter.generate_markdown(bundle)

        assert "**answer_relevancy 개선:**" in result
        assert "50.0%" in result

    def test_low_performers_recommendation(self) -> None:
        """Test recommendation when many low performers."""
        adapter = MarkdownReportAdapter()
        low_performers = [
            LowPerformerInfo(
                test_case_id=f"tc-{i:03d}",
                metric_name="faithfulness",
                score=0.3,
                threshold=0.7,
                question_preview=f"Question {i}",
            )
            for i in range(10)
        ]
        bundle = AnalysisBundle(
            run_id="run-lp",
            statistical=StatisticalAnalysis(
                run_id="run-lp",
                overall_pass_rate=0.8,
                metric_pass_rates={"faithfulness": 0.9},
                low_performers=low_performers,
            ),
            nlp=None,
        )

        result = adapter.generate_markdown(bundle)

        assert "**저성능 케이스 점검:**" in result
        assert "10건" in result

    def test_no_issues_recommendation(self) -> None:
        """Test default recommendation when no issues."""
        adapter = MarkdownReportAdapter()
        bundle = AnalysisBundle(
            run_id="run-good",
            statistical=StatisticalAnalysis(
                run_id="run-good",
                overall_pass_rate=0.9,
                metric_pass_rates={"faithfulness": 0.95},
            ),
            nlp=None,
        )

        result = adapter.generate_markdown(bundle)

        assert "중요 이슈가 없습니다" in result

    def test_vocabulary_diversity_recommendation(self) -> None:
        """Test recommendation for low vocabulary diversity."""
        adapter = MarkdownReportAdapter()
        bundle = AnalysisBundle(
            run_id="run-vocab",
            statistical=StatisticalAnalysis(
                run_id="run-vocab",
                overall_pass_rate=0.9,
                metric_pass_rates={"faithfulness": 0.95},
            ),
            nlp=NLPAnalysis(
                run_id="run-vocab",
                question_stats=TextStats(
                    char_count=2500,
                    word_count=500,
                    sentence_count=100,
                    avg_word_length=5.0,
                    unique_word_ratio=0.3,  # Low diversity
                ),
            ),
        )

        result = adapter.generate_markdown(bundle)

        assert "**어휘 다양성이 낮음:**" in result
