"""Tests for CausalAnalysisAdapter."""

from __future__ import annotations

import pytest

from evalvault.adapters.outbound.analysis import CausalAnalysisAdapter
from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.entities.analysis import (
    CausalFactorType,
    ImpactDirection,
    ImpactStrength,
)


@pytest.fixture
def sample_run() -> EvaluationRun:
    """Create sample evaluation run with results."""
    results = []
    for i in range(30):
        # Create test data with varying properties
        question = f"This is question number {i} " + ("with extra words " * (i % 5))
        answer = f"Answer {i} " + ("detailed " * (i % 4))
        contexts = [f"Context {i} with some content"] * ((i % 3) + 1)
        ground_truth = f"Ground truth {i}" if i % 2 == 0 else None

        # Create metrics that correlate with test case properties
        # Longer questions tend to have lower scores
        question_length = len(question.split())
        base_score = 0.9 - (question_length / 100)

        metrics = [
            MetricScore(name="faithfulness", score=max(0.3, base_score - 0.1 * (i % 3))),
            MetricScore(name="answer_relevancy", score=max(0.3, base_score - 0.05 * (i % 4))),
            MetricScore(
                name="context_precision", score=max(0.3, base_score + 0.1 * len(contexts) / 3)
            ),
        ]

        results.append(
            TestCaseResult(
                test_case_id=f"tc-{i:03d}",
                metrics=metrics,
                question=question,
                answer=answer,
                contexts=contexts,
                ground_truth=ground_truth,
            )
        )

    return EvaluationRun(
        run_id="run-causal-test",
        dataset_name="causal-test-dataset",
        model_name="gpt-5-nano",
        results=results,
        metrics_evaluated=["faithfulness", "answer_relevancy", "context_precision"],
        thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7, "context_precision": 0.7},
    )


@pytest.fixture
def small_run() -> EvaluationRun:
    """Create a run with too few samples for causal analysis."""
    return EvaluationRun(
        run_id="run-small",
        dataset_name="small-dataset",
        model_name="gpt-5-nano",
        results=[
            TestCaseResult(
                test_case_id="tc-001",
                metrics=[MetricScore(name="faithfulness", score=0.8)],
                question="Simple question",
                answer="Simple answer",
                contexts=["Context 1"],
                ground_truth="Ground truth",
            )
        ],
        metrics_evaluated=["faithfulness"],
        thresholds={"faithfulness": 0.7},
    )


