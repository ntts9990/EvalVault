"""Custom-metric scoring loops extracted from :class:`RagasEvaluator` (D-S5c).

This module hosts the per-sample scoring iteration that drives Ragas and
custom metrics across a :class:`Dataset`. The extraction is a pure
relocation: the sequential/parallel loops, the single-sample scoring
fan-out, the summary-faithfulness LLM judge fallback, and the custom-metric
scoring helpers move here byte-identically.

Mutable run state — specifically the ``_faithfulness_ragas_failed`` flag
that latches once Ragas faithfulness scoring has degraded — also moves here
so :class:`RagasEvaluator` no longer has to track it inline. The evaluator
exposes a property-based shim that delegates to this module to keep the
public surface unchanged.

LLM prompt discipline (memory ``feedback_llm_prompt_discipline.md``): the
two summary-faithfulness judge prompts move byte-identical from the
evaluator module. No other LLM-facing prompt strings are owned here; the
Ragas metric classes still own their own prompts and only the LLM backing
them is delegated through callbacks.

T2 discipline (memory ``project_decision_authority_t2.md``): scoring
results emit T1 raw scores and T2 evaluation evidence only — no
promote/rollback semantics are introduced.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ragas import SingleTurnSample

from evalvault.domain.entities import (
    ClaimLevelResult,
    Dataset,
    TestCase,
)
from evalvault.domain.services.batch_executor import run_in_batches
from evalvault.domain.services.prompt_catalog import (
    PROMPT_REGISTRY,
    SummaryFaithfulnessVerdict,
)
from evalvault.ports.outbound.llm_port import LLMPort

logger = logging.getLogger(__name__)


# Backward-compatible aliases for prompt strings now owned by
# :mod:`evalvault.domain.services.prompt_catalog` (D-S5d Part A).
_SUMMARY_FAITHFULNESS_PROMPT_KO = PROMPT_REGISTRY["summary_faithfulness_judge_prompt_ko"]
_SUMMARY_FAITHFULNESS_PROMPT_EN = PROMPT_REGISTRY["summary_faithfulness_judge_prompt_en"]


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


ScoreSampleCallable = Callable[
    [Any, list, str],
    Awaitable[tuple[dict[str, float], dict[str, ClaimLevelResult]]],
]


class MetricScorer:
    """Encapsulates the scoring loops extracted from RagasEvaluator (D-S5c).

    Owns the sequential/parallel iteration over Ragas samples, the
    single-sample scoring fan-out, the custom-metric scoring loop, and the
    summary-faithfulness LLM judge fallback. The latched
    ``_faithfulness_ragas_failed`` flag lives here so callers no longer
    have to track it inline.

    Dependencies (class attributes, mutable run state, helper methods) are
    injected via constructor arguments rather than referenced through a
    back-pointer to keep the helper testable in isolation.
    """

    def __init__(
        self,
        *,
        faithfulness_metrics: set[str],
        metric_args: dict[str, list[str]],
        custom_metric_map: dict[str, type[Any]],
        reference_required_metrics: set[str],
        active_llm_provider_getter: Callable[[], str | None],
        active_llm_getter: Callable[[], LLMPort | None],
        prompt_language_getter: Callable[[], str | None],
        claim_level_getter: Callable[[], bool],
        korean_fallback_score: Callable[[SingleTurnSample], float | None],
        korean_fallback_details: Callable[[SingleTurnSample], ClaimLevelResult | None],
        faithfulness_fallback_score: Callable[[SingleTurnSample], Awaitable[float | None]],
        calculate_cost: Callable[[str, int, int], float],
        summarize_error: Callable[[Exception], str],
        use_structured_output_getter: Callable[[], bool] | None = None,
    ) -> None:
        self._faithfulness_metrics = faithfulness_metrics
        self._metric_args = metric_args
        self._custom_metric_map = custom_metric_map
        self._reference_required_metrics = reference_required_metrics
        self._active_llm_provider_getter = active_llm_provider_getter
        self._active_llm_getter = active_llm_getter
        self._prompt_language_getter = prompt_language_getter
        self._claim_level_getter = claim_level_getter
        self._korean_fallback_score = korean_fallback_score
        self._korean_fallback_details = korean_fallback_details
        self._faithfulness_fallback_score = faithfulness_fallback_score
        self._calculate_cost_cb = calculate_cost
        self._summarize_error = summarize_error
        self._use_structured_output_getter = use_structured_output_getter or (lambda: False)
        self._faithfulness_ragas_failed = False

    @property
    def faithfulness_ragas_failed(self) -> bool:
        return self._faithfulness_ragas_failed

    @faithfulness_ragas_failed.setter
    def faithfulness_ragas_failed(self, value: bool) -> None:
        self._faithfulness_ragas_failed = bool(value)

    async def evaluate_sequential(
        self,
        *,
        dataset: Dataset,
        ragas_samples: list,
        ragas_metrics: list,
        llm: LLMPort,
        score_sample: ScoreSampleCallable,
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
            scores, claim_details = await score_sample(sample, ragas_metrics, test_case_id)
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
            cost_usd = self._calculate_cost_cb(
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

    async def evaluate_parallel(
        self,
        *,
        dataset: Dataset,
        ragas_samples: list,
        ragas_metrics: list,
        llm: LLMPort,
        score_sample: ScoreSampleCallable,
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
                scores, claim_details = await score_sample(sample, ragas_metrics, test_case.id)
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
                    results[test_case_id].cost_usd = self._calculate_cost_cb(
                        llm.get_model_name(),
                        avg_prompt,
                        avg_completion,
                    )

        return results

    async def score_single_sample(
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
            if metric.name in self._faithfulness_metrics:
                if self._active_llm_provider_getter() == "ollama":
                    fallback_score = self._korean_fallback_score(sample)
                    if fallback_score is None:
                        fallback_score = await self._faithfulness_fallback_score(sample)
                    if fallback_score is not None:
                        scores[metric.name] = fallback_score
                        continue
                if self._faithfulness_ragas_failed:
                    if metric.name == "summary_faithfulness":
                        judge_score = await self._score_summary_faithfulness_judge(sample)
                        if judge_score is not None:
                            scores[metric.name] = judge_score
                            continue
                    fallback_score = await self._faithfulness_fallback_score(sample)
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
                    required_args = self._metric_args.get(
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
                if self._claim_level_getter() and metric.name in self._faithfulness_metrics:
                    claim_result = self._korean_fallback_details(sample)
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
                if fallback_score is None and metric.name in self._faithfulness_metrics:
                    if not self._faithfulness_ragas_failed:
                        logger.warning(
                            "Failed to score metric %s via Ragas (%s). "
                            "Switching to fallback scoring.",
                            metric.name,
                            self._summarize_error(e),
                        )
                        self._faithfulness_ragas_failed = True
                    # When claim_level is enabled, get detailed results
                    if self._claim_level_getter():
                        fallback_claim_result = self._korean_fallback_details(sample)
                        if isinstance(fallback_claim_result, ClaimLevelResult):
                            fallback_score = fallback_claim_result.support_rate
                            # Update claim IDs with test_case_id prefix
                            for claim in fallback_claim_result.claims:
                                if not claim.claim_id.startswith(test_case_id):
                                    idx = claim.claim_id.split("-")[-1]
                                    claim.claim_id = f"{test_case_id}-claim-{idx}"
                            claim_details[metric.name] = fallback_claim_result
                    else:
                        fallback_score = await self._faithfulness_fallback_score(sample)
                if fallback_score is not None:
                    scores[metric.name] = fallback_score
                else:
                    # 개별 메트릭 실패 시 로그 출력 후 0.0으로 처리
                    logger.error(f"Failed to score metric {metric.name}: {e}", exc_info=True)
                    scores[metric.name] = 0.0

        return scores, claim_details

    async def score_summary_faithfulness_judge(self, sample: SingleTurnSample) -> float | None:
        return await self._score_summary_faithfulness_judge(sample)

    async def _score_summary_faithfulness_judge(self, sample: SingleTurnSample) -> float | None:
        llm = self._active_llm_getter()
        if llm is None or not sample.response or not sample.retrieved_contexts:
            return None

        context = "\n\n".join(sample.retrieved_contexts)
        language = self._prompt_language_getter() or "ko"
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

        if self._use_structured_output_getter():
            structured_score = self._parse_with_instructor_schema(response_text)
            if structured_score is not None:
                return structured_score
            # Schema parsing failed (malformed or unexpected verdict);
            # fall through to the legacy parser so behaviour stays at
            # least as forgiving as the default-off path.

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
    def _parse_with_instructor_schema(text: str) -> float | None:
        """Parse the judge response via the Instructor structured-output schema.

        Returns the numeric score (1.0 supported / 0.0 unsupported) when
        the response cleanly validates against
        :class:`SummaryFaithfulnessVerdict`. Returns ``None`` when the
        payload is missing or fails validation so the caller can fall
        back to the legacy raw-JSON parser. This keeps the feature-off
        path byte-identical even when the feature flag is on but the
        LLM returns malformed output.
        """
        if not text:
            return None
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            return None
        try:
            verdict = SummaryFaithfulnessVerdict.model_validate_json(text[start : end + 1])
        except Exception:
            return None
        return verdict.to_score()

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

    async def evaluate_with_custom_metrics(
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
            metric_class = self._custom_metric_map.get(metric_name)
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
                if metric_name in self._reference_required_metrics:
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


__all__ = [
    "MetricScorer",
    "ParallelSampleOutcome",
    "ScoreSampleCallable",
    "TestCaseEvalResult",
]
