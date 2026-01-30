"""Ragas evaluation service."""

from __future__ import annotations

import asyncio
import importlib
import json
import logging
import math
from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass
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
    TestCase,
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
from evalvault.domain.services.batch_executor import run_in_batches
from evalvault.domain.services.custom_metric_snapshot import build_custom_metric_snapshot
from evalvault.domain.services.dataset_preprocessor import DatasetPreprocessor
from evalvault.domain.services.retriever_context import apply_retriever_to_dataset
from evalvault.ports.outbound.korean_nlp_port import KoreanNLPToolkitPort, RetrieverPort
from evalvault.ports.outbound.llm_factory_port import LLMFactoryPort
from evalvault.ports.outbound.llm_port import LLMPort

_SUMMARY_FAITHFULNESS_PROMPT_KO = (
    "당신은 요약 충실도 판정자입니다.\n"
    "컨텍스트와 요약을 보고 요약의 모든 주장이 컨텍스트에 의해 뒷받침되는지 판단하세요.\n"
    "숫자, 조건, 면책, 기간, 자격 등이 누락되거나 추가되거나 모순되면 verdict는 unsupported입니다.\n"
    'JSON만 반환: {"verdict": "supported|unsupported", "reason": "..."}\n\n'
    "컨텍스트:\n{context}\n\n요약:\n{summary}\n"
)
_SUMMARY_FAITHFULNESS_PROMPT_EN = (
    "You are a strict summarization faithfulness judge.\n"
    "Given the CONTEXT and SUMMARY, determine whether every claim in SUMMARY is supported by CONTEXT.\n"
    "If any numbers, conditions, exclusions, durations, or eligibility are missing, added, or "
    "contradicted, verdict is unsupported.\n"
    'Return JSON only: {"verdict": "supported|unsupported", "reason": "..."}\n\n'
    "CONTEXT:\n{context}\n\nSUMMARY:\n{summary}\n"
)


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
    claim_details: dict[str, ClaimLevelResult] | None = None  # metric_name -> ClaimLevelResult