class TestCausalAnalysisAdapter:
    """Tests for CausalAnalysisAdapter."""

    def test_analyze_causality_basic(self, sample_run: EvaluationRun) -> None:
        """Test basic causal analysis."""
        adapter = CausalAnalysisAdapter()

        result = adapter.analyze_causality(sample_run)

        assert result.run_id == sample_run.run_id
        assert len(result.factor_stats) > 0
        assert len(result.factor_impacts) > 0

    def test_analyze_causality_insufficient_samples(self, small_run: EvaluationRun) -> None:
        """Test causal analysis with insufficient samples."""
        adapter = CausalAnalysisAdapter()

        result = adapter.analyze_causality(small_run, min_samples=10)

        assert result.run_id == small_run.run_id
        assert len(result.factor_impacts) == 0
        assert any("Insufficient samples" in insight for insight in result.insights)

    def test_analyze_causality_custom_min_samples(self, sample_run: EvaluationRun) -> None:
        """Test causal analysis with custom min_samples."""
        adapter = CausalAnalysisAdapter()

        result = adapter.analyze_causality(sample_run, min_samples=5)

        assert result.run_id == sample_run.run_id
        assert len(result.factor_impacts) > 0

    def test_factor_stats_extraction(self, sample_run: EvaluationRun) -> None:
        """Test factor statistics extraction."""
        adapter = CausalAnalysisAdapter()

        result = adapter.analyze_causality(sample_run)

        # Check that key factors are extracted
        assert CausalFactorType.QUESTION_LENGTH in result.factor_stats
        assert CausalFactorType.ANSWER_LENGTH in result.factor_stats
        assert CausalFactorType.CONTEXT_COUNT in result.factor_stats

        # Check stats properties
        question_stats = result.factor_stats[CausalFactorType.QUESTION_LENGTH]
        assert question_stats.mean > 0
        assert question_stats.std >= 0
        assert question_stats.min <= question_stats.max

    def test_factor_impacts_structure(self, sample_run: EvaluationRun) -> None:
        """Test factor impact structure."""
        adapter = CausalAnalysisAdapter()

        result = adapter.analyze_causality(sample_run)

        for impact in result.factor_impacts:
            assert impact.factor_type in CausalFactorType
            assert impact.metric_name in sample_run.metrics_evaluated
            assert impact.direction in ImpactDirection
            assert impact.strength in ImpactStrength
            assert -1.0 <= impact.correlation <= 1.0
            assert 0.0 <= impact.p_value <= 1.0

    def test_significant_impacts_filtering(self, sample_run: EvaluationRun) -> None:
        """Test significant impacts property."""
        adapter = CausalAnalysisAdapter()

        result = adapter.analyze_causality(sample_run)

        for impact in result.significant_impacts:
            assert impact.is_significant
            assert impact.p_value < 0.05

    def test_causal_relationships(self, sample_run: EvaluationRun) -> None:
        """Test causal relationship identification."""
        adapter = CausalAnalysisAdapter()

        result = adapter.analyze_causality(sample_run)

        for rel in result.causal_relationships:
            assert rel.cause in CausalFactorType
            assert rel.effect_metric in sample_run.metrics_evaluated
            assert rel.direction in ImpactDirection
            assert 0.0 <= rel.confidence <= 1.0
            assert rel.sample_size == len(sample_run.results)

    def test_strong_relationships_filtering(self, sample_run: EvaluationRun) -> None:
        """Test strong relationships property."""
        adapter = CausalAnalysisAdapter()

        result = adapter.analyze_causality(sample_run)

        for rel in result.strong_relationships:
            assert rel.confidence > 0.7

    def test_root_cause_analysis(self, sample_run: EvaluationRun) -> None:
        """Test root cause analysis."""
        adapter = CausalAnalysisAdapter()

        result = adapter.analyze_causality(sample_run)

        # May or may not have root causes depending on data
        for rc in result.root_causes:
            assert rc.metric_name in sample_run.metrics_evaluated
            assert len(rc.primary_causes) > 0

    def test_intervention_suggestions(self, sample_run: EvaluationRun) -> None:
        """Test intervention suggestions."""
        adapter = CausalAnalysisAdapter()

        result = adapter.analyze_causality(sample_run)

        # May or may not have interventions depending on data
        for intervention in result.interventions:
            assert intervention.target_metric in sample_run.metrics_evaluated
            assert intervention.intervention != ""
            assert intervention.expected_impact != ""
            assert intervention.priority in [1, 2, 3]

    def test_insights_generation(self, sample_run: EvaluationRun) -> None:
        """Test insights generation."""
        adapter = CausalAnalysisAdapter()

        result = adapter.analyze_causality(sample_run)

        # Should always have some insights
        assert len(result.insights) > 0

    def test_get_impacts_for_metric(self, sample_run: EvaluationRun) -> None:
        """Test getting impacts for specific metric."""
        adapter = CausalAnalysisAdapter()

        result = adapter.analyze_causality(sample_run)

        faithfulness_impacts = result.get_impacts_for_metric("faithfulness")

        for impact in faithfulness_impacts:
            assert impact.metric_name == "faithfulness"

    def test_get_impacts_for_factor(self, sample_run: EvaluationRun) -> None:
        """Test getting impacts for specific factor."""
        adapter = CausalAnalysisAdapter()

        result = adapter.analyze_causality(sample_run)

        question_length_impacts = result.get_impacts_for_factor(CausalFactorType.QUESTION_LENGTH)

        for impact in question_length_impacts:
            assert impact.factor_type == CausalFactorType.QUESTION_LENGTH


class TestFactorExtraction:
    """Tests for factor extraction methods."""

    def test_question_complexity_calculation(self) -> None:
        """Test question complexity calculation."""
        adapter = CausalAnalysisAdapter()

        # Simple question
        simple = adapter._calculate_question_complexity("What is the answer?")

        # Complex question
        complex_q = adapter._calculate_question_complexity(
            "What is the relationship between A, B, and C? "
            "How does this affect the overall outcome?"
        )

        assert 0.0 <= simple <= 1.0
        assert 0.0 <= complex_q <= 1.0
        # Complex question should have higher complexity
        assert complex_q >= simple

    def test_keyword_overlap_calculation(self) -> None:
        """Test keyword overlap calculation."""
        adapter = CausalAnalysisAdapter()

        # No contexts
        assert adapter._calculate_keyword_overlap("What is insurance?", None) == 0.0
        assert adapter._calculate_keyword_overlap("What is insurance?", []) == 0.0

        # With matching contexts
        overlap = adapter._calculate_keyword_overlap(
            "What is the insurance coverage amount?",
            ["The insurance policy provides coverage of $1 million."],
        )
        assert overlap > 0.0

        # With non-matching contexts
        low_overlap = adapter._calculate_keyword_overlap(
            "What is the weather today?", ["The insurance policy provides coverage of $1 million."]
        )
        assert low_overlap < overlap


