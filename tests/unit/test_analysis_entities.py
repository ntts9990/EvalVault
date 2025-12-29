"""Tests for analysis domain entities."""

import pytest

from evalvault.domain.entities.analysis import (
    AnalysisBundle,
    AnalysisType,
    ComparisonResult,
    CorrelationInsight,
    EffectSizeLevel,
    LowPerformerInfo,
    MetaAnalysisResult,
    MetricStats,
    StatisticalAnalysis,
)


class TestMetricStats:
    """MetricStats 엔티티 테스트."""

    def test_create_metric_stats(self):
        """MetricStats 생성 테스트."""
        stats = MetricStats(
            mean=0.75,
            std=0.1,
            min=0.5,
            max=0.95,
            median=0.76,
            percentile_25=0.68,
            percentile_75=0.82,
            count=10,
        )

        assert stats.mean == 0.75
        assert stats.std == 0.1
        assert stats.min == 0.5
        assert stats.max == 0.95
        assert stats.median == 0.76
        assert stats.percentile_25 == 0.68
        assert stats.percentile_75 == 0.82
        assert stats.count == 10

    def test_iqr_property(self):
        """IQR (사분위 범위) 계산 테스트."""
        stats = MetricStats(
            mean=0.75,
            std=0.1,
            min=0.5,
            max=0.95,
            median=0.76,
            percentile_25=0.60,
            percentile_75=0.90,
            count=10,
        )

        assert stats.iqr == pytest.approx(0.30)


class TestCorrelationInsight:
    """CorrelationInsight 엔티티 테스트."""

    def test_create_correlation_insight(self):
        """CorrelationInsight 생성 테스트."""
        insight = CorrelationInsight(
            variable1="faithfulness",
            variable2="answer_relevancy",
            correlation=0.85,
            p_value=0.001,
            is_significant=True,
            interpretation="strong positive correlation",
        )

        assert insight.variable1 == "faithfulness"
        assert insight.variable2 == "answer_relevancy"
        assert insight.correlation == 0.85
        assert insight.p_value == 0.001
        assert insight.is_significant is True

    def test_strength_weak(self):
        """약한 상관관계 강도 테스트."""
        insight = CorrelationInsight(variable1="a", variable2="b", correlation=0.2, p_value=0.05)
        assert insight.strength == "weak"

    def test_strength_moderate(self):
        """중간 상관관계 강도 테스트."""
        insight = CorrelationInsight(variable1="a", variable2="b", correlation=0.5, p_value=0.05)
        assert insight.strength == "moderate"

    def test_strength_strong(self):
        """강한 상관관계 강도 테스트."""
        insight = CorrelationInsight(variable1="a", variable2="b", correlation=0.8, p_value=0.05)
        assert insight.strength == "strong"

    def test_strength_negative(self):
        """음의 상관관계 강도 테스트."""
        insight = CorrelationInsight(variable1="a", variable2="b", correlation=-0.75, p_value=0.05)
        assert insight.strength == "strong"


class TestLowPerformerInfo:
    """LowPerformerInfo 엔티티 테스트."""

    def test_create_low_performer(self):
        """LowPerformerInfo 생성 테스트."""
        info = LowPerformerInfo(
            test_case_id="tc-001",
            metric_name="faithfulness",
            score=0.3,
            threshold=0.7,
            question_preview="What is the insurance coverage?",
            potential_causes=["Answer contains information not in context"],
        )

        assert info.test_case_id == "tc-001"
        assert info.metric_name == "faithfulness"
        assert info.score == 0.3
        assert info.threshold == 0.7
        assert len(info.potential_causes) == 1


