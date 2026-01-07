"""Tests for Statistical Analysis Adapter."""

from datetime import datetime

import pytest

from evalvault.adapters.outbound.analysis.statistical_adapter import (
    StatisticalAnalysisAdapter,
)
from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult


class TestStatisticalAnalysisAdapter:
    """StatisticalAnalysisAdapter 테스트."""

    @pytest.fixture
    def adapter(self):
        """어댑터 인스턴스."""
        return StatisticalAnalysisAdapter()

    @pytest.fixture
    def sample_run(self):
        """테스트용 샘플 EvaluationRun."""
        results = [
            TestCaseResult(
                test_case_id="tc-001",
                question="What is the coverage amount?",
                metrics=[
                    MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.85, threshold=0.7),
                ],
            ),
            TestCaseResult(
                test_case_id="tc-002",
                question="What are the exclusions?",
                metrics=[
                    MetricScore(name="faithfulness", score=0.75, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.6, threshold=0.7),
                ],
            ),
            TestCaseResult(
                test_case_id="tc-003",
                question="How to file a claim?",
                metrics=[
                    MetricScore(name="faithfulness", score=0.4, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.8, threshold=0.7),
                ],
            ),
        ]

        return EvaluationRun(
            run_id="run-001",
            dataset_name="test-dataset",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=results,
            metrics_evaluated=["faithfulness", "answer_relevancy"],
            thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7},
        )

    @pytest.fixture
    def empty_run(self):
        """빈 결과의 EvaluationRun."""
        return EvaluationRun(
            run_id="run-empty",
            dataset_name="empty-dataset",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=[],
            metrics_evaluated=[],
        )

    def test_analyze_statistics_basic(self, adapter, sample_run):
        """기본 통계 분석 테스트."""
        result = adapter.analyze_statistics(sample_run)

        assert result.run_id == "run-001"
        assert "faithfulness" in result.metrics_summary
        assert "answer_relevancy" in result.metrics_summary

        # 메트릭 통계 확인
        faith_stats = result.metrics_summary["faithfulness"]
        assert faith_stats.count == 3
        assert faith_stats.mean == pytest.approx((0.9 + 0.75 + 0.4) / 3)
        assert faith_stats.min == 0.4
        assert faith_stats.max == 0.9

    def test_analyze_statistics_empty_run(self, adapter, empty_run):
        """빈 실행 분석 테스트."""
        result = adapter.analyze_statistics(empty_run)

        assert result.run_id == "run-empty"
        assert len(result.metrics_summary) == 0
        assert "No test cases to analyze" in result.insights

    def test_analyze_statistics_with_correlations(self, adapter, sample_run):
        """상관관계 분석 포함 테스트."""
        result = adapter.analyze_statistics(sample_run, include_correlations=True)

        assert len(result.correlation_matrix) == 2
        assert len(result.correlation_metrics) == 2
        assert result.correlation_matrix[0][0] == 1.0  # 자기 상관

    def test_analyze_statistics_without_correlations(self, adapter, sample_run):
        """상관관계 분석 제외 테스트."""
        result = adapter.analyze_statistics(sample_run, include_correlations=False)

        assert len(result.correlation_matrix) == 0
        assert len(result.significant_correlations) == 0

    def test_analyze_statistics_low_performers(self, adapter, sample_run):
        """낮은 성능 케이스 분석 테스트."""
        result = adapter.analyze_statistics(
            sample_run,
            include_low_performers=True,
            low_performer_threshold=0.7,
        )

        # tc-002의 answer_relevancy(0.6)와 tc-003의 faithfulness(0.4)가 해당
        low_performers = result.low_performers
        assert len(low_performers) >= 2

        # 가장 낮은 점수가 먼저 오는지 확인
        assert low_performers[0].score <= low_performers[-1].score

    def test_analyze_statistics_without_low_performers(self, adapter, sample_run):
        """낮은 성능 분석 제외 테스트."""
        result = adapter.analyze_statistics(
            sample_run,
            include_low_performers=False,
        )

        assert len(result.low_performers) == 0

    def test_analyze_statistics_pass_rates(self, adapter, sample_run):
        """Pass rate 분석 테스트."""
        result = adapter.analyze_statistics(sample_run)

        # faithfulness: 2/3 passed, answer_relevancy: 2/3 passed
        assert result.metric_pass_rates["faithfulness"] == pytest.approx(2 / 3)
        assert result.metric_pass_rates["answer_relevancy"] == pytest.approx(2 / 3)

    def test_analyze_statistics_insights(self, adapter, sample_run):
        """인사이트 생성 테스트."""
        result = adapter.analyze_statistics(sample_run)

        assert len(result.insights) > 0
        # Pass rate 관련 인사이트가 있어야 함
        pass_rate_insights = [i for i in result.insights if "pass rate" in i.lower()]
        assert len(pass_rate_insights) > 0

    def test_infer_causes_summary_metrics(self, adapter):
        """요약 메트릭 원인 추론 테스트."""
        causes = adapter._infer_causes("summary_faithfulness", 0.2)
        assert "Summary contains unsupported statements" in causes
        assert "Possible hallucination in summary" in causes

        causes = adapter._infer_causes("summary_score", 0.2)
        assert "Summary misses key information from context" in causes

        causes = adapter._infer_causes("entity_preservation", 0.2)
        assert "Critical entities are missing or altered in summary" in causes


