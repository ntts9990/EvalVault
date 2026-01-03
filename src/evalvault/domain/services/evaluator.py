"""Ragas evaluation service."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ragas import SingleTurnSample

try:  # Ragas >=0.2.0
    from ragas.metrics.collections import (
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
        FactualCorrectness,
        Faithfulness,
        SemanticSimilarity,
    )
except ImportError:  # pragma: no cover - fallback for older Ragas versions
    from ragas.metrics import (
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
        FactualCorrectness,
        Faithfulness,
        SemanticSimilarity,
    )

from evalvault.domain.entities import Dataset, EvaluationRun, MetricScore, TestCase, TestCaseResult
from evalvault.domain.metrics.insurance import InsuranceTermAccuracy
from evalvault.domain.services.batch_executor import run_in_batches
from evalvault.ports.outbound.llm_port import LLMPort

logger = logging.getLogger(__name__)


@dataclass
class TestCaseEvalResult:
    """Ragas 평가 결과 (토큰 사용량, 비용, 타이밍 포함)."""

    __test__ = False

    scores: dict[str, float]
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    latency_ms: int = 0


@dataclass
class ParallelSampleOutcome:
    """Container for per-sample metadata collected during parallel evaluation."""

    scores: dict[str, float]
    started_at: datetime
    finished_at: datetime
    latency_ms: int
    error: Exception | None = None


class RagasEvaluator:
    """Ragas 기반 RAG 평가 서비스.

    Ragas 메트릭을 사용하여 RAG 시스템의 품질을 평가합니다.
    """

    # Ragas 메트릭 매핑
    METRIC_MAP = {
        "faithfulness": Faithfulness,
        "answer_relevancy": AnswerRelevancy,
        "context_precision": ContextPrecision,
        "context_recall": ContextRecall,
        "factual_correctness": FactualCorrectness,
        "semantic_similarity": SemanticSimilarity,
    }

    # Custom 메트릭 매핑 (Ragas 외부 메트릭)
    CUSTOM_METRIC_MAP = {
        "insurance_term_accuracy": InsuranceTermAccuracy,
    }

    # Metrics that require embeddings
    EMBEDDING_REQUIRED_METRICS = {"answer_relevancy", "semantic_similarity"}

    # Metrics that require reference (ground_truth)
    REFERENCE_REQUIRED_METRICS = {
        "context_precision",
        "context_recall",
        "factual_correctness",
        "semantic_similarity",
    }

    # Metric-specific required arguments for Ragas 0.4+ ascore() API
    METRIC_ARGS = {
        "faithfulness": ["user_input", "response", "retrieved_contexts"],
        "answer_relevancy": ["user_input", "response"],
        "context_precision": ["user_input", "retrieved_contexts", "reference"],
        "context_recall": ["user_input", "retrieved_contexts", "reference"],
        "factual_correctness": ["response", "reference"],
        "semantic_similarity": ["response", "reference"],
    }

    async def evaluate(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,
        thresholds: dict[str, float] | None = None,
        parallel: bool = False,
        batch_size: int = 5,
    ) -> EvaluationRun:
        """데이터셋을 Ragas로 평가.

        Args:
            dataset: 평가할 데이터셋
            metrics: 평가할 메트릭 리스트 (예: ['faithfulness', 'answer_relevancy'])
            llm: LLM 어댑터 (Ragas가 사용)
            thresholds: 메트릭별 임계값 (CLI에서 전달, 없으면 dataset.thresholds 사용)
            parallel: 병렬 처리 활성화 여부 (기본값: False)
            batch_size: 병렬 처리 시 배치 크기 (기본값: 5)

        Returns:
            평가 결과가 담긴 EvaluationRun

        Note:
            임계값 우선순위: CLI 옵션 > 데이터셋 내장 > 기본값(0.7)
        """
        # Resolve thresholds: CLI > dataset > default(0.7)
        resolved_thresholds = {}
        for metric in metrics:
            if thresholds and metric in thresholds:
                # CLI에서 전달된 값 우선
                resolved_thresholds[metric] = thresholds[metric]
            elif dataset.thresholds and metric in dataset.thresholds:
                # 데이터셋에 정의된 값
                resolved_thresholds[metric] = dataset.thresholds[metric]
            else:
                # 기본값
                resolved_thresholds[metric] = 0.7

        # Initialize evaluation run
        run = EvaluationRun(
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            model_name=llm.get_model_name(),
            started_at=datetime.now(),
            metrics_evaluated=metrics,
            thresholds=resolved_thresholds,
        )

        # Handle empty dataset
        if len(dataset.test_cases) == 0:
            run.finished_at = datetime.now()
            return run

        # Use resolved thresholds
        thresholds = resolved_thresholds

        # Separate Ragas metrics from custom metrics
        ragas_metrics = [m for m in metrics if m in self.METRIC_MAP]
        custom_metrics = [m for m in metrics if m in self.CUSTOM_METRIC_MAP]

        # Evaluate with Ragas (if any Ragas metrics)
        eval_results_by_test_case = {}
        if ragas_metrics:
            eval_results_by_test_case = await self._evaluate_with_ragas(
                dataset=dataset,
                metrics=ragas_metrics,
                llm=llm,
                parallel=parallel,
                batch_size=batch_size,
            )

        # Evaluate with custom metrics (if any custom metrics)
        if custom_metrics:
            custom_results = await self._evaluate_with_custom_metrics(
                dataset=dataset, metrics=custom_metrics
            )
            # Merge custom results into eval_results
            for test_case_id, custom_result in custom_results.items():
                if test_case_id in eval_results_by_test_case:
                    # Merge scores
                    eval_results_by_test_case[test_case_id].scores.update(custom_result.scores)
                else:
                    eval_results_by_test_case[test_case_id] = custom_result

        # Aggregate results
        total_tokens = 0
        total_cost = 0.0
        for test_case in dataset.test_cases:
            eval_result = eval_results_by_test_case.get(test_case.id, TestCaseEvalResult(scores={}))

            metric_scores = []
            for metric_name in metrics:
                score_value = eval_result.scores.get(metric_name, 0.0)
                threshold = thresholds.get(metric_name, 0.7)

                metric_scores.append(
                    MetricScore(
                        name=metric_name,
                        score=score_value,
                        threshold=threshold,
                    )
                )

            test_case_result = TestCaseResult(
                test_case_id=test_case.id,
                metrics=metric_scores,
                tokens_used=eval_result.tokens_used,
                latency_ms=eval_result.latency_ms,
                cost_usd=eval_result.cost_usd if eval_result.cost_usd > 0 else None,
                started_at=eval_result.started_at,
                finished_at=eval_result.finished_at,
                # 원본 데이터 포함 (Langfuse 로깅용)
                question=test_case.question,
                answer=test_case.answer,
                contexts=test_case.contexts,
                ground_truth=test_case.ground_truth,
            )
            run.results.append(test_case_result)
            total_tokens += eval_result.tokens_used
            total_cost += eval_result.cost_usd

        # Set total tokens and cost
        run.total_tokens = total_tokens
        run.total_cost_usd = total_cost if total_cost > 0 else None

        # Finalize run
        run.finished_at = datetime.now()
        return run

    async def _evaluate_with_ragas(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,
        parallel: bool = False,
        batch_size: int = 5,
    ) -> dict[str, TestCaseEvalResult]:
        """Ragas로 실제 평가 수행.

        Args:
            dataset: 평가할 데이터셋
            metrics: 평가할 메트릭 리스트
            llm: LLM 어댑터
            parallel: 병렬 처리 여부
            batch_size: 병렬 처리 시 배치 크기

        Returns:
            테스트 케이스 ID별 평가 결과 (토큰 사용량 포함)
            예: {"tc-001": TestCaseEvalResult(scores={"faithfulness": 0.9}, tokens_used=150)}
        """

        # Convert dataset to Ragas format
        ragas_samples = []
        for test_case in dataset.test_cases:
            sample = SingleTurnSample(
                user_input=test_case.question,
                response=test_case.answer,
                retrieved_contexts=test_case.contexts,
                reference=test_case.ground_truth,
            )
            ragas_samples.append(sample)

        # Get Ragas LLM and embeddings
        ragas_llm = llm.as_ragas_llm()
        ragas_embeddings = None
        if hasattr(llm, "as_ragas_embeddings"):
            ragas_embeddings = llm.as_ragas_embeddings()

        # Initialize Ragas metrics with LLM (new Ragas API requires llm at init)
        ragas_metrics = []
        for metric_name in metrics:
            metric_class = self.METRIC_MAP.get(metric_name)
            if metric_class:
                # Pass embeddings for metrics that require it
                if metric_name in self.EMBEDDING_REQUIRED_METRICS and ragas_embeddings:
                    ragas_metrics.append(metric_class(llm=ragas_llm, embeddings=ragas_embeddings))
                else:
                    ragas_metrics.append(metric_class(llm=ragas_llm))

        # 병렬 처리 vs 순차 처리
        if parallel and len(ragas_samples) > 1:
            return await self._evaluate_parallel(
                dataset=dataset,
                ragas_samples=ragas_samples,
                ragas_metrics=ragas_metrics,
                llm=llm,
                batch_size=batch_size,
            )
        else:
            return await self._evaluate_sequential(
                dataset=dataset,
                ragas_samples=ragas_samples,
                ragas_metrics=ragas_metrics,
                llm=llm,
            )

    async def _evaluate_sequential(
        self,
        dataset: Dataset,
        ragas_samples: list,
        ragas_metrics: list,
        llm: LLMPort,
    ) -> dict[str, TestCaseEvalResult]:
        """순차 평가 (기존 로직)."""
        results: dict[str, TestCaseEvalResult] = {}

        for idx, sample in enumerate(ragas_samples):
            test_case_id = dataset.test_cases[idx].id

            # Reset token tracking before each test case
            if hasattr(llm, "reset_token_usage"):
                llm.reset_token_usage()

            # 단일 테스트 케이스 평가
            test_case_started_at = datetime.now()
            scores = await self._score_single_sample(sample, ragas_metrics)
            test_case_finished_at = datetime.now()

            latency_ms = int((test_case_finished_at - test_case_started_at).total_seconds() * 1000)

            # Get token usage for this test case
            test_case_prompt_tokens = 0
            test_case_completion_tokens = 0
            test_case_tokens = 0
            if hasattr(llm, "get_and_reset_token_usage"):
                (
                    test_case_prompt_tokens,
                    test_case_completion_tokens,
                    test_case_tokens,
                ) = llm.get_and_reset_token_usage()

            results[test_case_id] = TestCaseEvalResult(
                scores=scores,
                tokens_used=test_case_tokens,
                prompt_tokens=test_case_prompt_tokens,
                completion_tokens=test_case_completion_tokens,
                cost_usd=0.0,
                started_at=test_case_started_at,
                finished_at=test_case_finished_at,
                latency_ms=latency_ms,
            )

        return results

    async def _evaluate_parallel(
        self,
        dataset: Dataset,
        ragas_samples: list,
        ragas_metrics: list,
        llm: LLMPort,
        batch_size: int = 5,
    ) -> dict[str, TestCaseEvalResult]:
        """병렬 평가 (배치 단위로 동시 실행).

        Args:
            dataset: 데이터셋
            ragas_samples: Ragas 샘플 목록
            ragas_metrics: 평가할 메트릭 목록
            llm: LLM 어댑터
            batch_size: 동시 실행할 테스트 케이스 수

        Returns:
            테스트 케이스별 평가 결과
        """
        results: dict[str, TestCaseEvalResult] = {}
        sample_pairs = list(zip(dataset.test_cases, ragas_samples, strict=True))
        total_samples = len(sample_pairs)

        async def worker(pair: tuple[TestCase, Any]):
            test_case, sample = pair
            started_at = datetime.now()
            error: Exception | None = None
            try:
                scores = await self._score_single_sample(sample, ragas_metrics)
            except Exception as exc:  # pragma: no cover - safe fallback
                logger.warning(
                    "Failed to evaluate test case '%s' in parallel mode: %s",
                    test_case.id,
                    exc,
                )
                scores = {metric.name: 0.0 for metric in ragas_metrics}
                error = exc
            finished_at = datetime.now()
            latency_ms = int((finished_at - started_at).total_seconds() * 1000)
            return (
                test_case.id,
                ParallelSampleOutcome(
                    scores=scores,
                    started_at=started_at,
                    finished_at=finished_at,
                    latency_ms=latency_ms,
                    error=error,
                ),
            )

        batched_outcomes = await run_in_batches(
            sample_pairs,
            worker=worker,
            batch_size=batch_size,
            return_exceptions=True,
        )

        for outcome in batched_outcomes:
            if isinstance(outcome, Exception):  # pragma: no cover - defensive
                logger.error("Parallel evaluation batch failed: %s", outcome)
                continue
            test_case_id, sample_outcome = outcome
            if sample_outcome.error:
                logger.debug(
                    "Parallel evaluation error for '%s': %s",
                    test_case_id,
                    sample_outcome.error,
                )
            results[test_case_id] = TestCaseEvalResult(
                scores=sample_outcome.scores,
                tokens_used=0,
                prompt_tokens=0,
                completion_tokens=0,
                cost_usd=0.0,
                started_at=sample_outcome.started_at,
                finished_at=sample_outcome.finished_at,
                latency_ms=sample_outcome.latency_ms,
            )

        # 전체 토큰 사용량 가져와서 테스트 케이스별로 평균 분배
        if hasattr(llm, "get_and_reset_token_usage"):
            total_prompt, total_completion, total_tokens = llm.get_and_reset_token_usage()
            if total_samples > 0:
                avg_tokens = total_tokens // total_samples
                avg_prompt = total_prompt // total_samples
                avg_completion = total_completion // total_samples

                for test_case_id in results:
                    results[test_case_id].tokens_used = avg_tokens
                    results[test_case_id].prompt_tokens = avg_prompt
                    results[test_case_id].completion_tokens = avg_completion

        return results

    async def _score_single_sample(
        self, sample: SingleTurnSample, ragas_metrics: list
    ) -> dict[str, float]:
        """단일 샘플에 대해 모든 메트릭 점수 계산.

        Args:
            sample: 평가할 Ragas 샘플
            ragas_metrics: 메트릭 인스턴스 목록

        Returns:
            메트릭명: 점수 딕셔너리
        """
        scores: dict[str, float] = {}

        for metric in ragas_metrics:
            try:
                # Ragas >=0.4 uses ascore() with kwargs
                if hasattr(metric, "ascore"):
                    all_args = {
                        "user_input": sample.user_input,
                        "response": sample.response,
                        "retrieved_contexts": sample.retrieved_contexts,
                        "reference": sample.reference,
                    }
                    required_args = self.METRIC_ARGS.get(
                        metric.name,
                        ["user_input", "response", "retrieved_contexts"],
                    )
                    kwargs = {
                        k: v for k, v in all_args.items() if k in required_args and v is not None
                    }
                    result = await metric.ascore(**kwargs)
                elif hasattr(metric, "single_turn_ascore"):
                    # Legacy Ragas <0.4 API
                    result = await metric.single_turn_ascore(sample)
                else:
                    raise AttributeError(
                        f"{metric.__class__.__name__} does not support scoring API."
                    )

                # Handle MetricResult (v0.4+), score attr, or raw float
                if hasattr(result, "value"):
                    scores[metric.name] = result.value
                elif hasattr(result, "score"):
                    scores[metric.name] = result.score
                else:
                    scores[metric.name] = float(result)
            except Exception:
                # 개별 메트릭 실패 시 0.0으로 처리
                scores[metric.name] = 0.0

        return scores

    async def _evaluate_with_custom_metrics(
        self, dataset: Dataset, metrics: list[str]
    ) -> dict[str, TestCaseEvalResult]:
        """커스텀 메트릭으로 평가 수행.

        Args:
            dataset: 평가할 데이터셋
            metrics: 평가할 커스텀 메트릭 리스트

        Returns:
            테스트 케이스 ID별 평가 결과
            예: {"tc-001": TestCaseEvalResult(scores={"insurance_term_accuracy": 0.9})}
        """
        results: dict[str, TestCaseEvalResult] = {}

        # Initialize custom metric instances
        metric_instances = {}
        for metric_name in metrics:
            metric_class = self.CUSTOM_METRIC_MAP.get(metric_name)
            if metric_class:
                metric_instances[metric_name] = metric_class()

        # Evaluate each test case
        for test_case in dataset.test_cases:
            scores: dict[str, float] = {}

            # Track start time for this test case
            test_case_started_at = datetime.now()

            # Run each custom metric
            for metric_name, metric_instance in metric_instances.items():
                score = metric_instance.score(
                    answer=test_case.answer,
                    contexts=test_case.contexts,
                )
                scores[metric_name] = score

            # Track end time and calculate latency
            test_case_finished_at = datetime.now()
            latency_ms = int((test_case_finished_at - test_case_started_at).total_seconds() * 1000)

            results[test_case.id] = TestCaseEvalResult(
                scores=scores,
                tokens_used=0,  # Custom metrics don't use LLM
                prompt_tokens=0,
                completion_tokens=0,
                cost_usd=0.0,
                started_at=test_case_started_at,
                finished_at=test_case_finished_at,
                latency_ms=latency_ms,
            )

        return results
