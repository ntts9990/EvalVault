"""Comprehensive tests for RagasEvaluator service.

이 파일은 evaluator.py의 테스트 커버리지를 높이기 위한 추가 테스트를 포함합니다.
기존 test_evaluator.py와 함께 사용됩니다.

Coverage targets:
- _evaluate_sequential: 순차 평가 로직
- _evaluate_parallel: 병렬 평가 에러 핸들링
- _score_single_sample: NaN, 에러, fallback 처리
- _evaluate_with_custom_metrics: 커스텀 메트릭
- _calculate_cost: 비용 계산
- on_progress callback: 진행률 콜백
- Faithfulness fallback: Korean fallback 로직
- Threshold resolution: CLI > dataset > default 우선순위
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ragas import SingleTurnSample

from evalvault.domain.entities import Dataset, TestCase
from evalvault.domain.services.evaluator import (
    ParallelSampleOutcome,
    RagasEvaluator,
    TestCaseEvalResult,
)
from evalvault.ports.outbound.llm_port import LLMPort


class MockLLMAdapter(LLMPort):
    """Mock LLM adapter for testing."""

    def __init__(self, model_name: str = "gpt-5-nano"):
        self._model_name = model_name
        self._mock_llm = MagicMock()
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._total_tokens = 0
        self.provider_name = "openai"

    def get_model_name(self) -> str:
        return self._model_name

    def as_ragas_llm(self):
        return self._mock_llm

    def as_ragas_embeddings(self):
        return MagicMock()

    def reset_token_usage(self):
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._total_tokens = 0

    def get_and_reset_token_usage(self):
        result = (self._prompt_tokens, self._completion_tokens, self._total_tokens)
        self.reset_token_usage()
        return result

    def set_token_usage(self, prompt: int, completion: int):
        self._prompt_tokens = prompt
        self._completion_tokens = completion
        self._total_tokens = prompt + completion


def build_dummy_prompt():
    def input_model(**kwargs):
        return SimpleNamespace(**kwargs)

    def output_model(**kwargs):
        return SimpleNamespace(**kwargs)

    return SimpleNamespace(
        instruction="",
        input_model=input_model,
        output_model=output_model,
        examples=[],
        language=None,
    )


@pytest.fixture
def sample_dataset():
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
                contexts=["Python is a high-level programming language."],
                ground_truth="A programming language",
            ),
        ],
    )


@pytest.fixture
def mock_llm():
    """Mock LLM adapter."""
    return MockLLMAdapter()


@pytest.fixture
def ragas_sample():
    """테스트용 Ragas SingleTurnSample."""
    return SingleTurnSample(
        user_input="What is the capital of France?",
        response="The capital of France is Paris.",
        retrieved_contexts=["Paris is the capital and largest city of France."],
        reference="Paris",
    )


class TestEvaluateSequential:
    """_evaluate_sequential 테스트."""

    @pytest.mark.asyncio
    async def test_sequential_evaluation_processes_all_samples(self, sample_dataset, mock_llm):
        """순차 평가가 모든 샘플을 처리하는지 확인."""
        evaluator = RagasEvaluator()

        ragas_samples = [
            SingleTurnSample(
                user_input=tc.question,
                response=tc.answer,
                retrieved_contexts=tc.contexts,
                reference=tc.ground_truth,
            )
            for tc in sample_dataset.test_cases
        ]

        mock_metric = MagicMock()
        mock_metric.name = "faithfulness"

        with patch.object(
            evaluator,
            "_score_single_sample",
            new_callable=AsyncMock,
            return_value=({"faithfulness": 0.85}, {}),
        ):
            results = await evaluator._evaluate_sequential(
                dataset=sample_dataset,
                ragas_samples=ragas_samples,
                ragas_metrics=[mock_metric],
                llm=mock_llm,
            )

        assert len(results) == 2
        assert "tc-001" in results
        assert "tc-002" in results
        assert results["tc-001"].scores["faithfulness"] == 0.85

    @pytest.mark.asyncio
    async def test_sequential_tracks_token_usage(self, sample_dataset, mock_llm):
        """순차 평가에서 토큰 사용량이 기록되는지 확인."""
        evaluator = RagasEvaluator()

        ragas_samples = [
            SingleTurnSample(
                user_input=tc.question,
                response=tc.answer,
                retrieved_contexts=tc.contexts,
                reference=tc.ground_truth,
            )
            for tc in sample_dataset.test_cases
        ]

        mock_metric = MagicMock()
        mock_metric.name = "faithfulness"

        # 각 호출마다 토큰 사용량 설정
        call_count = 0

        async def mock_score(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_llm.set_token_usage(100 * call_count, 50 * call_count)
            return ({"faithfulness": 0.85}, {})

        with patch.object(evaluator, "_score_single_sample", side_effect=mock_score):
            results = await evaluator._evaluate_sequential(
                dataset=sample_dataset,
                ragas_samples=ragas_samples,
                ragas_metrics=[mock_metric],
                llm=mock_llm,
            )

        assert results["tc-001"].tokens_used == 150  # 100 + 50
        assert results["tc-001"].prompt_tokens == 100
        assert results["tc-001"].completion_tokens == 50

    @pytest.mark.asyncio
    async def test_sequential_tracks_latency(self, sample_dataset, mock_llm):
        """순차 평가에서 지연 시간이 기록되는지 확인."""
        evaluator = RagasEvaluator()

        ragas_samples = [
            SingleTurnSample(
                user_input=tc.question,
                response=tc.answer,
                retrieved_contexts=tc.contexts,
                reference=tc.ground_truth,
            )
            for tc in sample_dataset.test_cases
        ]

        mock_metric = MagicMock()
        mock_metric.name = "faithfulness"

        async def mock_score(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms 지연
            return ({"faithfulness": 0.85}, {})

        with patch.object(evaluator, "_score_single_sample", side_effect=mock_score):
            results = await evaluator._evaluate_sequential(
                dataset=sample_dataset,
                ragas_samples=ragas_samples,
                ragas_metrics=[mock_metric],
                llm=mock_llm,
            )

        for result in results.values():
            assert result.started_at is not None
            assert result.finished_at is not None
            assert result.latency_ms >= 10  # 최소 10ms


class TestEvaluateParallel:
    """_evaluate_parallel 테스트."""

    @pytest.mark.asyncio
    async def test_parallel_handles_individual_failures(self, sample_dataset, mock_llm):
        """병렬 평가에서 개별 실패가 다른 샘플에 영향을 주지 않는지 확인."""
        evaluator = RagasEvaluator()

        ragas_samples = [
            SingleTurnSample(
                user_input=tc.question,
                response=tc.answer,
                retrieved_contexts=tc.contexts,
                reference=tc.ground_truth,
            )
            for tc in sample_dataset.test_cases
        ]

        mock_metric = MagicMock()
        mock_metric.name = "faithfulness"

        call_count = 0

        async def mock_score(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("API Error")
            return ({"faithfulness": 0.85}, {})

        with patch.object(evaluator, "_score_single_sample", side_effect=mock_score):
            results = await evaluator._evaluate_parallel(
                dataset=sample_dataset,
                ragas_samples=ragas_samples,
                ragas_metrics=[mock_metric],
                llm=mock_llm,
                batch_size=2,
            )

        # 두 결과 모두 있어야 함
        assert len(results) == 2
        # 실패한 케이스는 0.0 점수를 가짐
        scores = [r.scores.get("faithfulness", 0.0) for r in results.values()]
        assert 0.0 in scores
        assert 0.85 in scores

    @pytest.mark.asyncio
    async def test_parallel_distributes_tokens_evenly(self, sample_dataset, mock_llm):
        """병렬 평가에서 토큰이 균등 분배되는지 확인."""
        evaluator = RagasEvaluator()

        ragas_samples = [
            SingleTurnSample(
                user_input=tc.question,
                response=tc.answer,
                retrieved_contexts=tc.contexts,
                reference=tc.ground_truth,
            )
            for tc in sample_dataset.test_cases
        ]

        mock_metric = MagicMock()
        mock_metric.name = "faithfulness"

        # 전체 토큰 설정
        mock_llm.set_token_usage(200, 100)

        with patch.object(
            evaluator,
            "_score_single_sample",
            new_callable=AsyncMock,
            return_value={"faithfulness": 0.85},
        ):
            results = await evaluator._evaluate_parallel(
                dataset=sample_dataset,
                ragas_samples=ragas_samples,
                ragas_metrics=[mock_metric],
                llm=mock_llm,
                batch_size=2,
            )

        # 2개 샘플로 균등 분배: 300 / 2 = 150
        for result in results.values():
            assert result.tokens_used == 150
            assert result.prompt_tokens == 100
            assert result.completion_tokens == 50


class TestScoreSingleSample:
    """_score_single_sample 테스트."""

    @pytest.mark.asyncio
    async def test_score_handles_nan_result(self, ragas_sample):
        """NaN 결과가 0.0으로 변환되는지 확인."""
        evaluator = RagasEvaluator()

        mock_metric = MagicMock()
        mock_metric.name = "faithfulness"
        mock_metric.ascore = AsyncMock(return_value=MagicMock(value=float("nan")))

        scores, _ = await evaluator._score_single_sample(ragas_sample, [mock_metric])

        assert scores["faithfulness"] == 0.0

    @pytest.mark.asyncio
    async def test_score_handles_non_numeric_result(self, ragas_sample):
        """비숫자 결과가 0.0으로 변환되는지 확인."""
        evaluator = RagasEvaluator()

        mock_metric = MagicMock()
        mock_metric.name = "faithfulness"
        mock_metric.ascore = AsyncMock(return_value=MagicMock(value="invalid"))

        scores, _ = await evaluator._score_single_sample(ragas_sample, [mock_metric])

        assert scores["faithfulness"] == 0.0

    @pytest.mark.asyncio
    async def test_score_extracts_value_from_metric_result(self, ragas_sample):
        """MetricResult.value에서 점수를 추출하는지 확인."""
        evaluator = RagasEvaluator()

        mock_metric = MagicMock()
        mock_metric.name = "faithfulness"
        mock_metric.ascore = AsyncMock(return_value=MagicMock(value=0.95))

        scores, _ = await evaluator._score_single_sample(ragas_sample, [mock_metric])

        assert scores["faithfulness"] == 0.95

    @pytest.mark.asyncio
    async def test_score_extracts_score_attribute(self, ragas_sample):
        """score 속성에서 점수를 추출하는지 확인."""
        evaluator = RagasEvaluator()

        mock_result = MagicMock()
        del mock_result.value  # value 속성 제거
        mock_result.score = 0.88

        mock_metric = MagicMock()
        mock_metric.name = "faithfulness"
        mock_metric.ascore = AsyncMock(return_value=mock_result)

        scores, _ = await evaluator._score_single_sample(ragas_sample, [mock_metric])

        assert scores["faithfulness"] == 0.88

    @pytest.mark.asyncio
    async def test_score_handles_raw_float(self, ragas_sample):
        """raw float 결과를 처리하는지 확인."""
        evaluator = RagasEvaluator()

        mock_metric = MagicMock()
        mock_metric.name = "faithfulness"
        mock_metric.ascore = AsyncMock(return_value=0.75)

        scores, _ = await evaluator._score_single_sample(ragas_sample, [mock_metric])

        assert scores["faithfulness"] == 0.75

    @pytest.mark.asyncio
    async def test_score_uses_legacy_api_when_ascore_not_available(self, ragas_sample):
        """ascore가 없을 때 single_turn_ascore를 사용하는지 확인."""
        evaluator = RagasEvaluator()

        mock_metric = MagicMock(spec=["name", "single_turn_ascore"])
        mock_metric.name = "faithfulness"
        mock_metric.single_turn_ascore = AsyncMock(return_value=0.82)

        scores, _ = await evaluator._score_single_sample(ragas_sample, [mock_metric])

        assert scores["faithfulness"] == 0.82

    @pytest.mark.asyncio
    async def test_score_handles_metric_without_scoring_api(self, ragas_sample):
        """scoring API가 없는 메트릭에서 예외가 발생하는지 확인."""
        evaluator = RagasEvaluator()

        mock_metric = MagicMock(spec=["name"])
        mock_metric.name = "answer_relevancy"

        scores, _ = await evaluator._score_single_sample(ragas_sample, [mock_metric])

        # 예외 발생 시 0.0 반환
        assert scores["answer_relevancy"] == 0.0


class TestProgressCallback:
    """on_progress 콜백 테스트."""

    @pytest.mark.asyncio
    async def test_sequential_calls_progress_callback(self, sample_dataset, mock_llm):
        """순차 평가에서 progress 콜백이 호출되는지 확인."""
        evaluator = RagasEvaluator()

        ragas_samples = [
            SingleTurnSample(
                user_input=tc.question,
                response=tc.answer,
                retrieved_contexts=tc.contexts,
                reference=tc.ground_truth,
            )
            for tc in sample_dataset.test_cases
        ]

        mock_metric = MagicMock()
        mock_metric.name = "faithfulness"

        progress_calls = []

        def on_progress(current, total, message):
            progress_calls.append((current, total, message))

        with patch.object(
            evaluator,
            "_score_single_sample",
            new_callable=AsyncMock,
            return_value=({"faithfulness": 0.85}, {}),
        ):
            await evaluator._evaluate_sequential(
                dataset=sample_dataset,
                ragas_samples=ragas_samples,
                ragas_metrics=[mock_metric],
                llm=mock_llm,
                on_progress=on_progress,
            )

        assert len(progress_calls) == 2
        assert progress_calls[0] == (1, 2, "Evaluated tc-001")
        assert progress_calls[1] == (2, 2, "Evaluated tc-002")

    @pytest.mark.asyncio
    async def test_parallel_calls_progress_callback(self, sample_dataset, mock_llm):
        """병렬 평가에서 progress 콜백이 호출되는지 확인."""
        evaluator = RagasEvaluator()

        ragas_samples = [
            SingleTurnSample(
                user_input=tc.question,
                response=tc.answer,
                retrieved_contexts=tc.contexts,
                reference=tc.ground_truth,
            )
            for tc in sample_dataset.test_cases
        ]

        mock_metric = MagicMock()
        mock_metric.name = "faithfulness"

        progress_calls = []

        def on_progress(current, total, message):
            progress_calls.append((current, total, message))

        with patch.object(
            evaluator,
            "_score_single_sample",
            new_callable=AsyncMock,
            return_value={"faithfulness": 0.85},
        ):
            await evaluator._evaluate_parallel(
                dataset=sample_dataset,
                ragas_samples=ragas_samples,
                ragas_metrics=[mock_metric],
                llm=mock_llm,
                batch_size=2,
                on_progress=on_progress,
            )

        # 병렬이므로 순서는 보장되지 않지만 2번 호출되어야 함
        assert len(progress_calls) == 2
        # 모든 호출에서 total은 2여야 함
        assert all(call[1] == 2 for call in progress_calls)


class TestCustomMetrics:
    """_evaluate_with_custom_metrics 테스트."""

    @pytest.mark.asyncio
    async def test_custom_metric_evaluation(self):
        """커스텀 메트릭 평가가 올바르게 동작하는지 확인."""
        evaluator = RagasEvaluator()

        dataset = Dataset(
            name="custom-test",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="tc-001",
                    question="보험금 청구 방법?",
                    answer="보험금 청구는 보험사에 연락하세요.",
                    contexts=["보험금 청구 절차 안내"],
                    ground_truth="보험사 연락",
                ),
            ],
        )

        # Mock the custom metric class
        mock_metric_instance = MagicMock()
        mock_metric_instance.score.return_value = 0.9
        mock_metric_class = MagicMock(return_value=mock_metric_instance)

        with patch.dict(
            evaluator.CUSTOM_METRIC_MAP,
            {"insurance_term_accuracy": mock_metric_class},
        ):
            results = await evaluator._evaluate_with_custom_metrics(
                dataset=dataset, metrics=["insurance_term_accuracy"]
            )

        assert "tc-001" in results
        assert results["tc-001"].scores.get("insurance_term_accuracy") == 0.9
        assert results["tc-001"].tokens_used == 0  # 커스텀 메트릭은 LLM 사용 안함

    @pytest.mark.asyncio
    async def test_custom_metric_tracks_timing(self):
        """커스텀 메트릭이 타이밍을 기록하는지 확인."""
        evaluator = RagasEvaluator()

        dataset = Dataset(
            name="timing-test",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="tc-001",
                    question="Q",
                    answer="A",
                    contexts=["C"],
                    ground_truth="GT",
                ),
            ],
        )

        mock_metric_instance = MagicMock()
        mock_metric_instance.score.return_value = 0.8

        with patch.dict(
            evaluator.CUSTOM_METRIC_MAP,
            {"test_metric": MagicMock(return_value=mock_metric_instance)},
        ):
            results = await evaluator._evaluate_with_custom_metrics(
                dataset=dataset, metrics=["test_metric"]
            )

        result = results["tc-001"]
        assert result.started_at is not None
        assert result.finished_at is not None
        assert result.finished_at >= result.started_at


class TestCalculateCost:
    """_calculate_cost 테스트."""

    def test_calculate_cost_gpt4o(self):
        """GPT-4o 비용 계산."""
        evaluator = RagasEvaluator()

        # gpt-4o: input $2.50/1M, output $10.00/1M
        cost = evaluator._calculate_cost("gpt-4o", prompt_tokens=1000, completion_tokens=500)

        expected = (1000 / 1_000_000 * 2.50) + (500 / 1_000_000 * 10.00)
        assert cost == pytest.approx(expected)

    def test_calculate_cost_gpt5_nano(self):
        """GPT-5-nano 비용 계산."""
        evaluator = RagasEvaluator()

        # gpt-5-nano: input $5.00/1M, output $15.00/1M
        cost = evaluator._calculate_cost("gpt-5-nano", prompt_tokens=2000, completion_tokens=1000)

        expected = (2000 / 1_000_000 * 5.00) + (1000 / 1_000_000 * 15.00)
        assert cost == pytest.approx(expected)

    def test_calculate_cost_unknown_model_uses_default(self):
        """알 수 없는 모델은 기본 가격 사용."""
        evaluator = RagasEvaluator()

        cost = evaluator._calculate_cost("unknown-model", prompt_tokens=1000, completion_tokens=500)

        # 기본값: gpt-4o 가격
        expected = (1000 / 1_000_000 * 2.50) + (500 / 1_000_000 * 10.00)
        assert cost == pytest.approx(expected)

    def test_calculate_cost_with_prefix(self):
        """provider/model 형식 비용 계산."""
        evaluator = RagasEvaluator()

        cost = evaluator._calculate_cost(
            "openai/gpt-5-nano", prompt_tokens=1000, completion_tokens=500
        )

        expected = (1000 / 1_000_000 * 5.00) + (500 / 1_000_000 * 15.00)
        assert cost == pytest.approx(expected)


class TestThresholdResolution:
    """임계값 우선순위 테스트 (CLI > dataset > default)."""

    @pytest.mark.asyncio
    async def test_cli_threshold_takes_priority(self, mock_llm):
        """CLI 임계값이 최우선인지 확인."""
        evaluator = RagasEvaluator()

        dataset = Dataset(
            name="threshold-test",
            version="1.0.0",
            test_cases=[
                TestCase(id="tc-001", question="Q", answer="A", contexts=["C"]),
            ],
            thresholds={"faithfulness": 0.5},  # 데이터셋 임계값
        )

        mock_results = {"tc-001": TestCaseEvalResult(scores={"faithfulness": 0.85})}

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = (mock_results, {}, {})

            result = await evaluator.evaluate(
                dataset=dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                thresholds={"faithfulness": 0.9},  # CLI 임계값
            )

        # CLI 값이 사용되어야 함
        assert result.thresholds["faithfulness"] == 0.9

    @pytest.mark.asyncio
    async def test_dataset_threshold_used_when_cli_absent(self, mock_llm):
        """CLI 임계값이 없을 때 데이터셋 임계값이 사용되는지 확인."""
        evaluator = RagasEvaluator()

        dataset = Dataset(
            name="threshold-test",
            version="1.0.0",
            test_cases=[
                TestCase(id="tc-001", question="Q", answer="A", contexts=["C"]),
            ],
            thresholds={"faithfulness": 0.6},
        )

        mock_results = {"tc-001": TestCaseEvalResult(scores={"faithfulness": 0.85})}

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = (mock_results, {}, {})

            result = await evaluator.evaluate(
                dataset=dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                thresholds={},  # CLI 임계값 없음
            )

        # 데이터셋 값이 사용되어야 함
        assert result.thresholds["faithfulness"] == 0.6

    @pytest.mark.asyncio
    async def test_default_threshold_used_when_both_absent(self, mock_llm):
        """CLI와 데이터셋 임계값 모두 없을 때 기본값이 사용되는지 확인."""
        evaluator = RagasEvaluator()

        dataset = Dataset(
            name="threshold-test",
            version="1.0.0",
            test_cases=[
                TestCase(id="tc-001", question="Q", answer="A", contexts=["C"]),
            ],
            thresholds={},  # 데이터셋 임계값 없음
        )

        mock_results = {"tc-001": TestCaseEvalResult(scores={"faithfulness": 0.85})}

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = (mock_results, {}, {})

            result = await evaluator.evaluate(
                dataset=dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                thresholds=None,  # CLI 임계값 없음
            )

        # 기본값 0.7이 사용되어야 함
        assert result.thresholds["faithfulness"] == 0.7


class TestFaithfulnessFallback:
    """Faithfulness fallback 로직 테스트."""

    def test_contains_korean_returns_true_for_korean(self):
        """한국어 텍스트 감지."""
        assert RagasEvaluator._contains_korean("안녕하세요") is True
        assert RagasEvaluator._contains_korean("Hello 안녕") is True

    def test_contains_korean_returns_false_for_english(self):
        """영어 텍스트는 한국어로 감지되지 않음."""
        assert RagasEvaluator._contains_korean("Hello World") is False
        assert RagasEvaluator._contains_korean("123 ABC") is False

    def test_summarize_ragas_error_simple(self):
        """간단한 에러 요약."""
        error = ValueError("Test error message")
        summary = RagasEvaluator._summarize_ragas_error(error)

        assert "ValueError" in summary
        assert "Test error message" in summary

    def test_summarize_ragas_error_with_cause(self):
        """cause가 있는 에러 요약."""
        cause = ConnectionError("Connection failed")
        error = RuntimeError("Wrapper error")
        error.__cause__ = cause

        summary = RagasEvaluator._summarize_ragas_error(error)

        assert "ConnectionError" in summary
        assert "Connection failed" in summary

    def test_summarize_ragas_error_truncates_long_message(self):
        """긴 에러 메시지 truncation."""
        long_message = "A" * 300
        error = ValueError(long_message)

        summary = RagasEvaluator._summarize_ragas_error(error)

        assert len(summary) < 250
        assert "..." in summary

    @pytest.mark.asyncio
    async def test_faithfulness_fallback_returns_none_for_empty_response(self):
        """빈 응답에 대해 fallback이 None을 반환하는지 확인."""
        evaluator = RagasEvaluator()

        sample = SingleTurnSample(
            user_input="Q",
            response="",  # 빈 응답
            retrieved_contexts=["context"],
            reference=None,
        )

        result = evaluator._fallback_korean_faithfulness(sample)

        assert result is None

    @pytest.mark.asyncio
    async def test_faithfulness_fallback_returns_none_for_empty_contexts(self):
        """빈 컨텍스트에 대해 fallback이 None을 반환하는지 확인."""
        evaluator = RagasEvaluator()

        sample = SingleTurnSample(
            user_input="Q",
            response="A",
            retrieved_contexts=[],  # 빈 컨텍스트
            reference=None,
        )

        result = evaluator._fallback_korean_faithfulness(sample)

        assert result is None

    @pytest.mark.asyncio
    async def test_faithfulness_fallback_returns_none_for_non_korean(self):
        """영어 텍스트에 대해 fallback이 None을 반환하는지 확인."""
        evaluator = RagasEvaluator()

        sample = SingleTurnSample(
            user_input="What is AI?",
            response="AI is artificial intelligence",
            retrieved_contexts=["AI stands for artificial intelligence"],
            reference=None,
        )

        result = evaluator._fallback_korean_faithfulness(sample)

        assert result is None


class TestAnswerRelevancyPromptTuning:
    """Answer relevancy 프롬프트 튜닝 테스트."""

    def test_override_metric_prompt_updates_question_generation(self):
        """answer_relevancy prompt override가 적용되는지 확인."""
        prompt = build_dummy_prompt()
        prompt.instruction = "기존 지시문"
        metric = SimpleNamespace(question_generation=prompt)
        original = metric.question_generation.instruction

        applied = RagasEvaluator._override_metric_prompt(metric, "새 프롬프트 지시문")

        assert applied is True
        assert metric.question_generation.instruction == "새 프롬프트 지시문"
        assert metric.question_generation.instruction != original

    def test_korean_default_prompt_applied(self):
        """한국어 데이터셋에 기본 프롬프트가 적용되는지 확인."""
        evaluator = RagasEvaluator()
        dataset = Dataset(
            name="korean-dataset",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="kr-001",
                    question="사망 시 보상 한도는 얼마인가요?",
                    answer="사망 시 1억 5천만원까지 보장됩니다.",
                    contexts=["사망 시 1억 5천만원까지 보장됩니다."],
                )
            ],
        )
        prompt = build_dummy_prompt()
        metric = SimpleNamespace(name="answer_relevancy", question_generation=prompt)

        evaluator._apply_answer_relevancy_prompt_defaults(
            dataset=dataset,
            ragas_metrics=[metric],
            prompt_overrides=None,
        )

        assert (
            metric.question_generation.instruction == evaluator.ANSWER_RELEVANCY_KOREAN_INSTRUCTION
        )
        assert metric.question_generation.examples
        example_input, example_output = metric.question_generation.examples[0]
        assert example_input.response == evaluator.ANSWER_RELEVANCY_KOREAN_EXAMPLES[0]["response"]
        assert example_output.question == evaluator.ANSWER_RELEVANCY_KOREAN_EXAMPLES[0]["question"]

    def test_english_dataset_skips_korean_defaults(self):
        """영어 데이터셋은 한국어 기본 프롬프트를 적용하지 않는다."""
        evaluator = RagasEvaluator()
        dataset = Dataset(
            name="english-dataset",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="en-001",
                    question="What is the coverage limit for death benefits?",
                    answer="The coverage limit for death benefits is 150 million KRW.",
                    contexts=["The death benefit coverage limit is 150 million KRW."],
                )
            ],
        )
        prompt = build_dummy_prompt()
        prompt.instruction = "기존 지시문"
        metric = SimpleNamespace(name="answer_relevancy", question_generation=prompt)
        original = metric.question_generation.instruction

        evaluator._apply_answer_relevancy_prompt_defaults(
            dataset=dataset,
            ragas_metrics=[metric],
            prompt_overrides=None,
        )

        assert metric.question_generation.instruction == original

    def test_english_language_override_skips_korean_defaults(self):
        evaluator = RagasEvaluator()
        dataset = Dataset(
            name="korean-dataset",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="kr-001",
                    question="사망 시 보상 한도는 얼마인가요?",
                    answer="사망 시 1억 5천만원까지 보장됩니다.",
                    contexts=["사망 시 1억 5천만원까지 보장됩니다."],
                )
            ],
        )
        prompt = build_dummy_prompt()
        prompt.instruction = "기존 지시문"
        metric = SimpleNamespace(name="answer_relevancy", question_generation=prompt)

        evaluator._prompt_language = "en"
        evaluator._apply_answer_relevancy_prompt_defaults(
            dataset=dataset,
            ragas_metrics=[metric],
            prompt_overrides=None,
        )

        assert metric.question_generation.instruction == "기존 지시문"


class TestFactualCorrectnessPromptTuning:
    """Factual correctness 프롬프트 튜닝 테스트."""

    def test_korean_default_prompts_applied(self):
        """한국어 데이터셋에 기본 프롬프트가 적용되는지 확인."""
        evaluator = RagasEvaluator()
        dataset = Dataset(
            name="korean-dataset",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="kr-001",
                    question="사망 시 보상 한도는 얼마인가요?",
                    answer="사망 시 1억 5천만원까지 보장됩니다.",
                    contexts=["사망 시 1억 5천만원까지 보장됩니다."],
                    ground_truth="1억 5천만원",
                )
            ],
        )
        claim_prompt = build_dummy_prompt()
        nli_prompt = build_dummy_prompt()
        metric = SimpleNamespace(
            name="factual_correctness",
            claim_decomposition_prompt=claim_prompt,
            nli_prompt=nli_prompt,
        )

        evaluator._apply_factual_correctness_prompt_defaults(
            dataset=dataset,
            ragas_metrics=[metric],
            prompt_overrides=None,
        )

        assert (
            metric.claim_decomposition_prompt.instruction
            == evaluator.FACTUAL_CORRECTNESS_CLAIM_INSTRUCTION
        )
        assert metric.nli_prompt.instruction == evaluator.FACTUAL_CORRECTNESS_NLI_INSTRUCTION
        assert metric.claim_decomposition_prompt.examples
        assert metric.nli_prompt.examples

    def test_english_dataset_skips_korean_defaults(self):
        """영어 데이터셋은 한국어 기본 프롬프트를 적용하지 않는다."""
        evaluator = RagasEvaluator()
        dataset = Dataset(
            name="english-dataset",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="en-001",
                    question="What is the coverage limit for death benefits?",
                    answer="The coverage limit for death benefits is 150 million KRW.",
                    contexts=["The death benefit coverage limit is 150 million KRW."],
                    ground_truth="150 million KRW",
                )
            ],
        )
        claim_prompt = build_dummy_prompt()
        nli_prompt = build_dummy_prompt()
        claim_prompt.instruction = "기존 지시문"
        nli_prompt.instruction = "기존 지시문"
        metric = SimpleNamespace(
            name="factual_correctness",
            claim_decomposition_prompt=claim_prompt,
            nli_prompt=nli_prompt,
        )
        claim_original = metric.claim_decomposition_prompt.instruction
        nli_original = metric.nli_prompt.instruction

        evaluator._apply_factual_correctness_prompt_defaults(
            dataset=dataset,
            ragas_metrics=[metric],
            prompt_overrides=None,
        )

        assert metric.claim_decomposition_prompt.instruction == claim_original
        assert metric.nli_prompt.instruction == nli_original


class TestDataclasses:
    """데이터클래스 테스트."""

    def test_test_case_eval_result_defaults(self):
        """TestCaseEvalResult 기본값."""
        result = TestCaseEvalResult(scores={"test": 0.5})

        assert result.scores == {"test": 0.5}
        assert result.tokens_used == 0
        assert result.prompt_tokens == 0
        assert result.completion_tokens == 0
        assert result.cost_usd == 0.0
        assert result.started_at is None
        assert result.finished_at is None
        assert result.latency_ms == 0

    def test_parallel_sample_outcome_defaults(self):
        """ParallelSampleOutcome 기본값."""
        now = datetime.now()
        outcome = ParallelSampleOutcome(
            scores={"test": 0.8},
            started_at=now,
            finished_at=now,
            latency_ms=100,
        )

        assert outcome.scores == {"test": 0.8}
        assert outcome.error is None

    def test_parallel_sample_outcome_with_error(self):
        """ParallelSampleOutcome 에러 포함."""
        now = datetime.now()
        error = ValueError("Test error")
        outcome = ParallelSampleOutcome(
            scores={},
            started_at=now,
            finished_at=now,
            latency_ms=0,
            error=error,
        )

        assert outcome.error is error


class TestMetricMaps:
    """메트릭 맵 테스트."""

    def test_metric_map_has_all_standard_metrics(self):
        """METRIC_MAP에 모든 표준 메트릭이 있는지 확인."""
        evaluator = RagasEvaluator()

        expected_metrics = [
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
            "factual_correctness",
            "semantic_similarity",
            "summary_score",
            "summary_faithfulness",
        ]

        for metric in expected_metrics:
            assert metric in evaluator.METRIC_MAP

    def test_custom_metric_map_has_insurance_term_accuracy(self):
        """CUSTOM_METRIC_MAP에 insurance_term_accuracy가 있는지 확인."""
        evaluator = RagasEvaluator()

        assert "insurance_term_accuracy" in evaluator.CUSTOM_METRIC_MAP
        assert "entity_preservation" in evaluator.CUSTOM_METRIC_MAP

    def test_metric_args_defined_for_all_metrics(self):
        """METRIC_ARGS에 모든 메트릭의 인자가 정의되어 있는지 확인."""
        evaluator = RagasEvaluator()

        for metric_name in evaluator.METRIC_MAP:
            assert metric_name in evaluator.METRIC_ARGS

    def test_reference_required_metrics(self):
        """REFERENCE_REQUIRED_METRICS가 올바르게 정의되어 있는지 확인."""
        evaluator = RagasEvaluator()

        expected = {
            "context_precision",
            "context_recall",
            "exact_match",
            "f1_score",
            "factual_correctness",
            "hit_rate",
            "mrr",
            "ndcg",
            "no_answer_accuracy",
            "semantic_similarity",
        }

        assert expected == evaluator.REFERENCE_REQUIRED_METRICS

    def test_default_thresholds_for_summary_metrics(self):
        """요약 전용 메트릭 기본 임계값 확인."""
        evaluator = RagasEvaluator()

        assert evaluator.default_threshold_for("summary_faithfulness") == pytest.approx(0.9)
        assert evaluator.default_threshold_for("summary_score") == pytest.approx(0.85)
        assert evaluator.default_threshold_for("entity_preservation") == pytest.approx(0.9)
        assert evaluator.default_threshold_for("faithfulness") == pytest.approx(0.7)


class TestEvaluatorIntegration:
    """통합 테스트."""

    @pytest.mark.asyncio
    async def test_evaluate_with_mixed_metrics(self, mock_llm):
        """Ragas 메트릭과 커스텀 메트릭을 함께 평가."""
        evaluator = RagasEvaluator()

        dataset = Dataset(
            name="mixed-test",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="tc-001",
                    question="보험금 청구?",
                    answer="보험사에 연락하세요.",
                    contexts=["보험금 청구 방법"],
                    ground_truth="보험사 연락",
                ),
            ],
        )

        ragas_results = {"tc-001": TestCaseEvalResult(scores={"faithfulness": 0.9})}

        custom_results = {"tc-001": TestCaseEvalResult(scores={"insurance_term_accuracy": 0.85})}

        with patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_ragas:
            mock_ragas.return_value = (ragas_results, {}, {})

            with patch.object(
                evaluator, "_evaluate_with_custom_metrics", new_callable=AsyncMock
            ) as mock_custom:
                mock_custom.return_value = custom_results

                result = await evaluator.evaluate(
                    dataset=dataset,
                    metrics=["faithfulness", "insurance_term_accuracy"],
                    llm=mock_llm,
                )

        assert len(result.results) == 1
        tc_result = result.results[0]
        faithfulness_metric = tc_result.get_metric("faithfulness")
        insurance_metric = tc_result.get_metric("insurance_term_accuracy")

        assert faithfulness_metric is not None
        assert insurance_metric is not None
        assert faithfulness_metric.score == 0.9
        assert insurance_metric.score == 0.85

    @pytest.mark.asyncio
    async def test_evaluate_stores_preprocess_report(self, mock_llm):
        """전처리 리포트가 tracker_metadata에 저장되는지 확인."""
        evaluator = RagasEvaluator()

        dataset = Dataset(
            name="preprocess-test",
            version="1.0.0",
            test_cases=[
                TestCase(
                    id="tc-001",
                    question="Q",
                    answer="A",
                    contexts=["C"],
                    ground_truth="GT",
                ),
            ],
        )

        mock_results = {"tc-001": TestCaseEvalResult(scores={"faithfulness": 0.9})}

        # Mock preprocessor to return findings
        mock_report = MagicMock()
        mock_report.has_findings.return_value = True
        mock_report.to_dict.return_value = {"findings": ["test finding"]}

        with (
            patch.object(evaluator._preprocessor, "apply", return_value=mock_report),
            patch.object(evaluator, "_evaluate_with_ragas", new_callable=AsyncMock) as mock_eval,
        ):
            mock_eval.return_value = (mock_results, {}, {})

            result = await evaluator.evaluate(
                dataset=dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
            )

        assert "dataset_preprocess" in result.tracker_metadata
        assert result.tracker_metadata["dataset_preprocess"] == {"findings": ["test finding"]}
