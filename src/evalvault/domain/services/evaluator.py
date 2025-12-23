"""Ragas evaluation service."""

from dataclasses import dataclass
from datetime import datetime

from langchain_community.callbacks import get_openai_callback
from ragas import SingleTurnSample
from ragas.metrics import (
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
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
    """Ragas 평가 결과 (토큰 사용량 포함)."""

    scores: dict[str, float]
    tokens_used: int = 0


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
    }

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
            )
            run.results.append(test_case_result)
            total_tokens += eval_result.tokens_used

        # Set total tokens
        run.total_tokens = total_tokens

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

        # Initialize Ragas metrics
        ragas_metrics = []
        for metric_name in metrics:
            metric_class = self.METRIC_MAP.get(metric_name)
            if metric_class:
                ragas_metrics.append(metric_class())

        # Get LangChain LLM for Ragas
        ragas_llm = llm.as_ragas_llm()

        # Get embeddings if available (required for some metrics like answer_relevancy)
        ragas_embeddings = None
        if hasattr(llm, "as_ragas_embeddings"):
            ragas_embeddings = llm.as_ragas_embeddings()

        # Evaluate using Ragas with token tracking
        results: dict[str, TestCaseEvalResult] = {}
        for idx, sample in enumerate(ragas_samples):
            test_case_id = dataset.test_cases[idx].id
            scores: dict[str, float] = {}
            test_case_tokens = 0

            for metric in ragas_metrics:
                # Set LLM for the metric
                metric.llm = ragas_llm

                # Set embeddings if available (required for answer_relevancy, etc.)
                if ragas_embeddings is not None and hasattr(metric, "embeddings"):
                    metric.embeddings = ragas_embeddings

                # Evaluate the sample with token tracking
                with get_openai_callback() as cb:
                    score = await metric.single_turn_ascore(sample)
                    scores[metric.name] = score
                    test_case_tokens += cb.total_tokens

            results[test_case_id] = TestCaseEvalResult(
                scores=scores,
                tokens_used=test_case_tokens,
            )

        return results
