"""Ragas evaluation service."""

from __future__ import annotations

import importlib
import json
import logging
from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Any, Literal, overload

from pydantic import BaseModel, Field, field_validator
from ragas import SingleTurnSample

from evalvault.domain.entities import (
    ClaimLevelResult,
    ClaimVerdict,
    Dataset,
    EvaluationRun,
    MetricScore,
    TestCaseResult,
)
from evalvault.domain.metrics.confidence import ConfidenceScore
from evalvault.domain.metrics.contextual_relevancy import ContextualRelevancy
from evalvault.domain.metrics.entity_preservation import EntityPreservation
from evalvault.domain.metrics.insurance import InsuranceTermAccuracy
from evalvault.domain.metrics.no_answer import NoAnswerAccuracy
from evalvault.domain.metrics.retrieval_rank import MRR, NDCG, HitRate
from evalvault.domain.metrics.summary_accuracy import SummaryAccuracy
from evalvault.domain.metrics.summary_needs_followup import SummaryNeedsFollowup
from evalvault.domain.metrics.summary_non_definitive import SummaryNonDefinitive
from evalvault.domain.metrics.summary_risk_coverage import SummaryRiskCoverage
from evalvault.domain.metrics.text_match import ExactMatch, F1Score
from evalvault.domain.services import evaluation_cost as _evaluation_cost
from evalvault.domain.services import ragas_korean_prompts as _korean_prompts
from evalvault.domain.services.custom_metric_snapshot import build_custom_metric_snapshot
from evalvault.domain.services.dataset_preprocessor import DatasetPreprocessor
from evalvault.domain.services.faithfulness_fallback import FaithfulnessFallback
from evalvault.domain.services.metric_scoring import (
    MetricScorer,
    ParallelSampleOutcome,  # re-exported for backward compatibility (tests import here)
    TestCaseEvalResult,
)

__all__ = [
    "ParallelSampleOutcome",
    "RagasEvaluator",
    "SummaryFaithfulness",
    "TestCaseEvalResult",
]
from evalvault.domain.services.retriever_context import apply_retriever_to_dataset
from evalvault.ports.outbound.korean_nlp_port import KoreanNLPToolkitPort, RetrieverPort
from evalvault.ports.outbound.llm_factory_port import LLMFactoryPort
from evalvault.ports.outbound.llm_port import LLMPort


def _summary_faithfulness_structured_output_enabled() -> bool:
    """Return whether the Instructor structured-output wrapper is enabled.

    Reads ``use_structured_output_for_summary_faithfulness`` from the
    global :class:`Settings` lazily so the evaluator module avoids a
    hard dependency on the settings singleton. The flag defaults to
    ``False`` (D-S5d Part B), so existing behaviour stays byte-identical
    until a deployment opts in.
    """
    try:
        from evalvault.config.settings import get_settings

        return bool(
            getattr(get_settings(), "use_structured_output_for_summary_faithfulness", False)
        )
    except Exception:
        return False


def _patch_ragas_faithfulness_output() -> None:
    try:
        from ragas.metrics.collections import Faithfulness
    except Exception:
        try:
            from ragas.metrics import Faithfulness
        except Exception:
            return

    prompt = getattr(Faithfulness, "nli_statements_prompt", None)
    if prompt is None:
        return

    output_model = getattr(prompt, "output_model", None)
    if output_model is None:
        return

    class _StatementFaithfulnessAnswer(BaseModel):
        statement: str = Field(..., description="the original statement, word-by-word")
        reason: str = Field(..., description="the reason of the verdict")
        verdict: int = Field(..., description="the verdict(0/1) of the faithfulness.")

        @field_validator("verdict", mode="before")
        @classmethod
        def _coerce_verdict(cls, value):
            if isinstance(value, str):
                normalized = value.strip()
                if normalized.isdigit():
                    return int(normalized)
            return value

    class _NLIStatementOutput(BaseModel):
        statements: list[_StatementFaithfulnessAnswer]

    try:
        prompt.output_model = _NLIStatementOutput
    except Exception:
        return


def _import_metric(name: str) -> type[Any]:
    for module_name in ("ragas.metrics.collections", "ragas.metrics"):
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, name):
                if name == "Faithfulness":
                    _patch_ragas_faithfulness_output()
                return getattr(module, name)
        except ImportError:
            continue
    raise ImportError(f"Missing ragas metric: {name}")


def _import_optional_metric(names: list[str]) -> type[Any] | None:
    for name in names:
        try:
            return _import_metric(name)
        except Exception:
            continue
    return None


AnswerRelevancy = _import_metric("AnswerRelevancy")
ContextPrecision = _import_metric("ContextPrecision")
ContextRecall = _import_metric("ContextRecall")
FactualCorrectness = _import_metric("FactualCorrectness")
Faithfulness = _import_metric("Faithfulness")
SemanticSimilarity = _import_metric("SemanticSimilarity")
RagasSummaryScore = _import_optional_metric(["SummaryScore", "SummarizationScore"])

logger = logging.getLogger(__name__)