class TestImpactDetermination:
    """Tests for impact direction and strength determination."""

    def test_determine_direction_positive(self) -> None:
        """Test positive direction determination."""
        adapter = CausalAnalysisAdapter()

        direction = adapter._determine_direction(0.5, is_significant=True)
        assert direction == ImpactDirection.POSITIVE

    def test_determine_direction_negative(self) -> None:
        """Test negative direction determination."""
        adapter = CausalAnalysisAdapter()

        direction = adapter._determine_direction(-0.5, is_significant=True)
        assert direction == ImpactDirection.NEGATIVE

    def test_determine_direction_neutral_not_significant(self) -> None:
        """Test neutral direction when not significant."""
        adapter = CausalAnalysisAdapter()

        direction = adapter._determine_direction(0.5, is_significant=False)
        assert direction == ImpactDirection.NEUTRAL

    def test_determine_direction_neutral_low_correlation(self) -> None:
        """Test neutral direction with low correlation."""
        adapter = CausalAnalysisAdapter()

        direction = adapter._determine_direction(0.05, is_significant=True)
        assert direction == ImpactDirection.NEUTRAL

    def test_determine_strength_negligible(self) -> None:
        """Test negligible strength determination."""
        adapter = CausalAnalysisAdapter()

        strength = adapter._determine_strength(0.05)
        assert strength == ImpactStrength.NEGLIGIBLE

    def test_determine_strength_weak(self) -> None:
        """Test weak strength determination."""
        adapter = CausalAnalysisAdapter()

        strength = adapter._determine_strength(0.2)
        assert strength == ImpactStrength.WEAK

    def test_determine_strength_moderate(self) -> None:
        """Test moderate strength determination."""
        adapter = CausalAnalysisAdapter()

        strength = adapter._determine_strength(0.4)
        assert strength == ImpactStrength.MODERATE

    def test_determine_strength_strong(self) -> None:
        """Test strong strength determination."""
        adapter = CausalAnalysisAdapter()

        strength = adapter._determine_strength(0.6)
        assert strength == ImpactStrength.STRONG


class TestInterpretationGeneration:
    """Tests for interpretation generation."""

    def test_generate_interpretation_positive(self) -> None:
        """Test interpretation for positive impact."""
        adapter = CausalAnalysisAdapter()

        interpretation = adapter._generate_interpretation(
            CausalFactorType.QUESTION_LENGTH,
            "faithfulness",
            ImpactDirection.POSITIVE,
            ImpactStrength.MODERATE,
            0.45,
        )

        assert "Question length" in interpretation
        assert "faithfulness" in interpretation
        assert "moderate" in interpretation
        assert "positive" in interpretation

    def test_generate_interpretation_negative(self) -> None:
        """Test interpretation for negative impact."""
        adapter = CausalAnalysisAdapter()

        interpretation = adapter._generate_interpretation(
            CausalFactorType.CONTEXT_COUNT,
            "answer_relevancy",
            ImpactDirection.NEGATIVE,
            ImpactStrength.WEAK,
            -0.25,
        )

        assert "Number of contexts" in interpretation
        assert "answer_relevancy" in interpretation
        assert "weak" in interpretation
        assert "negative" in interpretation

    def test_generate_interpretation_neutral(self) -> None:
        """Test interpretation for neutral impact."""
        adapter = CausalAnalysisAdapter()

        interpretation = adapter._generate_interpretation(
            CausalFactorType.KEYWORD_OVERLAP,
            "context_precision",
            ImpactDirection.NEUTRAL,
            ImpactStrength.NEGLIGIBLE,
            0.02,
        )

        assert "no significant effect" in interpretation


class TestStratifiedAnalysis:
    """Tests for stratified analysis."""

    def test_stratify_analysis_basic(self, sample_run: EvaluationRun) -> None:
        """Test basic stratified analysis."""
        adapter = CausalAnalysisAdapter(num_strata=3, min_group_size=3)

        result = adapter.analyze_causality(sample_run)

        # Find an impact with stratified groups
        for impact in result.factor_impacts:
            if impact.stratified_groups:
                for group in impact.stratified_groups:
                    assert group.group_name in ["low", "medium", "high"]
                    assert group.count >= 3
                    assert group.lower_bound <= group.upper_bound
                    assert impact.metric_name in group.avg_scores
                break
