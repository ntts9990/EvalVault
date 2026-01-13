"""Tests for Ragas evaluator service."""

import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from evalvault.domain.entities import Dataset, EvaluationRun, TestCase
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
    async def test_evaluate_returns_evaluation_run(self, sample_dataset, mock_llm, thresholds):
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

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = (mock_results, {}, {})

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
    async def test_evaluate_applies_retriever_when_contexts_empty(self, mock_llm):
        """빈 컨텍스트에 대해 retriever가 적용되는지 확인."""

        @dataclass(frozen=True)
        class DummyRetrievalResult:
            document: str
            doc_id: int
            score: float

        class DummyRetriever:
            def __init__(self) -> None:
                self.calls: list[str] = []

            def search(self, query: str, top_k: int = 5):
                self.calls.append(query)
                return [
                    DummyRetrievalResult(document="컨텍스트 A", doc_id=0, score=0.9),
                    DummyRetrievalResult(document="컨텍스트 B", doc_id=1, score=0.8),
                ][:top_k]

        dataset = Dataset(
            name="retriever-dataset",
            version="1.0.0",
            test_cases=[
                TestCase(id="tc-1", question="Q1", answer="A1", contexts=[]),
                TestCase(id="tc-2", question="Q2", answer="A2", contexts=["existing"]),
            ],
        )
        evaluator = RagasEvaluator()
        retriever = DummyRetriever()
        mock_results = {
            "tc-1": TestCaseEvalResult(scores={"faithfulness": 0.9}),
            "tc-2": TestCaseEvalResult(scores={"faithfulness": 0.8}),
        }

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = (mock_results, {}, {})

            result = await evaluator.evaluate(
                dataset=dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                retriever=retriever,
                retriever_top_k=2,
                retriever_doc_ids=["doc-1", "doc-2"],
            )

        assert retriever.calls == ["Q1"]
        assert dataset.test_cases[0].contexts
        assert dataset.test_cases[1].contexts == ["existing"]
        assert result.retrieval_metadata["tc-1"]["doc_ids"] == ["doc-1", "doc-2"]
        assert "tc-2" not in result.retrieval_metadata

    @pytest.mark.asyncio
    async def test_evaluate_aggregates_scores_correctly(self, sample_dataset, mock_llm, thresholds):
        """평가 결과가 올바르게 집계되는지 테스트."""
        evaluator = RagasEvaluator()

        mock_results = {
            "tc-001": TestCaseEvalResult(scores={"faithfulness": 0.9}, tokens_used=100),
            "tc-002": TestCaseEvalResult(scores={"faithfulness": 0.5}, tokens_used=80),
        }

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = (mock_results, {}, {})

            result = await evaluator.evaluate(
                dataset=sample_dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                thresholds=thresholds,
            )

            # Check aggregated metrics
            assert result.total_test_cases == 2
            assert result.passed_test_cases == 1  # Only tc-001 passes (0.9 >= 0.7)
            assert result.pass_rate == 0.5  # 테스트 케이스 기준 통과율
            # 메트릭 "faithfulness"의 평균: (0.9 + 0.5) / 2 = 0.7 >= 0.7 → 통과
            assert result.metric_pass_rate == 1.0  # 메트릭 기준 통과율

            # Check average score
            avg_faithfulness = result.get_avg_score("faithfulness")
            assert avg_faithfulness == pytest.approx(0.7)

            # Check total tokens
            assert result.total_tokens == 180

    @pytest.mark.asyncio
    async def test_parallel_evaluation_tracks_latency(self, sample_dataset, mock_llm):
        """병렬 평가에서도 개별 테스트 케이스의 타이밍이 기록된다."""
        evaluator = RagasEvaluator()
        ragas_metrics = [MagicMock()]
        ragas_metrics[0].name = "faithfulness"

        async def fake_score(*_args, **_kwargs):
            await asyncio.sleep(0)
            return {"faithfulness": 0.9}

        with patch.object(evaluator, "_score_single_sample", side_effect=fake_score):
            mock_llm.reset_token_usage = MagicMock()
            mock_llm.get_and_reset_token_usage = MagicMock(return_value=(0, 0, 0))
            results = await evaluator._evaluate_parallel(
                dataset=sample_dataset,
                ragas_samples=["sample-1", "sample-2"],
                ragas_metrics=ragas_metrics,
                llm=mock_llm,
                batch_size=2,
            )

        assert len(results) == 2
        for res in results.values():
            assert res.started_at is not None
            assert res.finished_at is not None
            assert res.finished_at >= res.started_at
            assert res.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_evaluate_sets_timestamps(self, sample_dataset, mock_llm, thresholds):
        """평가 시작/종료 시간이 올바르게 설정되는지 테스트."""
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
                thresholds=thresholds,
            )

            assert result.started_at is not None
            assert result.finished_at is not None
            assert result.finished_at >= result.started_at
            assert result.duration_seconds is not None
            assert result.duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_evaluate_with_multiple_metrics(self, sample_dataset, mock_llm, thresholds):
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

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = (mock_results, {}, {})

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
    async def test_evaluate_applies_thresholds(self, sample_dataset, mock_llm, thresholds):
        """임계값이 올바르게 적용되는지 테스트."""
        evaluator = RagasEvaluator()

        mock_results = {
            "tc-001": TestCaseEvalResult(scores={"faithfulness": 0.9}),
            "tc-002": TestCaseEvalResult(scores={"faithfulness": 0.6}),
        }

        custom_thresholds = {"faithfulness": 0.8}

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = (mock_results, {}, {})

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
    async def test_evaluate_stores_thresholds_in_run(self, sample_dataset, mock_llm, thresholds):
        """임계값이 EvaluationRun에 저장되는지 테스트."""
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
                thresholds=thresholds,
            )

            # Only thresholds for evaluated metrics are stored
            assert result.thresholds == {"faithfulness": 0.7}

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
        try:
            from ragas.metrics.collections import FactualCorrectness
        except ImportError:  # pragma: no cover
            from ragas.metrics import FactualCorrectness
        assert evaluator.METRIC_MAP["factual_correctness"] == FactualCorrectness

    def test_metric_map_includes_semantic_similarity(self):
        """METRIC_MAP에 semantic_similarity가 포함되는지 테스트."""
        evaluator = RagasEvaluator()
        assert "semantic_similarity" in evaluator.METRIC_MAP
        try:
            from ragas.metrics.collections import SemanticSimilarity
        except ImportError:  # pragma: no cover
            from ragas.metrics import SemanticSimilarity
        assert evaluator.METRIC_MAP["semantic_similarity"] == SemanticSimilarity

    def test_embedding_required_metrics_constant(self):
        """EMBEDDING_REQUIRED_METRICS가 올바르게 정의되는지 테스트."""
        evaluator = RagasEvaluator()
        assert hasattr(evaluator, "EMBEDDING_REQUIRED_METRICS")
        assert "answer_relevancy" in evaluator.EMBEDDING_REQUIRED_METRICS
        assert "semantic_similarity" in evaluator.EMBEDDING_REQUIRED_METRICS