class SummaryFaithfulness(Faithfulness):
    """Faithfulness alias for summarization tasks."""

    name = "summary_faithfulness"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.name = "summary_faithfulness"


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
        "summary_score": RagasSummaryScore,
        "summary_faithfulness": SummaryFaithfulness,
    }

    # Custom 메트릭 매핑 (Ragas 외부 메트릭)
    CUSTOM_METRIC_MAP = {
        "insurance_term_accuracy": InsuranceTermAccuracy,
        "entity_preservation": EntityPreservation,
        "summary_accuracy": SummaryAccuracy,
        "summary_risk_coverage": SummaryRiskCoverage,
        "summary_non_definitive": SummaryNonDefinitive,
        "summary_needs_followup": SummaryNeedsFollowup,
        "exact_match": ExactMatch,
        "f1_score": F1Score,
        "no_answer_accuracy": NoAnswerAccuracy,
        "mrr": MRR,
        "ndcg": NDCG,
        "hit_rate": HitRate,
        "confidence_score": ConfidenceScore,
        "contextual_relevancy": ContextualRelevancy,
    }

    # Metrics that require embeddings
    EMBEDDING_REQUIRED_METRICS = {"answer_relevancy", "semantic_similarity"}

    # Faithfulness variants that can share fallback behavior
    FAITHFULNESS_METRICS = {"faithfulness", "summary_faithfulness"}

    # Metrics that require reference (ground_truth)
    REFERENCE_REQUIRED_METRICS = {
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

    # Metric-specific required arguments for Ragas 0.4+ ascore() API
    METRIC_ARGS = {
        "faithfulness": ["user_input", "response", "retrieved_contexts"],
        "answer_relevancy": ["user_input", "response"],
        "context_precision": ["user_input", "retrieved_contexts", "reference"],
        "context_recall": ["user_input", "retrieved_contexts", "reference"],
        "factual_correctness": ["response", "reference"],
        "semantic_similarity": ["response", "reference"],
        "summary_score": ["response", "reference_contexts"],
        "summary_faithfulness": ["user_input", "response", "retrieved_contexts"],
    }

    SUMMARY_SCORE_COEFF = 0.3
    SUMMARY_SCORE_COEFF_BY_DOMAIN = {
        "insurance": 0.15,
    }
    DEFAULT_THRESHOLD_FALLBACK = 0.7
    DEFAULT_METRIC_THRESHOLDS = {
        "summary_faithfulness": 0.9,
        "summary_score": 0.85,
        "entity_preservation": 0.9,
        "summary_accuracy": 0.9,
        "summary_risk_coverage": 0.9,
        "summary_non_definitive": 0.8,
        "summary_needs_followup": 0.8,
        "contextual_relevancy": 0.35,
    }
    LANGUAGE_SAMPLE_LIMIT = 5
    # Korean-language prompt overrides live in :mod:`ragas_korean_prompts`.
    # The class-level aliases preserve the existing public surface so that
    # callers and tests can keep using ``RagasEvaluator.<NAME>`` access.
    ANSWER_RELEVANCY_KOREAN_INSTRUCTION = _korean_prompts.ANSWER_RELEVANCY_KOREAN_INSTRUCTION
    ANSWER_RELEVANCY_KOREAN_EXAMPLES = _korean_prompts.ANSWER_RELEVANCY_KOREAN_EXAMPLES
    FACTUAL_CORRECTNESS_CLAIM_INSTRUCTION = _korean_prompts.FACTUAL_CORRECTNESS_CLAIM_INSTRUCTION
    FACTUAL_CORRECTNESS_NLI_INSTRUCTION = _korean_prompts.FACTUAL_CORRECTNESS_NLI_INSTRUCTION
    SUMMARY_SCORE_QUESTION_INSTRUCTION = _korean_prompts.SUMMARY_SCORE_QUESTION_INSTRUCTION
    SUMMARY_SCORE_ANSWER_INSTRUCTION = _korean_prompts.SUMMARY_SCORE_ANSWER_INSTRUCTION
    SUMMARY_SCORE_KEYPHRASE_INSTRUCTION = _korean_prompts.SUMMARY_SCORE_KEYPHRASE_INSTRUCTION
    SUMMARY_FAITHFULNESS_STATEMENT_INSTRUCTION = (
        _korean_prompts.SUMMARY_FAITHFULNESS_STATEMENT_INSTRUCTION
    )
    SUMMARY_FAITHFULNESS_NLI_INSTRUCTION = _korean_prompts.SUMMARY_FAITHFULNESS_NLI_INSTRUCTION
    FACTUAL_CORRECTNESS_CLAIM_EXAMPLES = _korean_prompts.FACTUAL_CORRECTNESS_CLAIM_EXAMPLES
    FACTUAL_CORRECTNESS_NLI_EXAMPLES = _korean_prompts.FACTUAL_CORRECTNESS_NLI_EXAMPLES

    # Pricing table lives in evaluation_cost (D-S5a extraction). The class
    # attribute is preserved so that ``self.MODEL_PRICING`` (and any subclass
    # override) continues to work.
    MODEL_PRICING = _evaluation_cost.MODEL_PRICING

    def __init__(
        self,
        *,
        preprocessor: DatasetPreprocessor | None = None,
        korean_toolkit: KoreanNLPToolkitPort | None = None,
        llm_factory: LLMFactoryPort | None = None,
    ) -> None:
        self._preprocessor = preprocessor or DatasetPreprocessor()
        self._korean_toolkit = korean_toolkit
        self._llm_factory = llm_factory
        self._active_llm_provider = None
        self._active_llm_model = None
        self._active_llm = None
        self._prompt_language = None
        self._faithfulness_fallback = FaithfulnessFallback(
            llm_factory=self._llm_factory,
            metric_map=self.METRIC_MAP,
            metric_args=self.METRIC_ARGS,
            summarize_error=self._summarize_ragas_error,
            korean_fallback=lambda s: self._fallback_korean_faithfulness(s, return_details=False),
        )
        self._metric_scorer = MetricScorer(
            faithfulness_metrics=self.FAITHFULNESS_METRICS,
            metric_args=self.METRIC_ARGS,
            custom_metric_map=self.CUSTOM_METRIC_MAP,
            reference_required_metrics=self.REFERENCE_REQUIRED_METRICS,
            active_llm_provider_getter=lambda: self._active_llm_provider,
            active_llm_getter=lambda: self._active_llm,
            prompt_language_getter=lambda: self._prompt_language,
            claim_level_getter=lambda: getattr(self, "_claim_level", False),
            korean_fallback_score=lambda s: self._fallback_korean_faithfulness(
                s, return_details=False
            ),
            korean_fallback_details=lambda s: self._fallback_korean_faithfulness(
                s, return_details=True
            ),
            faithfulness_fallback_score=self._score_faithfulness_with_fallback,
            calculate_cost=self._calculate_cost,
            summarize_error=self._summarize_ragas_error,
            use_structured_output_getter=_summary_faithfulness_structured_output_enabled,
        )

    @property
    def _faithfulness_ragas_failed(self) -> bool:
        """Latched faithfulness-failure flag.

        State now lives in :class:`MetricScorer` (D-S5c extraction); the
        property keeps ``evaluator._faithfulness_ragas_failed`` working for
        existing call sites and tests.
        """
        return self._metric_scorer.faithfulness_ragas_failed

    @_faithfulness_ragas_failed.setter
    def _faithfulness_ragas_failed(self, value: bool) -> None:
        self._metric_scorer.faithfulness_ragas_failed = bool(value)

    async def evaluate(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,
        thresholds: dict[str, float] | None = None,
        parallel: bool = False,
        batch_size: int = 5,
        retriever: RetrieverPort | None = None,
        retriever_top_k: int = 5,
        retriever_doc_ids: Sequence[str] | None = None,
        on_progress: Callable[[int, int, str], None] | None = None,
        prompt_overrides: dict[str, str] | None = None,
        claim_level: bool = False,
        language: str | None = None,
    ) -> EvaluationRun:
        """데이터셋을 Ragas로 평가.

        Args:
            dataset: 평가할 데이터셋
            metrics: 평가할 메트릭 리스트 (예: ['faithfulness', 'answer_relevancy'])
            llm: LLM 어댑터 (Ragas가 사용)
            thresholds: 메트릭별 임계값 (CLI에서 전달, 없으면
                dataset.thresholds 사용)
            parallel: 병렬 처리 활성화 여부 (기본값: False)
            batch_size: 병렬 처리 시 배치 크기 (기본값: 5)
            retriever: 컨텍스트가 비어 있을 때 사용할 retriever
            retriever_top_k: retriever 결과 상위 k개 사용
            retriever_doc_ids: retriever 결과 doc_id 인덱스 해석용 문서 ID 목록
            claim_level: Claim-level faithfulness 분석 활성화 여부 (기본값: False)

        Returns:
            평가 결과가 담긴 EvaluationRun

        Note:
            임계값 우선순위: CLI 옵션 > 데이터셋 내장 > 기본값(0.7)
        """
        self._claim_level = claim_level
        self._active_llm_provider = getattr(llm, "provider_name", None)
        self._active_llm_model = llm.get_model_name()
        self._active_llm = llm
        self._prompt_language = self._normalize_language_hint(language) if language else None
        if self._prompt_language is None:
            self._prompt_language = self._resolve_dataset_language(dataset)
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
                resolved_thresholds[metric] = self.default_threshold_for(metric)

        # Initialize evaluation run
        run = EvaluationRun(
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            model_name=llm.get_model_name(),
            started_at=datetime.now(),
            metrics_evaluated=metrics,
            thresholds=resolved_thresholds,
        )

        retrieval_metadata: dict[str, dict[str, Any]] = {}
        if retriever and dataset.test_cases:
            retrieval_metadata = apply_retriever_to_dataset(
                dataset=dataset,
                retriever=retriever,
                top_k=retriever_top_k,
                doc_ids=retriever_doc_ids,
            )
        run.retrieval_metadata = retrieval_metadata

        preprocess_report = self._preprocessor.apply(dataset, metrics=metrics)
        if preprocess_report.has_findings():
            run.tracker_metadata["dataset_preprocess"] = preprocess_report.to_dict()
        if run.retrieval_metadata:
            kept_ids = {test_case.id for test_case in dataset.test_cases}
            run.retrieval_metadata = {
                case_id: meta
                for case_id, meta in run.retrieval_metadata.items()
                if case_id in kept_ids
            }

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
        prompt_snapshots = {}
        if ragas_metrics:
            run.tracker_metadata["ragas_config"] = self._build_ragas_config(llm)
            (
                eval_results_by_test_case,
                override_status,
                prompt_snapshots,
            ) = await self._evaluate_with_ragas(
                dataset=dataset,
                metrics=ragas_metrics,
                llm=llm,
                parallel=parallel,
                batch_size=batch_size,
                on_progress=on_progress,
                prompt_overrides=prompt_overrides,
            )
            if override_status:
                run.tracker_metadata["ragas_prompt_overrides"] = override_status
            if prompt_snapshots:
                run.tracker_metadata["ragas_prompt_snapshots"] = prompt_snapshots
        elif prompt_overrides:
            logger.warning("Ragas prompt overrides provided but no Ragas metrics requested.")

        custom_snapshot = build_custom_metric_snapshot(self.CUSTOM_METRIC_MAP, metrics)
        if custom_snapshot:
            run.tracker_metadata["custom_metric_snapshot"] = custom_snapshot
            custom_prompt_snapshots = self._build_custom_prompt_snapshots(custom_snapshot)
            if custom_prompt_snapshots:
                run.tracker_metadata["custom_prompt_snapshots"] = custom_prompt_snapshots

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

                # Get claim details for this metric if available
                metric_claim_details = None
                if eval_result.claim_details and metric_name in eval_result.claim_details:
                    metric_claim_details = eval_result.claim_details[metric_name]

                metric_scores.append(
                    MetricScore(
                        name=metric_name,
                        score=score_value,
                        threshold=threshold,
                        claim_details=metric_claim_details,
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

    def _build_ragas_config(self, llm: LLMPort) -> dict[str, Any]:
        ragas_config: dict[str, Any] = {"embedding_model": None, "temperature": None}

        ragas_llm = None
        try:
            ragas_llm = llm.as_ragas_llm()
        except Exception:  # pragma: no cover - defensive for adapter mismatch
            ragas_llm = None
        if ragas_llm is not None:
            get_temperature = getattr(ragas_llm, "get_temperature", None)
            if callable(get_temperature):
                try:
                    ragas_config["temperature"] = get_temperature(1)
                except Exception:  # pragma: no cover - best-effort metadata
                    ragas_config["temperature"] = None

        embedding_model = None
        get_embedding_model_name = getattr(llm, "get_embedding_model_name", None)
        if callable(get_embedding_model_name):
            try:
                embedding_model = get_embedding_model_name()
            except Exception:  # pragma: no cover - best-effort metadata
                embedding_model = None

        if not embedding_model and hasattr(llm, "as_ragas_embeddings"):
            ragas_embeddings = None
            try:
                ragas_embeddings = llm.as_ragas_embeddings()
            except Exception:  # pragma: no cover - embeddings may be unavailable
                ragas_embeddings = None
            if ragas_embeddings is not None:
                embedding_model = getattr(ragas_embeddings, "model", None) or getattr(
                    ragas_embeddings, "model_name", None
                )

        if embedding_model:
            ragas_config["embedding_model"] = embedding_model
        return ragas_config

    async def _evaluate_with_ragas(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,
        parallel: bool = False,
        batch_size: int = 5,
        on_progress: Callable[[int, int, str], None] | None = None,
        prompt_overrides: dict[str, str] | None = None,
    ) -> tuple[dict[str, TestCaseEvalResult], dict[str, str], dict[str, dict[str, Any]]]:
        """Ragas로 실제 평가 수행.

        Args:
            dataset: 평가할 데이터셋
            metrics: 평가할 메트릭 리스트
            llm: LLM 어댑터
            parallel: 병렬 처리 여부
            batch_size: 병렬 처리 시 배치 크기

        Returns:
            (테스트 케이스 ID별 평가 결과, 프롬프트 오버라이드 적용 상태, 프롬프트 스냅샷)
            예: {"tc-001": TestCaseEvalResult(...)}
        """

        # Convert dataset to Ragas format
        ragas_samples = []
        for test_case in dataset.test_cases:
            sample = SingleTurnSample(
                user_input=test_case.question,
                response=test_case.answer,
                retrieved_contexts=test_case.contexts,
                reference_contexts=test_case.contexts,
                reference=test_case.ground_truth,
            )
            ragas_samples.append(sample)

        # Get Ragas LLM and embeddings
        ragas_llm = llm.as_ragas_llm()
        ragas_embeddings = None
        if hasattr(llm, "as_ragas_embeddings"):
            ragas_embeddings = llm.as_ragas_embeddings()

        # Initialize Ragas metrics with LLM (new Ragas API requires llm at init)
        domain_hint = dataset.metadata.get("domain") if isinstance(dataset.metadata, dict) else None
        summary_score_coeff = self._resolve_summary_score_coeff(domain_hint)
        ragas_metrics = []
        for metric_name in metrics:
            metric_class = self.METRIC_MAP.get(metric_name)
            if metric_class:
                # Pass embeddings for metrics that require it
                if metric_name in self.EMBEDDING_REQUIRED_METRICS and ragas_embeddings:
                    ragas_metrics.append(metric_class(llm=ragas_llm, embeddings=ragas_embeddings))
                elif metric_name == "summary_score":
                    ragas_metrics.append(
                        self._build_summary_score_metric(
                            metric_class,
                            ragas_llm,
                            summary_score_coeff,
                        )
                    )
                else:
                    ragas_metrics.append(metric_class(llm=ragas_llm))

        self._apply_answer_relevancy_prompt_defaults(
            dataset=dataset,
            ragas_metrics=ragas_metrics,
            prompt_overrides=prompt_overrides,
        )
        self._apply_summary_prompt_defaults(
            dataset=dataset,
            ragas_metrics=ragas_metrics,
            prompt_overrides=prompt_overrides,
        )
        self._apply_factual_correctness_prompt_defaults(
            dataset=dataset,
            ragas_metrics=ragas_metrics,
            prompt_overrides=prompt_overrides,
        )

        override_status = {}
        if prompt_overrides:
            override_status = self._apply_prompt_overrides(ragas_metrics, prompt_overrides)

        prompt_snapshots = self._collect_ragas_prompt_snapshots(
            ragas_metrics,
            prompt_overrides,
            override_status,
        )

        # 병렬 처리 vs 순차 처리
        if parallel and len(ragas_samples) > 1:
            return (
                await self._evaluate_parallel(
                    dataset=dataset,
                    ragas_samples=ragas_samples,
                    ragas_metrics=ragas_metrics,
                    llm=llm,
                    batch_size=batch_size,
                    on_progress=on_progress,
                ),
                override_status,
                prompt_snapshots,
            )
        return (
            await self._evaluate_sequential(
                dataset=dataset,
                ragas_samples=ragas_samples,
                ragas_metrics=ragas_metrics,
                llm=llm,
                on_progress=on_progress,
            ),
            override_status,
            prompt_snapshots,
        )

    def _apply_answer_relevancy_prompt_defaults(
        self,
        *,
        dataset: Dataset,
        ragas_metrics: list[Any],
        prompt_overrides: dict[str, str] | None,
    ) -> None:
        if not ragas_metrics:
            return
        if prompt_overrides and "answer_relevancy" in prompt_overrides:
            return
        resolved_language = self._resolve_dataset_language(dataset)
        if resolved_language == "en":
            return

        for metric in ragas_metrics:
            if getattr(metric, "name", None) != "answer_relevancy":
                continue
            self._apply_korean_answer_relevancy_prompt(metric)

    def _apply_summary_prompt_defaults(
        self,
        *,
        dataset: Dataset,
        ragas_metrics: list[Any],
        prompt_overrides: dict[str, str] | None,
    ) -> None:
        if not ragas_metrics:
            return
        if prompt_overrides and any(
            metric in prompt_overrides for metric in ("summary_score", "summary_faithfulness")
        ):
            return
        resolved_language = self._resolve_dataset_language(dataset)
        if resolved_language == "en":
            return

        for metric in ragas_metrics:
            metric_name = getattr(metric, "name", None)
            if metric_name == "summary_score":
                self._apply_korean_summary_score_prompts(metric)
            elif metric_name == "summary_faithfulness":
                self._apply_korean_summary_faithfulness_prompts(metric)

    def _apply_factual_correctness_prompt_defaults(
        self,
        *,
        dataset: Dataset,
        ragas_metrics: list[Any],
        prompt_overrides: dict[str, str] | None,
    ) -> None:
        if not ragas_metrics:
            return
        if prompt_overrides and "factual_correctness" in prompt_overrides:
            return
        resolved_language = self._resolve_dataset_language(dataset)
        if resolved_language == "en":
            return

        for metric in ragas_metrics:
            if getattr(metric, "name", None) != "factual_correctness":
                continue
            self._apply_korean_factual_correctness_prompts(metric)

    def _resolve_dataset_language(self, dataset: Dataset) -> str | None:
        if self._prompt_language:
            return self._prompt_language
        metadata = dataset.metadata if isinstance(dataset.metadata, dict) else {}
        for key in ("language", "lang", "locale"):
            normalized = self._normalize_language_hint(metadata.get(key))
            if normalized:
                return normalized

        languages = metadata.get("languages")
        if isinstance(languages, list | tuple | set):
            for entry in languages:
                normalized = self._normalize_language_hint(entry)
                if normalized:
                    return normalized

        english_found = False
        for test_case in dataset.test_cases[: self.LANGUAGE_SAMPLE_LIMIT]:
            if self._contains_korean(test_case.question) or self._contains_korean(test_case.answer):
                return "ko"
            if self._contains_latin(test_case.question) or self._contains_latin(test_case.answer):
                english_found = True
            for ctx in test_case.contexts:
                if self._contains_korean(ctx):
                    return "ko"
                if self._contains_latin(ctx):
                    english_found = True
        if english_found:
            return "en"
        return None

    @classmethod
    def _normalize_language_hint(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip().lower().replace("_", "-")
        if not text:
            return None
        if text in {"ko", "kor", "korean", "ko-kr", "kor-hang", "kr"}:
            return "ko"
        if text.startswith(("ko-", "kor-")):
            return "ko"
        if text in {"en", "eng", "english", "en-us", "en-gb"}:
            return "en"
        if text.startswith("en-"):
            return "en"
        return None

    def _apply_korean_answer_relevancy_prompt(self, metric: Any) -> bool:
        return _korean_prompts.apply_korean_answer_relevancy_prompt(metric)

    def _apply_korean_summary_score_prompts(self, metric: Any) -> bool:
        return _korean_prompts.apply_korean_summary_score_prompts(metric)

    def _apply_korean_summary_faithfulness_prompts(self, metric: Any) -> bool:
        return _korean_prompts.apply_korean_summary_faithfulness_prompts(metric)

    def _apply_korean_factual_correctness_prompts(self, metric: Any) -> bool:
        return _korean_prompts.apply_korean_factual_correctness_prompts(metric)

    def _apply_prompt_overrides(
        self,
        ragas_metrics: list[Any],
        prompt_overrides: dict[str, str],
    ) -> dict[str, str]:
        """Apply prompt overrides to Ragas metric instances."""

        statuses: dict[str, str] = {}
        for metric in ragas_metrics:
            metric_name = getattr(metric, "name", None)
            if not metric_name or metric_name not in prompt_overrides:
                continue
            prompt_text = prompt_overrides[metric_name]
            applied = self._override_metric_prompt(metric, prompt_text)
            if not applied and metric_name == "faithfulness":
                applied = self._override_faithfulness_prompt(metric, prompt_text)
            statuses[metric_name] = "applied" if applied else "unsupported"
            if not applied:
                logger.warning("Prompt override for metric '%s' could not be applied.", metric_name)
        return statuses

    @staticmethod
    def _override_metric_prompt(metric: Any, prompt_text: str) -> bool:
        """Best-effort override for metric prompt templates."""

        if hasattr(metric, "prompt"):
            target = metric.prompt
            if isinstance(target, str):
                metric.prompt = prompt_text
                return True
            if target is not None and hasattr(target, "template"):
                target.template = prompt_text
                return True
            if target is not None and hasattr(target, "instruction"):
                target.instruction = prompt_text
                return True

        if hasattr(metric, "question_generation"):
            target = getattr(metric, "question_generation", None)
            if isinstance(target, str):
                metric.question_generation = prompt_text
                return True
            if target is not None and hasattr(target, "template"):
                target.template = prompt_text
                return True
            if target is not None and hasattr(target, "instruction"):
                target.instruction = prompt_text
                return True

        candidates: list[tuple[str, Any]] = []
        for attr in dir(metric):
            if not attr.endswith("_prompt") or attr == "prompt":
                continue
            try:
                value = getattr(metric, attr)
            except Exception:
                continue
            if value is None:
                continue
            candidates.append((attr, value))

        if len(candidates) == 1:
            attr, value = candidates[0]
            if isinstance(value, str):
                setattr(metric, attr, prompt_text)
                return True
            if hasattr(value, "template"):
                value.template = prompt_text
                return True
            if hasattr(value, "instruction"):
                value.instruction = prompt_text
                return True

        return False

    @staticmethod
    def _override_faithfulness_prompt(metric: Any, prompt_text: str) -> bool:
        target = getattr(metric, "nli_statements_prompt", None)
        if target is None:
            return False
        if hasattr(target, "instruction"):
            target.instruction = prompt_text
            return True
        return False

    @staticmethod
    def _extract_prompt_text(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        for attr in ("template", "instruction", "prompt", "text"):
            try:
                candidate = getattr(value, attr)
            except Exception:
                continue
            if isinstance(candidate, str) and candidate.strip():
                return candidate
        return None

    def _collect_metric_prompt_text(self, metric: Any) -> str | None:
        for attr in ("prompt", "question_generation"):
            if hasattr(metric, attr):
                try:
                    value = getattr(metric, attr)
                except Exception:
                    continue
                text = self._extract_prompt_text(value)
                if text:
                    return text
        for attr in dir(metric):
            if not attr.endswith("_prompt") or attr == "prompt":
                continue
            try:
                value = getattr(metric, attr)
            except Exception:
                continue
            text = self._extract_prompt_text(value)
            if text:
                return text
        return None

    def _collect_ragas_prompt_snapshots(
        self,
        ragas_metrics: list[Any],
        prompt_overrides: dict[str, str] | None,
        override_status: dict[str, str],
    ) -> dict[str, dict[str, Any]]:
        snapshots: dict[str, dict[str, Any]] = {}
        for metric in ragas_metrics:
            metric_name = getattr(metric, "name", None)
            if not metric_name:
                continue
            requested = bool(prompt_overrides and metric_name in prompt_overrides)
            status = override_status.get(metric_name)
            source = "override" if status == "applied" else "default"

            prompts: dict[str, str] = {}
            if metric_name == "summary_score":
                prompts["question_generation"] = (
                    self._extract_prompt_text(getattr(metric, "question_generation_prompt", None))
                    or ""
                )
                prompts["answer_generation"] = (
                    self._extract_prompt_text(getattr(metric, "answer_generation_prompt", None))
                    or ""
                )
                prompts["extract_keyphrases"] = (
                    self._extract_prompt_text(getattr(metric, "extract_keyphrases_prompt", None))
                    or ""
                )
                prompts = {k: v for k, v in prompts.items() if v}
            elif metric_name == "summary_faithfulness":
                prompts["statement_generation"] = (
                    self._extract_prompt_text(getattr(metric, "statement_generator_prompt", None))
                    or ""
                )
                prompts["nli_statements"] = (
                    self._extract_prompt_text(getattr(metric, "nli_statements_prompt", None)) or ""
                )
                prompts = {k: v for k, v in prompts.items() if v}

            prompt_text = self._collect_metric_prompt_text(metric)
            if prompts:
                snapshots[str(metric_name)] = {
                    "prompts": prompts,
                    "source": source,
                    "override_requested": requested,
                    "override_status": status,
                }
            elif prompt_text:
                snapshots[str(metric_name)] = {
                    "prompt": prompt_text,
                    "source": source,
                    "override_requested": requested,
                    "override_status": status,
                }
        return snapshots

    async def _evaluate_sequential(
        self,
        dataset: Dataset,
        ragas_samples: list,
        ragas_metrics: list,
        llm: LLMPort,
        on_progress: Callable[[int, int, str], None] | None = None,
    ) -> dict[str, TestCaseEvalResult]:
        """순차 평가 — :class:`MetricScorer` 위임 (D-S5c)."""
        return await self._metric_scorer.evaluate_sequential(
            dataset=dataset,
            ragas_samples=ragas_samples,
            ragas_metrics=ragas_metrics,
            llm=llm,
            score_sample=lambda sample, metrics, tcid: self._score_single_sample(
                sample, metrics, test_case_id=tcid
            ),
            on_progress=on_progress,
        )

    async def _evaluate_parallel(
        self,
        dataset: Dataset,
        ragas_samples: list,
        ragas_metrics: list,
        llm: LLMPort,
        batch_size: int = 5,
        on_progress: Callable[[int, int, str], None] | None = None,
    ) -> dict[str, TestCaseEvalResult]:
        """병렬 평가 — :class:`MetricScorer` 위임 (D-S5c)."""
        return await self._metric_scorer.evaluate_parallel(
            dataset=dataset,
            ragas_samples=ragas_samples,
            ragas_metrics=ragas_metrics,
            llm=llm,
            score_sample=lambda sample, metrics, tcid: self._score_single_sample(
                sample, metrics, test_case_id=tcid
            ),
            batch_size=batch_size,
            on_progress=on_progress,
        )

    async def _score_single_sample(
        self,
        sample: SingleTurnSample,
        ragas_metrics: list,
        *,
        test_case_id: str = "",
    ) -> tuple[dict[str, float], dict[str, ClaimLevelResult]]:
        """단일 샘플에 대해 모든 메트릭 점수 계산 — :class:`MetricScorer` 위임 (D-S5c)."""
        return await self._metric_scorer.score_single_sample(
            sample, ragas_metrics, test_case_id=test_case_id
        )

    @classmethod
    def _resolve_summary_score_coeff(cls, domain: str | None) -> float:
        if not domain:
            return cls.SUMMARY_SCORE_COEFF
        normalized = str(domain).strip().lower()
        return cls.SUMMARY_SCORE_COEFF_BY_DOMAIN.get(normalized, cls.SUMMARY_SCORE_COEFF)

    def _build_custom_prompt_snapshots(self, snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
        entries = snapshot.get("metrics") if isinstance(snapshot, dict) else None
        if not isinstance(entries, list):
            return {}
        prompt_snapshot: dict[str, dict[str, Any]] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = entry.get("metric_name")
            if not isinstance(name, str) or not name:
                continue
            evaluation_process = entry.get("evaluation_process")
            if not isinstance(evaluation_process, str) or not evaluation_process:
                continue
            rules = entry.get("rules") if isinstance(entry.get("rules"), dict) else None
            prompts: dict[str, str] = {"rule": evaluation_process}
            if rules:
                prompts["rules"] = json.dumps(rules, ensure_ascii=False, indent=2)
            prompt_snapshot[name] = {
                "prompts": prompts,
                "source": "custom_rules",
                "rules": rules,
                "inputs": entry.get("inputs"),
            }
        return prompt_snapshot

    def _build_summary_score_metric(self, metric_class, ragas_llm, coeff: float | None = None):
        if coeff is None:
            coeff = self.SUMMARY_SCORE_COEFF
        try:
            return metric_class(llm=ragas_llm, coeff=coeff)
        except TypeError:
            return metric_class(llm=ragas_llm)

    @classmethod
    def default_threshold_for(cls, metric_name: str) -> float:
        return cls.DEFAULT_METRIC_THRESHOLDS.get(metric_name, cls.DEFAULT_THRESHOLD_FALLBACK)

    @overload
    def _fallback_korean_faithfulness(
        self,
        sample: SingleTurnSample,
        *,
        return_details: Literal[True],
    ) -> ClaimLevelResult | None: ...

    @overload
    def _fallback_korean_faithfulness(
        self,
        sample: SingleTurnSample,
        *,
        return_details: Literal[False] = False,
    ) -> float | None: ...

    def _fallback_korean_faithfulness(
        self, sample: SingleTurnSample, *, return_details: bool = False
    ) -> float | ClaimLevelResult | None:
        """Fallback faithfulness scoring for Korean text when Ragas fails.

        Args:
            sample: Ragas SingleTurnSample to evaluate
            return_details: If True, return ClaimLevelResult instead of float score

        Returns:
            If return_details=False: float score or None
            If return_details=True: ClaimLevelResult or None
        """
        if not sample.response or not sample.retrieved_contexts:
            return None

        text = f"{sample.response} {' '.join(sample.retrieved_contexts)}"
        if not self._contains_korean(text):
            return None

        if self._korean_toolkit is None:
            return None

        try:
            result = self._korean_toolkit.check_faithfulness(
                answer=sample.response,
                contexts=sample.retrieved_contexts,
            )
        except Exception:  # pragma: no cover - best effort fallback
            return None

        if return_details:
            return self._convert_to_claim_level_result(result, test_case_id="")

        score = getattr(result, "score", None)
        if score is None:
            return None
        try:
            return float(score)
        except (TypeError, ValueError):
            return None

    def _convert_to_claim_level_result(
        self, faithfulness_result: Any, test_case_id: str
    ) -> ClaimLevelResult:
        """Convert KoreanFaithfulnessChecker result to ClaimLevelResult.

        Args:
            faithfulness_result: FaithfulnessResult from KoreanNLPToolkit
            test_case_id: Test case ID for claim ID generation

        Returns:
            ClaimLevelResult with converted claim verdicts
        """
        claim_results = getattr(faithfulness_result, "claim_results", [])
        total_claims = getattr(faithfulness_result, "total_claims", len(claim_results))

        claims: list[ClaimVerdict] = []
        for idx, cr in enumerate(claim_results):
            claim_id = f"{test_case_id}-claim-{idx}" if test_case_id else f"claim-{idx}"
            claim_text = getattr(cr, "claim", "")
            is_faithful = getattr(cr, "is_faithful", False)
            coverage = getattr(cr, "coverage", 0.0)
            number_mismatch = getattr(cr, "number_mismatch", False)
            matched_keywords = getattr(cr, "matched_keywords", [])

            # Determine verdict string
            if is_faithful:
                verdict = "supported"
            elif number_mismatch:
                verdict = "not_supported"
            elif coverage >= 0.3:  # Partial support threshold
                verdict = "partially_supported"
            else:
                verdict = "not_supported"

            # Build reason
            reason_parts = []
            if number_mismatch:
                reason_parts.append("숫자 불일치 발견")
            elif not is_faithful:
                reason_parts.append(f"키워드 매칭률 {coverage:.0%}")
            if matched_keywords:
                reason_parts.append(f"매칭된 키워드: {', '.join(matched_keywords[:5])}")

            claims.append(
                ClaimVerdict(
                    claim_id=claim_id,
                    claim_text=claim_text,
                    verdict=verdict,
                    confidence=coverage,
                    reason=" | ".join(reason_parts) if reason_parts else None,
                    source_context_indices=None,  # Korean NLP doesn't track source indices
                )
            )

        # Count verdicts
        not_supported = sum(1 for c in claims if c.verdict == "not_supported")
        partially_supported = sum(1 for c in claims if c.verdict == "partially_supported")
        supported = total_claims - not_supported - partially_supported

        return ClaimLevelResult(
            total_claims=total_claims,
            supported_claims=supported,
            not_supported_claims=not_supported,
            partially_supported_claims=partially_supported,
            claims=claims,
            extraction_method="korean_nlp",
        )

    async def _score_summary_faithfulness_judge(self, sample: SingleTurnSample) -> float | None:
        """Summary-faithfulness LLM judge — :class:`MetricScorer` 위임 (D-S5c)."""
        return await self._metric_scorer.score_summary_faithfulness_judge(sample)

    @staticmethod
    def _parse_json_payload(text: str) -> dict[str, Any] | None:
        """JSON 페이로드 추출 — :class:`MetricScorer` 위임 (D-S5c)."""
        return MetricScorer._parse_json_payload(text)

    async def _score_faithfulness_with_fallback(
        self,
        sample: SingleTurnSample,
    ) -> float | None:
        """Delegate fallback scoring to :class:`FaithfulnessFallback` (D-S5b).

        Behaviour is preserved exactly; the helper owns the cached LLM,
        cached metric, and one-shot warning state that used to live on
        ``self``.
        """
        return await self._faithfulness_fallback.score(
            sample,
            self._active_llm_provider,
            self._active_llm_model,
        )

    @staticmethod
    def _contains_korean(text: str) -> bool:
        return any("\uac00" <= ch <= "\ud7a3" for ch in text)

    @staticmethod
    def _contains_latin(text: str) -> bool:
        return any("A" <= ch <= "Z" or "a" <= ch <= "z" for ch in text)

    @staticmethod
    def _summarize_ragas_error(exc: Exception) -> str:
        root = exc
        last_attempt = getattr(root, "last_attempt", None)
        if last_attempt is not None:
            try:
                last_exc = last_attempt.exception()
                if last_exc:
                    root = last_exc
            except Exception:
                pass
        cause = getattr(root, "__cause__", None)
        if cause:
            root = cause
        message = str(root).strip()
        if not message:
            return root.__class__.__name__
        first_line = message.splitlines()[0]
        if len(first_line) > 200:
            first_line = f"{first_line[:200]}..."
        return f"{root.__class__.__name__}: {first_line}"

    async def _evaluate_with_custom_metrics(
        self, dataset: Dataset, metrics: list[str]
    ) -> dict[str, TestCaseEvalResult]:
        """커스텀 메트릭 평가 — :class:`MetricScorer` 위임 (D-S5c)."""
        return await self._metric_scorer.evaluate_with_custom_metrics(dataset, metrics)

    def _score_custom_metric_with_metadata(
        self,
        metric_instance: Any,
        *,
        answer: str,
        contexts: list[str],
        metadata: dict[str, Any],
    ) -> float:
        """커스텀 메트릭 metadata 시그니처 어댑터 — :class:`MetricScorer` 위임 (D-S5c)."""
        return self._metric_scorer._score_custom_metric_with_metadata(
            metric_instance,
            answer=answer,
            contexts=contexts,
            metadata=metadata,
        )

    def _calculate_cost(self, model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost in USD based on model pricing.

        Thin wrapper that delegates to
        :func:`evalvault.domain.services.evaluation_cost.calculate_cost` while
        forwarding ``self.MODEL_PRICING`` so subclass-level pricing overrides
        keep their semantics (D-S5a extraction).
        """
        return _evaluation_cost.calculate_cost(
            model_name,
            prompt_tokens,
            completion_tokens,
            pricing=self.MODEL_PRICING,
        )