class TestComparisonResult:
    """ComparisonResult 엔티티 테스트."""

    def test_from_values_significant(self):
        """유의미한 차이가 있는 ComparisonResult 생성 테스트."""
        result = ComparisonResult.from_values(
            run_id_a="run-001",
            run_id_b="run-002",
            metric="faithfulness",
            mean_a=0.7,
            mean_b=0.9,
            p_value=0.01,
            effect_size=0.85,
        )

        assert result.run_id_a == "run-001"
        assert result.run_id_b == "run-002"
        assert result.metric == "faithfulness"
        assert result.mean_a == 0.7
        assert result.mean_b == 0.9
        assert result.diff == pytest.approx(0.2)
        assert result.diff_percent == pytest.approx(28.57, rel=0.01)
        assert result.is_significant is True
        assert result.effect_level == EffectSizeLevel.LARGE
        assert result.winner == "run-002"

    def test_from_values_not_significant(self):
        """유의미한 차이가 없는 ComparisonResult 생성 테스트."""
        result = ComparisonResult.from_values(
            run_id_a="run-001",
            run_id_b="run-002",
            metric="faithfulness",
            mean_a=0.75,
            mean_b=0.76,
            p_value=0.5,
            effect_size=0.05,
        )

        assert result.is_significant is False
        assert result.effect_level == EffectSizeLevel.NEGLIGIBLE
        assert result.winner is None

    def test_effect_size_levels(self):
        """효과 크기 수준 분류 테스트."""
        # Negligible (< 0.2)
        result = ComparisonResult.from_values("a", "b", "m", 0.5, 0.55, 0.1, 0.15)
        assert result.effect_level == EffectSizeLevel.NEGLIGIBLE

        # Small (0.2 - 0.5)
        result = ComparisonResult.from_values("a", "b", "m", 0.5, 0.6, 0.01, 0.35)
        assert result.effect_level == EffectSizeLevel.SMALL

        # Medium (0.5 - 0.8)
        result = ComparisonResult.from_values("a", "b", "m", 0.5, 0.7, 0.01, 0.65)
        assert result.effect_level == EffectSizeLevel.MEDIUM

        # Large (> 0.8)
        result = ComparisonResult.from_values("a", "b", "m", 0.5, 0.9, 0.01, 0.95)
        assert result.effect_level == EffectSizeLevel.LARGE

    def test_winner_is_lower_run_when_a_is_better(self):
        """run_a가 더 나은 경우 승자 결정 테스트."""
        result = ComparisonResult.from_values(
            run_id_a="run-001",
            run_id_b="run-002",
            metric="faithfulness",
            mean_a=0.9,
            mean_b=0.7,
            p_value=0.01,
            effect_size=-0.85,
        )

        assert result.winner == "run-001"


class TestStatisticalAnalysis:
    """StatisticalAnalysis 엔티티 테스트."""

    def test_create_statistical_analysis(self):
        """StatisticalAnalysis 생성 테스트."""
        analysis = StatisticalAnalysis(
            run_id="run-001",
            metrics_summary={
                "faithfulness": MetricStats(
                    mean=0.8,
                    std=0.1,
                    min=0.6,
                    max=1.0,
                    median=0.82,
                    percentile_25=0.75,
                    percentile_75=0.88,
                    count=10,
                )
            },
            overall_pass_rate=0.85,
            metric_pass_rates={"faithfulness": 0.85},
            insights=["Good overall pass rate"],
        )

        assert analysis.run_id == "run-001"
        assert analysis.analysis_type == AnalysisType.STATISTICAL
        assert "faithfulness" in analysis.metrics_summary
        assert analysis.overall_pass_rate == 0.85

    def test_get_metric_stats(self):
        """메트릭 통계 조회 테스트."""
        stats = MetricStats(
            mean=0.8,
            std=0.1,
            min=0.6,
            max=1.0,
            median=0.82,
            percentile_25=0.75,
            percentile_75=0.88,
            count=10,
        )
        analysis = StatisticalAnalysis(
            run_id="run-001",
            metrics_summary={"faithfulness": stats},
        )

        result = analysis.get_metric_stats("faithfulness")
        assert result is not None
        assert result.mean == 0.8

        result = analysis.get_metric_stats("nonexistent")
        assert result is None

    def test_get_correlation(self):
        """상관계수 조회 테스트."""
        analysis = StatisticalAnalysis(
            run_id="run-001",
            correlation_matrix=[[1.0, 0.8], [0.8, 1.0]],
            correlation_metrics=["faithfulness", "answer_relevancy"],
        )

        corr = analysis.get_correlation("faithfulness", "answer_relevancy")
        assert corr == 0.8

        corr = analysis.get_correlation("answer_relevancy", "faithfulness")
        assert corr == 0.8

        corr = analysis.get_correlation("faithfulness", "nonexistent")
        assert corr is None

    def test_get_correlation_empty(self):
        """빈 상관관계 행렬에서 조회 테스트."""
        analysis = StatisticalAnalysis(run_id="run-001")

        corr = analysis.get_correlation("faithfulness", "answer_relevancy")
        assert corr is None