class TestStatisticalAdapterComparison:
    """두 실행 비교 테스트."""

    @pytest.fixture
    def adapter(self):
        return StatisticalAnalysisAdapter()

    @pytest.fixture
    def run_a(self):
        """첫 번째 실행 (낮은 점수)."""
        results = [
            TestCaseResult(
                test_case_id=f"tc-{i:03d}",
                metrics=[
                    MetricScore(name="faithfulness", score=0.6 + i * 0.02, threshold=0.7),
                ],
            )
            for i in range(10)
        ]
        return EvaluationRun(
            run_id="run-a",
            dataset_name="test",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=results,
            metrics_evaluated=["faithfulness"],
        )

    @pytest.fixture
    def run_b(self):
        """두 번째 실행 (높은 점수)."""
        results = [
            TestCaseResult(
                test_case_id=f"tc-{i:03d}",
                metrics=[
                    MetricScore(name="faithfulness", score=0.8 + i * 0.01, threshold=0.7),
                ],
            )
            for i in range(10)
        ]
        return EvaluationRun(
            run_id="run-b",
            dataset_name="test",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=results,
            metrics_evaluated=["faithfulness"],
        )

    def test_compare_runs_t_test(self, adapter, run_a, run_b):
        """t-test 비교 테스트."""
        results = adapter.compare_runs(run_a, run_b, test_type="t-test")

        assert len(results) == 1
        result = results[0]

        assert result.run_id_a == "run-a"
        assert result.run_id_b == "run-b"
        assert result.metric == "faithfulness"
        assert result.mean_b > result.mean_a
        assert result.diff > 0

    def test_compare_runs_mann_whitney(self, adapter, run_a, run_b):
        """Mann-Whitney U 비교 테스트."""
        results = adapter.compare_runs(run_a, run_b, test_type="mann-whitney")

        assert len(results) == 1
        result = results[0]

        assert result.metric == "faithfulness"
        assert result.p_value >= 0
        assert result.p_value <= 1

    def test_compare_runs_specific_metrics(self, adapter, run_a, run_b):
        """특정 메트릭만 비교 테스트."""
        results = adapter.compare_runs(run_a, run_b, metrics=["faithfulness"])

        assert len(results) == 1

    def test_compare_runs_no_common_metrics(self, adapter, run_a):
        """공통 메트릭이 없는 경우 테스트."""
        # run_c는 다른 메트릭을 가짐
        results_c = [
            TestCaseResult(
                test_case_id="tc-001",
                metrics=[
                    MetricScore(name="context_precision", score=0.8, threshold=0.7),
                ],
            )
        ]
        run_c = EvaluationRun(
            run_id="run-c",
            dataset_name="test",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=results_c,
            metrics_evaluated=["context_precision"],
        )

        results = adapter.compare_runs(run_a, run_c)
        assert len(results) == 0

    def test_compare_runs_invalid_test_type(self, adapter, run_a, run_b):
        """잘못된 검정 유형 테스트."""
        with pytest.raises(ValueError, match="Unknown test type"):
            adapter.compare_runs(run_a, run_b, test_type="invalid")


