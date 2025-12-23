"""Ragas evaluation service."""

from dataclasses import dataclass
from datetime import datetime

from langchain_community.callbacks import get_openai_callback
from ragas import SingleTurnSample
from ragas.metrics.collections import (
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
    FactualCorrectness,
    SemanticSimilarity,
)

from evalvault.domain.entities import (
    Dataset,
    EvaluationRun,
    MetricScore,
    TestCaseResult,
)
from evalvault.ports.outbound.llm_port import LLMPort


@dataclass
class TestCaseEvalResult:
    """Ragas 평가 결과 (토큰 사용량, 비용, 타이밍 포함)."""

    scores: dict[str, float]
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    latency_ms: int = 0


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

    # Metrics that require embeddings
    EMBEDDING_REQUIRED_METRICS = {"answer_relevancy", "semantic_similarity"}

    async def evaluate(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,
        thresholds: dict[str, float] | None = None,
    ) -> EvaluationRun:
        """데이터셋을 Ragas로 평가.

        Args:
            dataset: 평가할 데이터셋
            metrics: 평가할 메트릭 리스트 (예: ['faithfulness', 'answer_relevancy'])
            llm: LLM 어댑터 (Ragas가 사용)
            thresholds: 메트릭별 임계값 (기본값: 0.7)

        Returns:
            평가 결과가 담긴 EvaluationRun
        """
        # Initialize evaluation run
        run = EvaluationRun(
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            model_name=llm.get_model_name(),
            started_at=datetime.now(),
            metrics_evaluated=metrics,
            thresholds=thresholds or {},
        )

        # Handle empty dataset
        if len(dataset.test_cases) == 0:
            run.finished_at = datetime.now()
            return run

        # Set default thresholds
        if thresholds is None:
            thresholds = dict.fromkeys(metrics, 0.7)

        # Evaluate with Ragas
        eval_results_by_test_case = await self._evaluate_with_ragas(
            dataset=dataset, metrics=metrics, llm=llm
        )

        # Aggregate results
        total_tokens = 0
        total_cost = 0.0
        for test_case in dataset.test_cases:
            eval_result = eval_results_by_test_case.get(
                test_case.id, TestCaseEvalResult(scores={})
            )

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
        self, dataset: Dataset, metrics: list[str], llm: LLMPort
    ) -> dict[str, TestCaseEvalResult]:
        """Ragas로 실제 평가 수행.

        Args:
            dataset: 평가할 데이터셋
            metrics: 평가할 메트릭 리스트
            llm: LLM 어댑터

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

        # Evaluate using Ragas with token, cost, and timing tracking
        results: dict[str, TestCaseEvalResult] = {}
        for idx, sample in enumerate(ragas_samples):
            test_case_id = dataset.test_cases[idx].id
            scores: dict[str, float] = {}
            test_case_tokens = 0
            test_case_prompt_tokens = 0
            test_case_completion_tokens = 0
            test_case_cost = 0.0

            # Track start time for this test case
            test_case_started_at = datetime.now()

            for metric in ragas_metrics:
                # Evaluate the sample with token and cost tracking
                with get_openai_callback() as cb:
                    # Build kwargs based on metric type
                    ascore_kwargs = {
                        "user_input": sample.user_input,
                        "response": sample.response,
                    }
                    # Add contexts for metrics that require it
                    if metric.name in ("faithfulness", "context_precision", "context_recall"):
                        ascore_kwargs["retrieved_contexts"] = sample.retrieved_contexts
                    # Add reference for metrics that require it
                    if metric.name in ("context_recall", "factual_correctness"):
                        ascore_kwargs["reference"] = sample.reference

                    result = await metric.ascore(**ascore_kwargs)
                    # Handle both MetricResult and float returns
                    if hasattr(result, "score"):
                        scores[metric.name] = result.score
                    else:
                        scores[metric.name] = float(result)
                    test_case_tokens += cb.total_tokens
                    test_case_prompt_tokens += cb.prompt_tokens
                    test_case_completion_tokens += cb.completion_tokens
                    test_case_cost += cb.total_cost

            # Track end time and calculate latency
            test_case_finished_at = datetime.now()
            latency_ms = int(
                (test_case_finished_at - test_case_started_at).total_seconds() * 1000
            )

            results[test_case_id] = TestCaseEvalResult(
                scores=scores,
                tokens_used=test_case_tokens,
                prompt_tokens=test_case_prompt_tokens,
                completion_tokens=test_case_completion_tokens,
                cost_usd=test_case_cost,
                started_at=test_case_started_at,
                finished_at=test_case_finished_at,
                latency_ms=latency_ms,
            )

        return results