class TestMetaAnalysisResult:
    """MetaAnalysisResult 엔티티 테스트."""

    def test_create_meta_analysis(self):
        """MetaAnalysisResult 생성 테스트."""
        result = MetaAnalysisResult(
            run_ids=["run-001", "run-002", "run-003"],
            best_runs={"faithfulness": "run-002"},
            worst_runs={"faithfulness": "run-001"},
            overall_ranking=["run-002", "run-003", "run-001"],
            consistency_score=0.85,
            recommendations=["Best overall run: run-002"],
        )

        assert len(result.run_ids) == 3
        assert result.best_runs["faithfulness"] == "run-002"
        assert result.overall_ranking[0] == "run-002"
        assert result.consistency_score == 0.85

    def test_get_comparisons_for_metric(self):
        """특정 메트릭 비교 결과 조회 테스트."""
        comparisons = [
            ComparisonResult.from_values("a", "b", "faithfulness", 0.7, 0.8, 0.05, 0.3),
            ComparisonResult.from_values("a", "b", "answer_relevancy", 0.6, 0.7, 0.05, 0.3),
            ComparisonResult.from_values("a", "c", "faithfulness", 0.7, 0.9, 0.01, 0.5),
        ]

        result = MetaAnalysisResult(
            run_ids=["a", "b", "c"],
            comparisons=comparisons,
        )

        faith_comparisons = result.get_comparisons_for_metric("faithfulness")
        assert len(faith_comparisons) == 2

        relevancy_comparisons = result.get_comparisons_for_metric("answer_relevancy")
        assert len(relevancy_comparisons) == 1


class TestAnalysisBundle:
    """AnalysisBundle 엔티티 테스트."""

    def test_create_bundle(self):
        """AnalysisBundle 생성 테스트."""
        statistical = StatisticalAnalysis(run_id="run-001")
        bundle = AnalysisBundle(
            run_id="run-001",
            statistical=statistical,
        )

        assert bundle.run_id == "run-001"
        assert bundle.has_statistical is True
        assert bundle.has_nlp is False
        assert bundle.has_causal is False

    def test_bundle_properties(self):
        """번들 속성 테스트."""
        bundle = AnalysisBundle(run_id="run-001")

        assert bundle.has_statistical is False
        assert bundle.has_nlp is False
        assert bundle.has_causal is False


class TestAnalysisType:
    """AnalysisType enum 테스트."""

    def test_analysis_types(self):
        """분석 유형 값 테스트."""
        assert AnalysisType.STATISTICAL.value == "statistical"
        assert AnalysisType.NLP.value == "nlp"
        assert AnalysisType.CAUSAL.value == "causal"
        assert AnalysisType.DATA_QUALITY.value == "data_quality"


class TestEffectSizeLevel:
    """EffectSizeLevel enum 테스트."""

    def test_effect_size_levels(self):
        """효과 크기 수준 값 테스트."""
        assert EffectSizeLevel.NEGLIGIBLE.value == "negligible"
        assert EffectSizeLevel.SMALL.value == "small"
        assert EffectSizeLevel.MEDIUM.value == "medium"
        assert EffectSizeLevel.LARGE.value == "large"