class TestEffectSizeCalculation:
    """효과 크기 계산 테스트."""

    @pytest.fixture
    def adapter(self):
        return StatisticalAnalysisAdapter()

    def test_calculate_effect_size_positive(self, adapter):
        """양의 효과 크기 테스트."""
        values_a = [0.5, 0.55, 0.52, 0.48, 0.51]
        values_b = [0.8, 0.85, 0.82, 0.78, 0.81]

        effect_size = adapter.calculate_effect_size(values_a, values_b)
        assert effect_size > 0  # B가 더 높으므로 양수

    def test_calculate_effect_size_negative(self, adapter):
        """음의 효과 크기 테스트."""
        values_a = [0.8, 0.85, 0.82, 0.78, 0.81]
        values_b = [0.5, 0.55, 0.52, 0.48, 0.51]

        effect_size = adapter.calculate_effect_size(values_a, values_b)
        assert effect_size < 0  # B가 더 낮으므로 음수

    def test_calculate_effect_size_zero(self, adapter):
        """동일한 값의 효과 크기 테스트."""
        values_a = [0.7, 0.7, 0.7, 0.7, 0.7]
        values_b = [0.7, 0.7, 0.7, 0.7, 0.7]

        effect_size = adapter.calculate_effect_size(values_a, values_b)
        assert effect_size == 0.0

    def test_calculate_effect_size_empty_lists(self, adapter):
        """빈 리스트의 효과 크기 테스트."""
        effect_size = adapter.calculate_effect_size([], [])
        assert effect_size == 0.0

        effect_size = adapter.calculate_effect_size([0.5], [])
        assert effect_size == 0.0


class TestMetricStatsCalculation:
    """메트릭 통계 계산 테스트."""

    @pytest.fixture
    def adapter(self):
        return StatisticalAnalysisAdapter()

    def test_calculate_metric_stats(self, adapter):
        """메트릭 통계 계산 테스트."""
        scores = [0.5, 0.6, 0.7, 0.8, 0.9]

        stats = adapter._calculate_metric_stats(scores)

        assert stats.mean == pytest.approx(0.7)
        assert stats.min == 0.5
        assert stats.max == 0.9
        assert stats.median == 0.7
        assert stats.count == 5

    def test_calculate_metric_stats_single_value(self, adapter):
        """단일 값 통계 테스트."""
        scores = [0.75]

        stats = adapter._calculate_metric_stats(scores)

        assert stats.mean == 0.75
        assert stats.min == 0.75
        assert stats.max == 0.75
        assert stats.std == 0.0


class TestCorrelationAnalysis:
    """상관관계 분석 테스트."""

    @pytest.fixture
    def adapter(self):
        return StatisticalAnalysisAdapter()

    def test_analyze_correlations_perfect_positive(self, adapter):
        """완벽한 양의 상관관계 테스트."""
        metric_scores = {
            "metric_a": [0.1, 0.2, 0.3, 0.4, 0.5],
            "metric_b": [0.2, 0.4, 0.6, 0.8, 1.0],
        }

        matrix, metrics, significant = adapter._analyze_correlations(metric_scores)

        assert len(matrix) == 2
        assert len(metrics) == 2
        assert matrix[0][1] == pytest.approx(1.0)  # 완벽한 양의 상관

    def test_analyze_correlations_negative(self, adapter):
        """음의 상관관계 테스트."""
        metric_scores = {
            "metric_a": [0.1, 0.2, 0.3, 0.4, 0.5],
            "metric_b": [1.0, 0.8, 0.6, 0.4, 0.2],
        }

        matrix, metrics, significant = adapter._analyze_correlations(metric_scores)

        assert matrix[0][1] < 0  # 음의 상관

    def test_analyze_correlations_insufficient_data(self, adapter):
        """데이터 부족 시 상관관계 테스트."""
        metric_scores = {
            "metric_a": [0.5, 0.6],  # 3개 미만
            "metric_b": [0.7, 0.8],
        }

        matrix, metrics, significant = adapter._analyze_correlations(metric_scores)

        # 데이터가 부족하면 0.0으로 처리
        assert matrix[0][1] == 0.0


