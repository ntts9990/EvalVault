"""Integration tests for evaluation flow.

These tests verify the complete evaluation pipeline.
Tests marked with @pytest.mark.requires_openai require OPENAI_API_KEY.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from evalvault.domain.entities import (
    Dataset,
    EvaluationRun,
    MetricScore,
    TestCase,
    TestCaseResult,
)
from evalvault.domain.services.evaluator import RagasEvaluator, TestCaseEvalResult
from evalvault.ports.outbound.llm_port import LLMPort
from tests.integration.conftest import get_test_model


class MockLLMAdapter(LLMPort):
    """Mock LLM adapter for testing without API calls."""

    def __init__(self, model_name: str = "mock-model"):
        self._model_name = model_name
        self._mock_llm = MagicMock()

    def get_model_name(self) -> str:
        return self._model_name

    def as_ragas_llm(self):
        return self._mock_llm


class TestEvaluationFlowWithMock:
    """Mock을 사용한 평가 플로우 통합 테스트."""

    @pytest.fixture
    def sample_dataset(self):
        """테스트용 샘플 데이터셋."""
        return Dataset(
            name="integration-test",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="tc-001",
                    question="What is the capital of France?",
                    answer="The capital of France is Paris.",
                    contexts=["Paris is the capital and largest city of France."],
                    ground_truth="Paris",
                ),
                TestCase(
                    id="tc-002",
                    question="What is Python?",
                    answer="Python is a programming language.",
                    contexts=[
                        "Python is a high-level programming language.",
                        "It was created by Guido van Rossum.",
                    ],
                    ground_truth="A programming language",
                ),
            ],
        )

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM adapter."""
        return MockLLMAdapter()

    @pytest.mark.asyncio
    async def test_full_evaluation_flow(self, sample_dataset, mock_llm):
        """전체 평가 플로우 테스트 (Mock LLM)."""
        evaluator = RagasEvaluator()

        # Mock the Ragas evaluation to return fixed scores with token usage
        mock_results = {
            "tc-001": TestCaseEvalResult(
                scores={"faithfulness": 0.9, "answer_relevancy": 0.85},
                tokens_used=200,
            ),
            "tc-002": TestCaseEvalResult(
                scores={"faithfulness": 0.75, "answer_relevancy": 0.8},
                tokens_used=180,
            ),
        }

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = (mock_results, {}, {})

            result = await evaluator.evaluate(
                dataset=sample_dataset,
                metrics=["faithfulness", "answer_relevancy"],
                llm=mock_llm,
                thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7},
            )

        # Verify result structure
        assert isinstance(result, EvaluationRun)
        assert result.dataset_name == "integration-test"
        assert result.model_name == "mock-model"
        assert len(result.results) == 2

        # Verify all test cases have results
        result_ids = {r.test_case_id for r in result.results}
        expected_ids = {"tc-001", "tc-002"}
        assert result_ids == expected_ids

        # Verify metrics are evaluated
        assert "faithfulness" in result.metrics_evaluated
        assert "answer_relevancy" in result.metrics_evaluated

        # Verify token tracking
        assert result.total_tokens == 380

    @pytest.mark.asyncio
    async def test_evaluation_with_thresholds(self, sample_dataset, mock_llm):
        """임계값 적용 평가 테스트."""
        evaluator = RagasEvaluator()

        mock_results = {
            "tc-001": TestCaseEvalResult(scores={"faithfulness": 0.9}),  # Pass
            "tc-002": TestCaseEvalResult(scores={"faithfulness": 0.5}),  # Fail
        }

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = (mock_results, {}, {})

            result = await evaluator.evaluate(
                dataset=sample_dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                thresholds={"faithfulness": 0.7},
            )

        # Verify pass/fail status
        assert result.passed_test_cases == 1
        assert result.total_test_cases == 2
        assert result.pass_rate == 0.5

    @pytest.mark.asyncio
    async def test_evaluation_timestamps(self, sample_dataset, mock_llm):
        """평가 시간 기록 테스트."""
        evaluator = RagasEvaluator()

        mock_results = {
            "tc-001": TestCaseEvalResult(scores={"faithfulness": 0.9}),
            "tc-002": TestCaseEvalResult(scores={"faithfulness": 0.8}),
        }

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = (mock_results, {}, {})

            result = await evaluator.evaluate(
                dataset=sample_dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                thresholds={"faithfulness": 0.7},
            )

        assert result.started_at is not None
        assert result.finished_at is not None
        assert result.duration_seconds >= 0


class TestRealEvaluationFlow:
    """실제 API를 사용하는 평가 플로우 테스트.

    이 테스트는 OPENAI_API_KEY가 설정되어 있을 때만 실행됩니다.
    """

    @pytest.fixture
    def small_dataset(self):
        """API 비용을 최소화하기 위한 작은 데이터셋."""
        return Dataset(
            name="real-api-test",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="tc-001",
                    question="What is 2+2?",
                    answer="2+2 equals 4.",
                    contexts=["Basic arithmetic: 2+2=4"],
                    ground_truth="4",
                ),
            ],
        )

    @pytest.mark.slow
    @pytest.mark.requires_openai
    @pytest.mark.asyncio
    async def test_real_evaluation_faithfulness(self, small_dataset):
        """실제 OpenAI API로 faithfulness 평가 테스트."""
        from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter
        from evalvault.config.settings import Settings

        settings = Settings()
        llm = OpenAIAdapter(settings)
        evaluator = RagasEvaluator()

        result = await evaluator.evaluate(
            dataset=small_dataset,
            metrics=["faithfulness"],
            llm=llm,
            thresholds={"faithfulness": 0.5},  # Lower threshold for test
        )

        assert isinstance(result, EvaluationRun)
        assert len(result.results) == 1
        assert result.results[0].metrics[0].name == "faithfulness"
        # Score should be between 0 and 1
        assert 0 <= result.results[0].metrics[0].score <= 1


class TestEvaluationResultAggregation:
    """평가 결과 집계 테스트."""

    def test_evaluation_run_summary(self):
        """EvaluationRun 요약 정보 테스트."""
        run = EvaluationRun(
            dataset_name="test",
            dataset_version="1.0.0",
            model_name=get_test_model(),
            started_at=datetime.now(),
            finished_at=datetime.now() + timedelta(seconds=30),
            metrics_evaluated=["faithfulness", "answer_relevancy"],
            thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7},
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[
                        MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.85, threshold=0.7),
                    ],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    metrics=[
                        MetricScore(name="faithfulness", score=0.6, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.75, threshold=0.7),
                    ],
                ),
            ],
        )

        # Test summary dict
        summary = run.to_summary_dict()
        assert summary["dataset_name"] == "test"
        assert summary["total_test_cases"] == 2
        assert summary["passed_test_cases"] == 1  # Only tc-001 passes all
        assert summary["pass_rate"] == 0.5
        assert summary["duration_seconds"] == pytest.approx(30.0)

        # Test average scores
        assert run.get_avg_score("faithfulness") == pytest.approx(0.75)
        assert run.get_avg_score("answer_relevancy") == pytest.approx(0.8)

    def test_metric_score_pass_fail(self):
        """MetricScore 통과/실패 판정 테스트."""
        passing_score = MetricScore(name="faithfulness", score=0.8, threshold=0.7)
        failing_score = MetricScore(name="faithfulness", score=0.6, threshold=0.7)
        exact_score = MetricScore(name="faithfulness", score=0.7, threshold=0.7)

        assert passing_score.passed is True
        assert failing_score.passed is False
        assert exact_score.passed is True  # >= threshold
