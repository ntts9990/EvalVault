"""Tests for domain entities."""

from datetime import datetime

import pytest

from evalvault.domain.entities import (
    Dataset,
    EvaluationRun,
    MetricScore,
    TestCase,
    TestCaseResult,
)


class TestTestCase:
    """TestCase 엔티티 테스트."""

    def test_create_test_case(self):
        """TestCase 생성 테스트."""
        tc = TestCase(
            id="tc-001",
            question="What is Python?",
            answer="Python is a programming language.",
            contexts=["Python is a high-level programming language."],
            ground_truth="A programming language",
        )
        assert tc.id == "tc-001"
        assert tc.question == "What is Python?"
        assert tc.answer == "Python is a programming language."
        assert len(tc.contexts) == 1
        assert tc.ground_truth == "A programming language"

    def test_to_ragas_dict(self):
        """Ragas 형식 변환 테스트."""
        tc = TestCase(
            id="tc-001",
            question="What is Python?",
            answer="Python is a programming language.",
            contexts=["Context 1", "Context 2"],
            ground_truth="A language",
        )
        ragas_dict = tc.to_ragas_dict()
        assert ragas_dict["user_input"] == "What is Python?"
        assert ragas_dict["response"] == "Python is a programming language."
        assert ragas_dict["retrieved_contexts"] == ["Context 1", "Context 2"]
        assert ragas_dict["reference"] == "A language"

    def test_to_ragas_dict_without_ground_truth(self):
        """ground_truth 없는 경우 Ragas 변환 테스트."""
        tc = TestCase(
            id="tc-001",
            question="What is Python?",
            answer="Python is a programming language.",
            contexts=["Context"],
        )
        ragas_dict = tc.to_ragas_dict()
        assert "reference" not in ragas_dict


class TestDataset:
    """Dataset 엔티티 테스트."""

    def test_create_dataset(self):
        """Dataset 생성 테스트."""
        test_cases = [
            TestCase(id="tc-001", question="Q1", answer="A1", contexts=["C1"]),
            TestCase(id="tc-002", question="Q2", answer="A2", contexts=["C2"]),
        ]
        ds = Dataset(name="test-dataset", version="1.0.0", test_cases=test_cases)
        assert ds.name == "test-dataset"
        assert ds.version == "1.0.0"
        assert len(ds) == 2

    def test_dataset_iteration(self):
        """Dataset 반복 테스트."""
        test_cases = [
            TestCase(id="tc-001", question="Q1", answer="A1", contexts=["C1"]),
            TestCase(id="tc-002", question="Q2", answer="A2", contexts=["C2"]),
        ]
        ds = Dataset(name="test-dataset", version="1.0.0", test_cases=test_cases)
        ids = [tc.id for tc in ds]
        assert ids == ["tc-001", "tc-002"]

    def test_to_ragas_list(self):
        """Ragas 리스트 변환 테스트."""
        test_cases = [
            TestCase(id="tc-001", question="Q1", answer="A1", contexts=["C1"]),
        ]
        ds = Dataset(name="test", version="1.0.0", test_cases=test_cases)
        ragas_list = ds.to_ragas_list()
        assert len(ragas_list) == 1
        assert ragas_list[0]["user_input"] == "Q1"


class TestMetricScore:
    """MetricScore 엔티티 테스트."""

    def test_passed_above_threshold(self):
        """threshold 이상일 때 passed=True."""
        ms = MetricScore(name="faithfulness", score=0.85, threshold=0.7)
        assert ms.passed is True

    def test_passed_below_threshold(self):
        """threshold 미만일 때 passed=False."""
        ms = MetricScore(name="faithfulness", score=0.5, threshold=0.7)
        assert ms.passed is False

    def test_passed_at_threshold(self):
        """threshold 정확히 같을 때 passed=True."""
        ms = MetricScore(name="faithfulness", score=0.7, threshold=0.7)
        assert ms.passed is True


class TestTestCaseResult:
    """TestCaseResult 엔티티 테스트."""

    def test_all_passed_true(self):
        """모든 메트릭 통과 시 all_passed=True."""
        result = TestCaseResult(
            test_case_id="tc-001",
            metrics=[
                MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                MetricScore(name="answer_relevancy", score=0.85, threshold=0.7),
            ],
        )
        assert result.all_passed is True

    def test_all_passed_false(self):
        """일부 메트릭 실패 시 all_passed=False."""
        result = TestCaseResult(
            test_case_id="tc-001",
            metrics=[
                MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                MetricScore(name="answer_relevancy", score=0.5, threshold=0.7),
            ],
        )
        assert result.all_passed is False

    def test_get_metric(self):
        """특정 메트릭 조회 테스트."""
        result = TestCaseResult(
            test_case_id="tc-001",
            metrics=[
                MetricScore(name="faithfulness", score=0.9, threshold=0.7),
            ],
        )
        metric = result.get_metric("faithfulness")
        assert metric is not None
        assert metric.score == 0.9

    def test_get_metric_not_found(self):
        """존재하지 않는 메트릭 조회."""
        result = TestCaseResult(test_case_id="tc-001", metrics=[])
        assert result.get_metric("faithfulness") is None


class TestEvaluationRun:
    """EvaluationRun 엔티티 테스트."""

    def test_create_run(self):
        """EvaluationRun 생성 테스트."""
        run = EvaluationRun(
            dataset_name="test-dataset",
            dataset_version="1.0.0",
            model_name="gpt-4o",
        )
        assert run.run_id is not None
        assert run.dataset_name == "test-dataset"
        assert run.total_test_cases == 0

    def test_pass_rate(self):
        """pass_rate 계산 테스트 (메트릭 기준 통과율)."""
        run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0.0",
            model_name="gpt-4o",
            metrics_evaluated=["f"],
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="f", score=0.9, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    metrics=[MetricScore(name="f", score=0.5, threshold=0.7)],
                ),
            ],
        )
        assert run.total_test_cases == 2
        assert run.passed_test_cases == 1  # 1개 테스트 케이스만 모든 메트릭 통과
        assert run.pass_rate == 0.5  # 테스트 케이스 기준 통과율
        # 메트릭 "f"의 평균: (0.9 + 0.5) / 2 = 0.7 >= 0.7 → 통과
        assert run.metric_pass_rate == 1.0  # 메트릭 기준 통과율 (1/1 메트릭 통과)

    def test_pass_rate_empty(self):
        """결과 없을 때 pass_rate=0."""
        run = EvaluationRun(dataset_name="test", dataset_version="1.0.0", model_name="gpt-4o")
        assert run.pass_rate == 0.0

    def test_duration_seconds(self):
        """duration_seconds 계산 테스트."""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 12, 0, 30)
        run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0.0",
            model_name="gpt-4o",
            started_at=start,
            finished_at=end,
        )
        assert run.duration_seconds == 30.0

    def test_get_avg_score(self):
        """평균 점수 계산 테스트."""
        run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0.0",
            model_name="gpt-4o",
            metrics_evaluated=["faithfulness"],
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="faithfulness", score=0.8, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    metrics=[MetricScore(name="faithfulness", score=0.6, threshold=0.7)],
                ),
            ],
        )
        avg = run.get_avg_score("faithfulness")
        assert avg == pytest.approx(0.7)

    def test_to_summary_dict(self):
        """요약 딕셔너리 생성 테스트."""
        run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0.0",
            model_name="gpt-4o",
            metrics_evaluated=["faithfulness"],
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
            ],
        )
        summary = run.to_summary_dict()
        assert summary["dataset_name"] == "test"
        assert summary["total_test_cases"] == 1
        assert summary["avg_faithfulness"] == 0.9