@dataclass
class ParallelSampleOutcome:
    """Container for per-sample metadata collected during parallel evaluation."""

    scores: dict[str, float]
    started_at: datetime
    finished_at: datetime
    latency_ms: int
    error: Exception | None = None
    claim_details: dict[str, ClaimLevelResult] | None = None


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
    ANSWER_RELEVANCY_KOREAN_INSTRUCTION = (
        "다음 답변에 대해 질문을 생성하고, 답변이 회피적, "
        "모호, 불확실하면 noncommittal=1, 명확하면 0으로 표시하세요. "
        "질문은 답변과 동일한 언어(한국어)로 작성하세요."
    )
    ANSWER_RELEVANCY_KOREAN_EXAMPLES = [
        {
            "response": "사망 시 1억 5천만원까지 보장됩니다.",
            "question": "사망 시 보상 한도는 얼마인가요?",
            "noncommittal": 0,
        },
        {
            "response": "정확한 수치는 확인이 필요합니다.",
            "question": "보장 한도는 얼마인가요?",
            "noncommittal": 1,
        },
    ]
    FACTUAL_CORRECTNESS_CLAIM_INSTRUCTION = (
        "다음 문장을 독립적인 사실 주장으로 분해하세요. "
        "각 주장은 다른 주장과 독립적으로 "
        "참/거짓 판단이 가능해야 합니다. "
        "예시의 원자성 수준을 따르세요."
    )
    FACTUAL_CORRECTNESS_NLI_INSTRUCTION = (
        "주어진 컨텍스트를 보고 각 진술이 직접적으로 도출 가능한지 판단하세요. "
        "가능하면 verdict=1, 불가능하면 verdict=0을 JSON으로 반환하세요."
    )
    SUMMARY_SCORE_QUESTION_INSTRUCTION = (
        "다음 텍스트와 핵심 키워드를 기반으로, "
        "텍스트에 근거해 반드시 1로 답할 수 있는 폐쇄형 질문을 생성하세요. "
        "질문은 한국어로 작성하세요."
    )
    SUMMARY_SCORE_ANSWER_INSTRUCTION = (
        "다음 질문 목록에 대해, 제공된 요약이 각 질문에 답할 수 있으면 '1', "
        "그렇지 않으면 '0'을 JSON 배열로 반환하세요."
    )
    SUMMARY_SCORE_KEYPHRASE_INSTRUCTION = (
        "다음 텍스트에서 인물, 기관, 위치, 날짜/시간, 금액, 비율과 같은 핵심 키워드를 추출하세요."
    )
    SUMMARY_FAITHFULNESS_STATEMENT_INSTRUCTION = (
        "질문과 답변을 보고 각 문장을 이해 가능한 주장으로 분해하세요. "
        "각 주장은 대명사 없이 독립적으로 이해 가능해야 합니다."
    )
    SUMMARY_FAITHFULNESS_NLI_INSTRUCTION = (
        "주어진 컨텍스트를 보고 각 진술이 직접적으로 도출 가능한지 판단하세요. "
        "가능하면 verdict=1, 불가능하면 verdict=0을 JSON으로 반환하세요."
    )
    FACTUAL_CORRECTNESS_CLAIM_EXAMPLES = [
        {
            "response": "대인배상 I은 사망 시 1억 5천만원까지 보장합니다.",
            "claims": ["대인배상 I은 사망 시 1억 5천만원까지 보장한다."],
        },
        {
            "response": "마일리지 특약은 3천km 이하 주행 시 47% 할인됩니다.",
            "claims": ["마일리지 특약은 3천km 이하 주행 시 47% 할인된다."],
        },
    ]
    FACTUAL_CORRECTNESS_NLI_EXAMPLES = [
        {
            "context": "대인배상 I은 사망 시 1억 5천만원까지 보장한다.",
            "statements": [
                "대인배상 I은 사망 시 1억 5천만원까지 보장한다.",
                "대인배상 I은 부상 시 3천만원까지 보장한다.",
            ],
            "verdicts": [1, 0],
            "reasons": [
                "컨텍스트에 동일한 내용이 포함되어 있습니다.",
                "컨텍스트에 부상 보장 내용이 없습니다.",
            ],
        }
    ]

    # Estimated pricing (USD per 1M tokens) as of Jan 2025
    # Format: (input_price, output_price)
    MODEL_PRICING = {
        "gpt-4o": (2.50, 10.00),
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4-turbo": (10.00, 30.00),
        "gpt-3.5-turbo": (0.50, 1.50),
        "openai/gpt-4o": (2.50, 10.00),
        "openai/gpt-4o-mini": (0.15, 0.60),
        "gpt-5-nano": (5.00, 15.00),  # Hypothetical project model
        "openai/gpt-5-nano": (5.00, 15.00),
    }

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
        self._faithfulness_ragas_failed = False
        self._faithfulness_fallback_llm = None
        self._faithfulness_fallback_metric = None
        self._faithfulness_fallback_failed = False
        self._faithfulness_fallback_logged = False
        self._active_llm_provider = None
        self._active_llm_model = None
        self._active_llm = None
        self._prompt_language = None

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
        prompt = getattr(metric, "question_generation", None)
        if prompt is None:
            return False

        if isinstance(prompt, str):
            metric.question_generation = self.ANSWER_RELEVANCY_KOREAN_INSTRUCTION
            return True
        if not hasattr(prompt, "instruction"):
            return False
        prompt.instruction = self.ANSWER_RELEVANCY_KOREAN_INSTRUCTION

        input_model = getattr(prompt, "input_model", None)
        output_model = getattr(prompt, "output_model", None)
        if input_model and output_model:
            with suppress(Exception):  # pragma: no cover - best effort prompt tuning
                prompt.examples = [
                    (
                        input_model(response=example["response"]),
                        output_model(
                            question=example["question"],
                            noncommittal=example["noncommittal"],
                        ),
                    )
                    for example in self.ANSWER_RELEVANCY_KOREAN_EXAMPLES
                ]

        if hasattr(prompt, "language"):
            with suppress(Exception):  # pragma: no cover - best effort metadata
                prompt.language = "ko"
        return True

    def _apply_korean_summary_score_prompts(self, metric: Any) -> bool:
        question_prompt = getattr(metric, "question_generation_prompt", None)
        answer_prompt = getattr(metric, "answer_generation_prompt", None)
        keyphrase_prompt = getattr(metric, "extract_keyphrases_prompt", None)
        applied = False

        if question_prompt and hasattr(question_prompt, "instruction"):
            question_prompt.instruction = self.SUMMARY_SCORE_QUESTION_INSTRUCTION
            if hasattr(question_prompt, "language"):
                with suppress(Exception):
                    question_prompt.language = "ko"
            applied = True

        if answer_prompt and hasattr(answer_prompt, "instruction"):
            answer_prompt.instruction = self.SUMMARY_SCORE_ANSWER_INSTRUCTION
            if hasattr(answer_prompt, "language"):
                with suppress(Exception):
                    answer_prompt.language = "ko"
            applied = True

        if keyphrase_prompt and hasattr(keyphrase_prompt, "instruction"):
            keyphrase_prompt.instruction = self.SUMMARY_SCORE_KEYPHRASE_INSTRUCTION
            if hasattr(keyphrase_prompt, "language"):
                with suppress(Exception):
                    keyphrase_prompt.language = "ko"
            applied = True

        return applied

    def _apply_korean_summary_faithfulness_prompts(self, metric: Any) -> bool:
        statement_prompt = getattr(metric, "statement_generator_prompt", None)
        nli_prompt = getattr(metric, "nli_statements_prompt", None)
        applied = False

        if statement_prompt and hasattr(statement_prompt, "instruction"):
            statement_prompt.instruction = self.SUMMARY_FAITHFULNESS_STATEMENT_INSTRUCTION
            if hasattr(statement_prompt, "language"):
                with suppress(Exception):
                    statement_prompt.language = "ko"
            applied = True

        if nli_prompt and hasattr(nli_prompt, "instruction"):
            nli_prompt.instruction = self.SUMMARY_FAITHFULNESS_NLI_INSTRUCTION
            if hasattr(nli_prompt, "language"):
                with suppress(Exception):
                    nli_prompt.language = "ko"
            applied = True

        return applied

    def _apply_korean_factual_correctness_prompts(self, metric: Any) -> bool:
        claim_prompt = getattr(metric, "claim_decomposition_prompt", None)
        nli_prompt = getattr(metric, "nli_prompt", None)
        applied = False

        if claim_prompt and hasattr(claim_prompt, "instruction"):
            claim_prompt.instruction = self.FACTUAL_CORRECTNESS_CLAIM_INSTRUCTION
            input_model = getattr(claim_prompt, "input_model", None)
            output_model = getattr(claim_prompt, "output_model", None)
            if input_model and output_model:
                with suppress(Exception):  # pragma: no cover - best effort prompt tuning
                    claim_prompt.examples = [
                        (
                            input_model(response=example["response"]),
                            output_model(claims=example["claims"]),
                        )
                        for example in self.FACTUAL_CORRECTNESS_CLAIM_EXAMPLES
                    ]
            if hasattr(claim_prompt, "language"):
                with suppress(Exception):  # pragma: no cover - best effort metadata
                    claim_prompt.language = "ko"
            applied = True

        if nli_prompt and hasattr(nli_prompt, "instruction"):
            nli_prompt.instruction = self.FACTUAL_CORRECTNESS_NLI_INSTRUCTION
            input_model = getattr(nli_prompt, "input_model", None)
            output_model = getattr(nli_prompt, "output_model", None)
            if input_model and output_model:
                with suppress(Exception):  # pragma: no cover - best effort prompt tuning
                    nli_prompt.examples = [
                        (
                            input_model(
                                context=example["context"],
                                statements=example["statements"],
                            ),
                            output_model(
                                statements=[
                                    {
                                        "statement": statement,
                                        "reason": reason,
                                        "verdict": verdict,
                                    }
                                    for statement, reason, verdict in zip(
                                        example["statements"],
                                        example["reasons"],
                                        example["verdicts"],
                                        strict=True,
                                    )
                                ]
                            ),
                        )
                        for example in self.FACTUAL_CORRECTNESS_NLI_EXAMPLES
                    ]
            if hasattr(nli_prompt, "language"):
                with suppress(Exception):  # pragma: no cover - best effort metadata
                    nli_prompt.language = "ko"
            applied = True

        return applied

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
        """순차 평가 (기존 로직)."""
        results: dict[str, TestCaseEvalResult] = {}
        total = len(ragas_samples)

        for idx, sample in enumerate(ragas_samples):
            test_case_id = dataset.test_cases[idx].id

            # Reset token tracking before each test case
            if hasattr(llm, "reset_token_usage"):
                llm.reset_token_usage()

            # 단일 테스트 케이스 평가
            test_case_started_at = datetime.now()
            scores, claim_details = await self._score_single_sample(
                sample, ragas_metrics, test_case_id=test_case_id
            )
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

            # Calculate cost
            cost_usd = self._calculate_cost(
                llm.get_model_name(), test_case_prompt_tokens, test_case_completion_tokens
            )

            results[test_case_id] = TestCaseEvalResult(
                scores=scores,
                tokens_used=test_case_tokens,
                prompt_tokens=test_case_prompt_tokens,
                completion_tokens=test_case_completion_tokens,
                cost_usd=cost_usd,
                started_at=test_case_started_at,
                finished_at=test_case_finished_at,
                latency_ms=latency_ms,
                claim_details=claim_details if claim_details else None,
            )

            if on_progress:
                on_progress(idx + 1, total, f"Evaluated {test_case_id}")

        return results

    async def _evaluate_parallel(
        self,
        dataset: Dataset,
        ragas_samples: list,
        ragas_metrics: list,
        llm: LLMPort,
        batch_size: int = 5,
        on_progress: Callable[[int, int, str], None] | None = None,
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
        completed_count = 0

        async def worker(pair: tuple[TestCase, Any]):
            test_case, sample = pair
            started_at = datetime.now()
            error: Exception | None = None
            claim_details: dict[str, ClaimLevelResult] | None = None
            try:
                scores, claim_details = await self._score_single_sample(
                    sample, ragas_metrics, test_case_id=test_case.id
                )
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

            nonlocal completed_count
            completed_count += 1
            if on_progress:
                on_progress(completed_count, total_samples, f"Evaluated {test_case.id}")

            return (
                test_case.id,
                ParallelSampleOutcome(
                    scores=scores,
                    started_at=started_at,
                    finished_at=finished_at,
                    latency_ms=latency_ms,
                    error=error,
                    claim_details=claim_details if claim_details else None,
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
                claim_details=sample_outcome.claim_details,
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
                    results[test_case_id].cost_usd = self._calculate_cost(
                        llm.get_model_name(),
                        avg_prompt,
                        avg_completion,
                    )

        return results

    async def _score_single_sample(
        self,
        sample: SingleTurnSample,
        ragas_metrics: list,
        *,
        test_case_id: str = "",
    ) -> tuple[dict[str, float], dict[str, ClaimLevelResult]]:
        """단일 샘플에 대해 모든 메트릭 점수 계산.

        Args:
            sample: 평가할 Ragas 샘플
            ragas_metrics: 메트릭 인스턴스 목록
            test_case_id: 테스트 케이스 ID (claim ID 생성용)

        Returns:
            (메트릭명: 점수 딕셔너리, 메트릭명: ClaimLevelResult 딕셔너리)
        """
        scores: dict[str, float] = {}
        claim_details: dict[str, ClaimLevelResult] = {}

        for metric in ragas_metrics:
            if metric.name in self.FAITHFULNESS_METRICS:
                if self._active_llm_provider == "ollama":
                    fallback_score = self._fallback_korean_faithfulness(
                        sample, return_details=False
                    )
                    if fallback_score is None:
                        fallback_score = await self._score_faithfulness_with_fallback(sample)
                    if fallback_score is not None:
                        scores[metric.name] = fallback_score
                        continue
                if self._faithfulness_ragas_failed:
                    if metric.name == "summary_faithfulness":
                        judge_score = await self._score_summary_faithfulness_judge(sample)
                        if judge_score is not None:
                            scores[metric.name] = judge_score
                            continue
                    fallback_score = await self._score_faithfulness_with_fallback(sample)
                    if fallback_score is not None:
                        scores[metric.name] = fallback_score
                        continue
            try:
                # Ragas >=0.4 uses ascore() with kwargs
                if hasattr(metric, "ascore"):
                    all_args = {
                        "user_input": sample.user_input,
                        "response": sample.response,
                        "retrieved_contexts": sample.retrieved_contexts,
                        "reference_contexts": sample.reference_contexts,
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
                    ragas_input = kwargs
                elif hasattr(metric, "single_turn_ascore"):
                    # Legacy Ragas <0.4 API
                    result = await metric.single_turn_ascore(sample)
                    ragas_input = {
                        "user_input": sample.user_input,
                        "response": sample.response,
                        "retrieved_contexts": sample.retrieved_contexts,
                        "reference_contexts": sample.reference_contexts,
                        "reference": sample.reference,
                    }
                else:
                    raise AttributeError(
                        f"{metric.__class__.__name__} does not support scoring API."
                    )

                # Handle MetricResult (v0.4+), score attr, or raw float
                if hasattr(result, "value"):
                    score_value = result.value
                elif hasattr(result, "score"):
                    score_value = result.score
                else:
                    score_value = result

                try:
                    score_value = float(score_value)
                except (TypeError, ValueError):
                    logger.warning(
                        "Metric %s returned non-numeric score (%r). Using 0.0.",
                        metric.name,
                        score_value,
                    )
                    score_value = 0.0

                if math.isnan(score_value):
                    if metric.name == "summary_faithfulness":
                        judge_score = await self._score_summary_faithfulness_judge(sample)
                        if judge_score is not None:
                            scores[metric.name] = judge_score
                            continue
                    logger.warning(
                        "Metric %s returned NaN. Using 0.0. ragas_input=%s ragas_output=%r",
                        metric.name,
                        ragas_input,
                        result,
                    )
                    score_value = 0.0

                scores[metric.name] = score_value

                # Collect claim details when claim_level is enabled for faithfulness metrics
                if (
                    getattr(self, "_claim_level", False)
                    and metric.name in self.FAITHFULNESS_METRICS
                ):
                    claim_result = self._fallback_korean_faithfulness(sample, return_details=True)
                    if isinstance(claim_result, ClaimLevelResult):
                        # Update claim IDs with test_case_id prefix
                        for claim in claim_result.claims:
                            if not claim.claim_id.startswith(test_case_id):
                                idx = claim.claim_id.split("-")[-1]
                                claim.claim_id = f"{test_case_id}-claim-{idx}"
                        claim_details[metric.name] = claim_result

            except Exception as e:
                fallback_score = None
                fallback_claim_result = None
                if metric.name == "summary_faithfulness":
                    fallback_score = await self._score_summary_faithfulness_judge(sample)
                if fallback_score is None and metric.name in self.FAITHFULNESS_METRICS:
                    if not self._faithfulness_ragas_failed:
                        logger.warning(
                            "Failed to score metric %s via Ragas (%s). "
                            "Switching to fallback scoring.",
                            metric.name,
                            self._summarize_ragas_error(e),
                        )
                        self._faithfulness_ragas_failed = True
                    # When claim_level is enabled, get detailed results
                    if getattr(self, "_claim_level", False):
                        fallback_claim_result = self._fallback_korean_faithfulness(
                            sample, return_details=True
                        )
                        if isinstance(fallback_claim_result, ClaimLevelResult):
                            fallback_score = fallback_claim_result.support_rate
                            # Update claim IDs with test_case_id prefix
                            for claim in fallback_claim_result.claims:
                                if not claim.claim_id.startswith(test_case_id):
                                    idx = claim.claim_id.split("-")[-1]
                                    claim.claim_id = f"{test_case_id}-claim-{idx}"
                            claim_details[metric.name] = fallback_claim_result
                    else:
                        fallback_score = await self._score_faithfulness_with_fallback(sample)
                if fallback_score is not None:
                    scores[metric.name] = fallback_score
                else:
                    # 개별 메트릭 실패 시 로그 출력 후 0.0으로 처리
                    logger.error(f"Failed to score metric {metric.name}: {e}", exc_info=True)
                    scores[metric.name] = 0.0

        return scores, claim_details

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
        llm = self._active_llm
        if llm is None or not sample.response or not sample.retrieved_contexts:
            return None

        context = "\n\n".join(sample.retrieved_contexts)
        language = self._prompt_language or "ko"
        template = (
            _SUMMARY_FAITHFULNESS_PROMPT_EN if language == "en" else _SUMMARY_FAITHFULNESS_PROMPT_KO
        )
        prompt = template.format(context=context, summary=sample.response)

        try:
            response_text = await asyncio.to_thread(llm.generate_text, prompt, json_mode=True)
        except NotImplementedError:
            try:
                response_text = await llm.agenerate_text(prompt)
            except Exception:
                return None
        except Exception:
            return None

        payload = self._parse_json_payload(response_text)
        if not payload:
            return None

        verdict = str(payload.get("verdict", "")).strip().lower()
        if verdict == "supported":
            return 1.0
        if verdict == "unsupported":
            return 0.0
        return None

    @staticmethod
    def _parse_json_payload(text: str) -> dict[str, Any] | None:
        if not text:
            return None
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None

    async def _score_faithfulness_with_fallback(
        self,
        sample: SingleTurnSample,
    ) -> float | None:
        metric = self._get_faithfulness_fallback_metric()
        if metric is None:
            return self._fallback_korean_faithfulness(sample, return_details=False)

        try:
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
                kwargs = {k: v for k, v in all_args.items() if k in required_args and v is not None}
                result = await metric.ascore(**kwargs)
            elif hasattr(metric, "single_turn_ascore"):
                result = await metric.single_turn_ascore(sample)
            else:
                raise AttributeError(f"{metric.__class__.__name__} does not support scoring API.")

            if hasattr(result, "value"):
                score_value = result.value
            elif hasattr(result, "score"):
                score_value = result.score
            else:
                score_value = result

            if score_value is None:
                raise ValueError("Metric returned None")
            score_value = float(score_value)
            if math.isnan(score_value):
                raise ValueError("Metric returned NaN")
            return score_value
        except Exception as exc:
            if not self._faithfulness_fallback_failed:
                logger.warning(
                    "Faithfulness fallback LLM failed (%s). Using Korean fallback.",
                    self._summarize_ragas_error(exc),
                )
                self._faithfulness_fallback_failed = True
            return self._fallback_korean_faithfulness(sample, return_details=False)

    def _get_faithfulness_fallback_metric(self):
        if self._faithfulness_fallback_failed:
            return None
        if self._faithfulness_fallback_metric is not None:
            return self._faithfulness_fallback_metric

        llm = self._get_faithfulness_fallback_llm()
        if llm is None:
            return None

        metric_class = self.METRIC_MAP.get("faithfulness")
        if not metric_class:
            return None
        try:
            self._faithfulness_fallback_metric = metric_class(llm=llm.as_ragas_llm())
            return self._faithfulness_fallback_metric
        except Exception as exc:
            if not self._faithfulness_fallback_failed:
                logger.warning(
                    "Faithfulness fallback metric init failed (%s).",
                    self._summarize_ragas_error(exc),
                )
                self._faithfulness_fallback_failed = True
            return None

    def _get_faithfulness_fallback_llm(self) -> LLMPort | None:
        if self._faithfulness_fallback_failed:
            return None
        if self._faithfulness_fallback_llm is not None:
            return self._faithfulness_fallback_llm
        if self._llm_factory is None:
            return None

        try:
            llm = self._llm_factory.create_faithfulness_fallback(
                self._active_llm_provider,
                self._active_llm_model,
            )
        except Exception as exc:
            if not self._faithfulness_fallback_failed:
                logger.warning(
                    "Faithfulness fallback LLM init failed (%s).",
                    self._summarize_ragas_error(exc),
                )
                self._faithfulness_fallback_failed = True
            return None

        if llm is None:
            return None

        self._faithfulness_fallback_llm = llm
        if not self._faithfulness_fallback_logged:
            provider = getattr(llm, "provider_name", None)
            model = llm.get_model_name()
            logger.warning(
                "Faithfulness fallback LLM enabled: %s/%s",
                provider,
                model,
            )
            self._faithfulness_fallback_logged = True
        return llm

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
                # Check if metric requires ground_truth
                if metric_name in self.REFERENCE_REQUIRED_METRICS:
                    if not test_case.ground_truth:
                        logger.warning(
                            "Metric %s requires ground_truth but test case %s has none. "
                            "Skipping metric.",
                            metric_name,
                            test_case.id,
                        )
                        scores[metric_name] = 0.0
                        continue
                    score = metric_instance.score(
                        answer=test_case.answer,
                        ground_truth=test_case.ground_truth,
                        contexts=test_case.contexts,
                    )
                else:
                    if metric_name == "contextual_relevancy":
                        score = metric_instance.score(
                            question=test_case.question,
                            answer=test_case.answer,
                            ground_truth=test_case.ground_truth,
                            contexts=test_case.contexts,
                        )
                    else:
                        score = self._score_custom_metric_with_metadata(
                            metric_instance,
                            answer=test_case.answer,
                            contexts=test_case.contexts,
                            metadata=test_case.metadata,
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

    def _score_custom_metric_with_metadata(
        self,
        metric_instance: Any,
        *,
        answer: str,
        contexts: list[str],
        metadata: dict[str, Any],
    ) -> float:
        try:
            return float(metric_instance.score(answer=answer, contexts=contexts, metadata=metadata))
        except TypeError:
            return float(metric_instance.score(answer=answer, contexts=contexts))

    def _calculate_cost(self, model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost in USD based on model pricing."""
        if "ollama" in model_name:
            return 0.0
        # Find matching model key (exact or substring match)
        price_key = "openai/gpt-4o"  # Default fallback
        for key in self.MODEL_PRICING:
            if key in model_name or model_name in key:
                price_key = key
                break

        input_price, output_price = self.MODEL_PRICING.get(price_key, (0.0, 0.0))

        cost = (prompt_tokens / 1_000_000 * input_price) + (
            completion_tokens / 1_000_000 * output_price
        )
        return cost