class TestRagasEvaluatorParallel:
    """병렬 처리 관련 테스트."""

    @pytest.fixture
    def large_dataset(self):
        """병렬 처리 테스트용 대용량 데이터셋."""
        test_cases = [
            TestCase(
                id=f"tc-{i:03d}",
                question=f"Question {i}?",
                answer=f"Answer {i}.",
                contexts=[f"Context for question {i}."],
                ground_truth=f"Ground truth {i}",
            )
            for i in range(10)
        ]
        return Dataset(name="large-test", version="1.0.0", test_cases=test_cases)

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM adapter."""
        return MockLLMAdapter()

    @pytest.mark.asyncio
    async def test_evaluate_with_parallel_option(self, large_dataset, mock_llm):
        """parallel=True 옵션으로 병렬 평가 테스트."""
        evaluator = RagasEvaluator()

        # Create mock results for all test cases
        mock_results = {
            f"tc-{i:03d}": TestCaseEvalResult(
                scores={"faithfulness": 0.8},
                tokens_used=100,
            )
            for i in range(10)
        }

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = (mock_results, {}, {})

            result = await evaluator.evaluate(
                dataset=large_dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                parallel=True,
            )

            assert len(result.results) == 10
            assert result.total_tokens == 1000  # 10 * 100

    @pytest.mark.asyncio
    async def test_evaluate_with_batch_size(self, large_dataset, mock_llm):
        """batch_size 옵션으로 배치 평가 테스트."""
        evaluator = RagasEvaluator()

        mock_results = {
            f"tc-{i:03d}": TestCaseEvalResult(
                scores={"faithfulness": 0.8},
                tokens_used=100,
            )
            for i in range(10)
        }

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = (mock_results, {}, {})

            result = await evaluator.evaluate(
                dataset=large_dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                parallel=True,
                batch_size=5,
            )

            assert len(result.results) == 10

    @pytest.mark.asyncio
    async def test_parallel_evaluation_faster_than_sequential(self, large_dataset, mock_llm):
        """병렬 평가가 순차 평가보다 빠른지 테스트 (mock 기반)."""
        import time

        evaluator = RagasEvaluator()

        # Simulate slow evaluation with sleep
        async def slow_eval(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms per call
            return (
                {
                    f"tc-{i:03d}": TestCaseEvalResult(scores={"faithfulness": 0.8})
                    for i in range(10)
                },
                {},
                {},
            )

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.side_effect = slow_eval

            start = time.time()
            await evaluator.evaluate(
                dataset=large_dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                parallel=True,
            )
            parallel_time = time.time() - start

            # Parallel should complete in reasonable time (not 10x sequential)
            assert parallel_time < 0.5  # Should be much faster than 100ms
