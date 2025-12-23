"""Tests for Ragas evaluator service."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from evalvault.domain.entities import Dataset, TestCase, EvaluationRun, MetricType
from evalvault.domain.services.evaluator import RagasEvaluator, TestCaseEvalResult
from evalvault.ports.outbound.llm_port import LLMPort
from tests.unit.conftest import get_test_model


class MockLLMAdapter(LLMPort):
    """Mock LLM adapter for testing."""

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or get_test_model()
        self._mock_llm = MagicMock()

    def get_model_name(self) -> str:
        return self._model_name

    def as_ragas_llm(self):
        return self._mock_llm


class TestRagasEvaluator:
    """RagasEvaluator 서비스 테스트."""

    @pytest.fixture
    def sample_dataset(self):
        """테스트용 샘플 데이터셋."""
        return Dataset(
            name="test-dataset",
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

    @pytest.fixture
    def thresholds(self):
        """테스트용 임계값."""
        return {
            "faithfulness": 0.7,
            "answer_relevancy": 0.7,
            "context_precision": 0.7,
            "context_recall": 0.7,
            "factual_correctness": 0.7,
            "semantic_similarity": 0.7,
        }

    @pytest.mark.asyncio
    async def test_evaluate_returns_evaluation_run(
        self, sample_dataset, mock_llm, thresholds
    ):
        """evaluate 메서드가 EvaluationRun을 반환하는지 테스트."""
        evaluator = RagasEvaluator()

        # Mock the Ragas evaluation with TestCaseEvalResult
        mock_results = {
            "tc-001": TestCaseEvalResult(
                scores={"faithfulness": 0.9, "answer_relevancy": 0.85},
                tokens_used=150,
            ),
            "tc-002": TestCaseEvalResult(
                scores={"faithfulness": 0.75, "answer_relevancy": 0.8},
                tokens_used=120,
            ),
        }

        with patch.object(
            evaluator, "_evaluate_with_ragas", new_callable=AsyncMock
        ) as mock_eval:
            mock_eval.return_value = mock_results

            result = await evaluator.evaluate(
                dataset=sample_dataset,
                metrics=["faithfulness", "answer_relevancy"],
                llm=mock_llm,
                thresholds=thresholds,
            )

            assert isinstance(result, EvaluationRun)
            assert result.dataset_name == "test-dataset"
            assert result.dataset_version == "1.0.0"
            assert result.model_name == get_test_model()
            assert len(result.results) == 2
            assert result.metrics_evaluated == ["faithfulness", "answer_relevancy"]
            # Verify token tracking
            assert result.total_tokens == 270  # 150 + 120
            assert result.results[0].tokens_used == 150
            assert result.results[1].tokens_used == 120

    @pytest.mark.asyncio
    async def test_evaluate_aggregates_scores_correctly(
        self, sample_dataset, mock_llm, thresholds
    ):
        """평가 결과가 올바르게 집계되는지 테스트."""
        evaluator = RagasEvaluator()

        mock_results = {
            "tc-001": TestCaseEvalResult(scores={"faithfulness": 0.9}, tokens_used=100),
            "tc-002": TestCaseEvalResult(scores={"faithfulness": 0.5}, tokens_used=80),
        }

        with patch.object(
            evaluator, "_evaluate_with_ragas", new_callable=AsyncMock
        ) as mock_eval:
            mock_eval.return_value = mock_results

            result = await evaluator.evaluate(
                dataset=sample_dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                thresholds=thresholds,
            )

            # Check aggregated metrics
            assert result.total_test_cases == 2
            assert result.passed_test_cases == 1  # Only tc-001 passes (0.9 >= 0.7)
            assert result.pass_rate == 0.5

            # Check average score
            avg_faithfulness = result.get_avg_score("faithfulness")
            assert avg_faithfulness == pytest.approx(0.7)

            # Check total tokens
            assert result.total_tokens == 180

    @pytest.mark.asyncio
    async def test_evaluate_sets_timestamps(self, sample_dataset, mock_llm, thresholds):
        """평가 시작/종료 시간이 올바르게 설정되는지 테스트."""
        evaluator = RagasEvaluator()

        mock_results = {
            "tc-001": TestCaseEvalResult(scores={"faithfulness": 0.9}),
            "tc-002": TestCaseEvalResult(scores={"faithfulness": 0.8}),
        }

        with patch.object(
            evaluator, "_evaluate_with_ragas", new_callable=AsyncMock
        ) as mock_eval:
            mock_eval.return_value = mock_results

            result = await evaluator.evaluate(
                dataset=sample_dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                thresholds=thresholds,
            )

            assert result.started_at is not None
            assert result.finished_at is not None
            assert result.finished_at >= result.started_at
            assert result.duration_seconds is not None
            assert result.duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_evaluate_with_multiple_metrics(
        self, sample_dataset, mock_llm, thresholds
    ):
        """여러 메트릭을 동시에 평가할 수 있는지 테스트."""
        evaluator = RagasEvaluator()

        mock_results = {
            "tc-001": TestCaseEvalResult(
                scores={
                    "faithfulness": 0.9,
                    "answer_relevancy": 0.85,
                    "context_precision": 0.8,
                },
                tokens_used=300,
            ),
            "tc-002": TestCaseEvalResult(
                scores={
                    "faithfulness": 0.75,
                    "answer_relevancy": 0.7,
                    "context_precision": 0.65,
                },
                tokens_used=280,
            ),
        }

        with patch.object(
            evaluator, "_evaluate_with_ragas", new_callable=AsyncMock
        ) as mock_eval:
            mock_eval.return_value = mock_results

            result = await evaluator.evaluate(
                dataset=sample_dataset,
                metrics=["faithfulness", "answer_relevancy", "context_precision"],
                llm=mock_llm,
                thresholds=thresholds,
            )

            # Check first test case
            tc1_result = result.results[0]
            assert len(tc1_result.metrics) == 3
            assert tc1_result.get_metric("faithfulness").score == 0.9
            assert tc1_result.get_metric("answer_relevancy").score == 0.85
            assert tc1_result.get_metric("context_precision").score == 0.8

    @pytest.mark.asyncio
    async def test_evaluate_applies_thresholds(
        self, sample_dataset, mock_llm, thresholds
    ):
        """임계값이 올바르게 적용되는지 테스트."""
        evaluator = RagasEvaluator()

        mock_results = {
            "tc-001": TestCaseEvalResult(scores={"faithfulness": 0.9}),
            "tc-002": TestCaseEvalResult(scores={"faithfulness": 0.6}),
        }

        custom_thresholds = {"faithfulness": 0.8}

        with patch.object(
            evaluator, "_evaluate_with_ragas", new_callable=AsyncMock
        ) as mock_eval:
            mock_eval.return_value = mock_results

            result = await evaluator.evaluate(
                dataset=sample_dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                thresholds=custom_thresholds,
            )

            # tc-001: 0.9 >= 0.8 -> passed
            assert result.results[0].all_passed is True
            # tc-002: 0.6 < 0.8 -> failed
            assert result.results[1].all_passed is False

    @pytest.mark.asyncio
    async def test_evaluate_stores_thresholds_in_run(
        self, sample_dataset, mock_llm, thresholds
    ):
        """임계값이 EvaluationRun에 저장되는지 테스트."""
        evaluator = RagasEvaluator()

        mock_results = {
            "tc-001": TestCaseEvalResult(scores={"faithfulness": 0.9}),
            "tc-002": TestCaseEvalResult(scores={"faithfulness": 0.8}),
        }

        with patch.object(
            evaluator, "_evaluate_with_ragas", new_callable=AsyncMock
        ) as mock_eval:
            mock_eval.return_value = mock_results

            result = await evaluator.evaluate(
                dataset=sample_dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                thresholds=thresholds,
            )

            assert result.thresholds == thresholds

    @pytest.mark.asyncio
    async def test_evaluate_with_empty_dataset(self, mock_llm, thresholds):
        """빈 데이터셋 평가 테스트."""
        empty_dataset = Dataset(name="empty", version="1.0.0", test_cases=[])
        evaluator = RagasEvaluator()

        result = await evaluator.evaluate(
            dataset=empty_dataset,
            metrics=["faithfulness"],
            llm=mock_llm,
            thresholds=thresholds,
        )

        assert result.total_test_cases == 0
        assert result.pass_rate == 0.0
        assert len(result.results) == 0

    def test_metric_map_includes_factual_correctness(self):
        """METRIC_MAP에 factual_correctness가 포함되는지 테스트."""
        evaluator = RagasEvaluator()
        assert "factual_correctness" in evaluator.METRIC_MAP
        from ragas.metrics.collections import FactualCorrectness
        assert evaluator.METRIC_MAP["factual_correctness"] == FactualCorrectness

    def test_metric_map_includes_semantic_similarity(self):
        """METRIC_MAP에 semantic_similarity가 포함되는지 테스트."""
        evaluator = RagasEvaluator()
        assert "semantic_similarity" in evaluator.METRIC_MAP
        from ragas.metrics.collections import SemanticSimilarity
        assert evaluator.METRIC_MAP["semantic_similarity"] == SemanticSimilarity

    def test_embedding_required_metrics_constant(self):
        """EMBEDDING_REQUIRED_METRICS가 올바르게 정의되는지 테스트."""
        evaluator = RagasEvaluator()
        assert hasattr(evaluator, "EMBEDDING_REQUIRED_METRICS")
        assert "answer_relevancy" in evaluator.EMBEDDING_REQUIRED_METRICS
        assert "semantic_similarity" in evaluator.EMBEDDING_REQUIRED_METRICS