class TestLowPerformerDetection:
    """낮은 성능 케이스 감지 테스트."""

    @pytest.fixture
    def adapter(self):
        return StatisticalAnalysisAdapter()

    @pytest.fixture
    def run_with_low_performers(self):
        """낮은 성능 케이스가 있는 실행."""
        results = [
            TestCaseResult(
                test_case_id="tc-001",
                question="This is a very long question that should be truncated when displayed in the preview",
                metrics=[
                    MetricScore(name="faithfulness", score=0.2, threshold=0.7),
                ],
            ),
            TestCaseResult(
                test_case_id="tc-002",
                question="Short question",
                metrics=[
                    MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                ],
            ),
        ]
        return EvaluationRun(
            run_id="run-low",
            dataset_name="test",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=results,
            metrics_evaluated=["faithfulness"],
        )

    def test_find_low_performers(self, adapter, run_with_low_performers):
        """낮은 성능 케이스 감지 테스트."""
        low_performers = adapter._find_low_performers(run_with_low_performers, threshold=0.5)

        assert len(low_performers) == 1
        assert low_performers[0].test_case_id == "tc-001"
        assert low_performers[0].score == 0.2

    def test_low_performer_question_preview_truncation(self, adapter, run_with_low_performers):
        """질문 미리보기 자르기 테스트."""
        low_performers = adapter._find_low_performers(run_with_low_performers, threshold=0.5)

        # 긴 질문은 50자로 잘림
        assert len(low_performers[0].question_preview) <= 50

    def test_low_performer_potential_causes(self, adapter, run_with_low_performers):
        """잠재적 원인 추론 테스트."""
        low_performers = adapter._find_low_performers(run_with_low_performers, threshold=0.5)

        # faithfulness가 낮으면 hallucination 관련 원인이 포함되어야 함
        causes = low_performers[0].potential_causes
        assert len(causes) > 0
        assert any("hallucination" in c.lower() for c in causes)


class TestInsightGeneration:
    """인사이트 생성 테스트."""

    @pytest.fixture
    def adapter(self):
        return StatisticalAnalysisAdapter()

    def test_generate_insights_high_pass_rate(self, adapter):
        """높은 통과율 인사이트 테스트."""
        from evalvault.domain.entities.analysis import MetricStats

        metrics_summary = {
            "faithfulness": MetricStats(
                mean=0.9,
                std=0.05,
                min=0.8,
                max=1.0,
                median=0.9,
                percentile_25=0.88,
                percentile_75=0.95,
                count=10,
            )
        }

        insights = adapter._generate_insights(metrics_summary, [], [], 0.95)

        assert any("Excellent" in i for i in insights)

    def test_generate_insights_low_pass_rate(self, adapter):
        """낮은 통과율 인사이트 테스트."""
        from evalvault.domain.entities.analysis import MetricStats

        metrics_summary = {
            "faithfulness": MetricStats(
                mean=0.4,
                std=0.2,
                min=0.1,
                max=0.7,
                median=0.4,
                percentile_25=0.3,
                percentile_75=0.5,
                count=10,
            )
        }

        insights = adapter._generate_insights(metrics_summary, [], [], 0.3)

        assert any("attention" in i.lower() or "low" in i.lower() for i in insights)

    def test_generate_insights_with_correlations(self, adapter):
        """상관관계 인사이트 테스트."""
        from evalvault.domain.entities.analysis import CorrelationInsight, MetricStats

        correlations = [
            CorrelationInsight(
                variable1="faithfulness",
                variable2="answer_relevancy",
                correlation=0.85,
                p_value=0.001,
                is_significant=True,
            )
        ]

        metrics_summary = {
            "faithfulness": MetricStats(
                mean=0.8,
                std=0.1,
                min=0.6,
                max=1.0,
                median=0.8,
                percentile_25=0.75,
                percentile_75=0.85,
                count=10,
            )
        }

        insights = adapter._generate_insights(metrics_summary, correlations, [], 0.8)

        assert any("correlation" in i.lower() for i in insights)
