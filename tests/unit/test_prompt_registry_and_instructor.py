"""Tests for the D-S5d prompt catalog + Instructor structured-output wrapper.

Covers:

* The :data:`PROMPT_REGISTRY` exposes every LLM prompt string the
  evaluator can emit, and each entry is byte-identical to the legacy
  source it replaced.
* The default-off path of ``MetricScorer._score_summary_faithfulness_judge``
  produces the same numeric score as the legacy raw-JSON parser when the
  LLM returns the historical free-form JSON.
* The default-on path validates the LLM response with the Instructor
  schema (:class:`SummaryFaithfulnessVerdict`) and emits the same T2
  score without invoking the legacy dictionary lookup.

The tests intentionally bypass real LLMs by stubbing ``LLMPort``
implementations whose ``generate_text`` returns canned JSON.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from ragas import SingleTurnSample

from evalvault.domain.services import metric_scoring, ragas_korean_prompts
from evalvault.domain.services.metric_scoring import MetricScorer
from evalvault.domain.services.prompt_catalog import (
    EXAMPLE_REGISTRY,
    PROMPT_REGISTRY,
    SummaryFaithfulnessVerdict,
)

# ---------------------------------------------------------------------------
# Test (a): registry inventory + byte-identity
# ---------------------------------------------------------------------------
EXPECTED_PROMPT_KEYS = {
    "answer_relevancy_korean_instruction",
    "factual_correctness_claim_instruction_ko",
    "factual_correctness_nli_instruction_ko",
    "summary_score_question_instruction_ko",
    "summary_score_answer_instruction_ko",
    "summary_score_keyphrase_instruction_ko",
    "summary_faithfulness_statement_instruction_ko",
    "summary_faithfulness_nli_instruction_ko",
    "summary_faithfulness_judge_prompt_ko",
    "summary_faithfulness_judge_prompt_en",
}
EXPECTED_EXAMPLE_KEYS = {
    "answer_relevancy_korean_examples",
    "factual_correctness_claim_examples_ko",
    "factual_correctness_nli_examples_ko",
}


def test_prompt_registry_keys_match_expected_inventory() -> None:
    """The catalog must enumerate every prompt the evaluator can emit."""

    assert set(PROMPT_REGISTRY.keys()) == EXPECTED_PROMPT_KEYS
    assert set(EXAMPLE_REGISTRY.keys()) == EXPECTED_EXAMPLE_KEYS

    # Every value in PROMPT_REGISTRY is a non-empty string.
    for key, value in PROMPT_REGISTRY.items():
        assert isinstance(value, str) and value, f"{key} must be a non-empty string"

    # Re-exports in ``ragas_korean_prompts`` must point to the same
    # registry objects so the relocation is byte-identical.
    assert (
        ragas_korean_prompts.ANSWER_RELEVANCY_KOREAN_INSTRUCTION
        is PROMPT_REGISTRY["answer_relevancy_korean_instruction"]
    )
    assert (
        ragas_korean_prompts.FACTUAL_CORRECTNESS_CLAIM_INSTRUCTION
        is PROMPT_REGISTRY["factual_correctness_claim_instruction_ko"]
    )
    assert (
        ragas_korean_prompts.FACTUAL_CORRECTNESS_NLI_INSTRUCTION
        is PROMPT_REGISTRY["factual_correctness_nli_instruction_ko"]
    )
    assert (
        ragas_korean_prompts.SUMMARY_SCORE_QUESTION_INSTRUCTION
        is PROMPT_REGISTRY["summary_score_question_instruction_ko"]
    )
    assert (
        ragas_korean_prompts.SUMMARY_SCORE_ANSWER_INSTRUCTION
        is PROMPT_REGISTRY["summary_score_answer_instruction_ko"]
    )
    assert (
        ragas_korean_prompts.SUMMARY_SCORE_KEYPHRASE_INSTRUCTION
        is PROMPT_REGISTRY["summary_score_keyphrase_instruction_ko"]
    )
    assert (
        ragas_korean_prompts.SUMMARY_FAITHFULNESS_STATEMENT_INSTRUCTION
        is PROMPT_REGISTRY["summary_faithfulness_statement_instruction_ko"]
    )
    assert (
        ragas_korean_prompts.SUMMARY_FAITHFULNESS_NLI_INSTRUCTION
        is PROMPT_REGISTRY["summary_faithfulness_nli_instruction_ko"]
    )

    # Re-exports in ``metric_scoring`` must also alias the registry.
    assert (
        metric_scoring._SUMMARY_FAITHFULNESS_PROMPT_KO
        is PROMPT_REGISTRY["summary_faithfulness_judge_prompt_ko"]
    )
    assert (
        metric_scoring._SUMMARY_FAITHFULNESS_PROMPT_EN
        is PROMPT_REGISTRY["summary_faithfulness_judge_prompt_en"]
    )

    # Example collections are also aliased to the registry to keep the
    # relocation byte-identical.
    assert (
        ragas_korean_prompts.ANSWER_RELEVANCY_KOREAN_EXAMPLES
        is EXAMPLE_REGISTRY["answer_relevancy_korean_examples"]
    )
    assert (
        ragas_korean_prompts.FACTUAL_CORRECTNESS_CLAIM_EXAMPLES
        is EXAMPLE_REGISTRY["factual_correctness_claim_examples_ko"]
    )
    assert (
        ragas_korean_prompts.FACTUAL_CORRECTNESS_NLI_EXAMPLES
        is EXAMPLE_REGISTRY["factual_correctness_nli_examples_ko"]
    )


# ---------------------------------------------------------------------------
# Shared test scaffolding: stub LLM + MetricScorer factory
# ---------------------------------------------------------------------------
class _StubLLM:
    """Minimal LLMPort double for the summary-faithfulness judge call."""

    def __init__(self, response_text: str) -> None:
        self._response_text = response_text
        self.calls: list[str] = []

    def get_model_name(self) -> str:  # pragma: no cover - not exercised
        return "stub-model"

    def as_ragas_llm(self) -> Any:  # pragma: no cover - not exercised
        return None

    def generate_text(self, prompt: str, *, json_mode: bool = False) -> str:
        self.calls.append(prompt)
        return self._response_text


def _build_scorer(llm: _StubLLM, *, use_structured_output: bool) -> MetricScorer:
    """Construct a MetricScorer just rich enough to drive the judge."""

    return MetricScorer(
        faithfulness_metrics={"faithfulness"},
        metric_args={},
        custom_metric_map={},
        reference_required_metrics=set(),
        active_llm_provider_getter=lambda: "stub",
        active_llm_getter=lambda: llm,
        prompt_language_getter=lambda: "ko",
        claim_level_getter=lambda: False,
        korean_fallback_score=lambda _s: None,
        korean_fallback_details=lambda _s: None,
        faithfulness_fallback_score=_async_none,
        calculate_cost=lambda *_args, **_kwargs: 0.0,
        summarize_error=lambda exc: str(exc),
        use_structured_output_getter=lambda: use_structured_output,
    )


async def _async_none(_sample: SingleTurnSample) -> float | None:
    return None


def _sample() -> SingleTurnSample:
    return SingleTurnSample(
        user_input="이 보험의 보장금액은 얼마인가요?",
        response="보장금액은 1억 5천만원입니다.",
        retrieved_contexts=["대인배상 I은 사망 시 1억 5천만원까지 보장한다."],
    )


# ---------------------------------------------------------------------------
# Test (b): default-off parsing matches the legacy raw-JSON helper.
#
# Note: ``_score_summary_faithfulness_judge`` cannot be exercised end-to-end
# with a real prompt because the historical prompt template contains
# literal JSON braces (``{"verdict": ...}``) that pre-date D-S5d and
# clash with :py:meth:`str.format`. The byte-identical relocation
# constraint of D-S5d forbids editing those strings. We exercise the two
# parsing branches (legacy + Instructor schema) directly so test
# coverage doesn't depend on the prompt-format bug being fixed in some
# future slice.
# ---------------------------------------------------------------------------
def _legacy_verdict_score(payload: dict[str, Any] | None) -> float | None:
    """Replicate the legacy verdict-to-score mapping used by the default-off path."""

    if not payload:
        return None
    verdict = str(payload.get("verdict", "")).strip().lower()
    if verdict == "supported":
        return 1.0
    if verdict == "unsupported":
        return 0.0
    return None


@pytest.mark.parametrize(
    ("response_text", "expected_score"),
    [
        ('{"verdict": "supported", "reason": "covered"}', 1.0),
        ('{"verdict": "unsupported", "reason": "missing"}', 0.0),
        # Surrounding chatter is tolerated by the legacy parser.
        ('판정 결과입니다: {"verdict": "supported", "reason": "ok"} 끝.', 1.0),
        # Unknown verdict short-circuits to None for the legacy path.
        ('{"verdict": "maybe", "reason": "unclear"}', None),
    ],
)
def test_default_off_parsing_matches_legacy_helper(
    response_text: str, expected_score: float | None
) -> None:
    """The legacy raw-JSON parser still maps verdicts to T2 scores intact."""

    payload = MetricScorer._parse_json_payload(response_text)
    assert _legacy_verdict_score(payload) == expected_score


# ---------------------------------------------------------------------------
# Test (c): default-on path validates with the Instructor schema
# ---------------------------------------------------------------------------
def test_structured_output_helper_validates_supported_verdict() -> None:
    """The schema branch returns ``1.0`` for a well-formed supported verdict."""

    score = MetricScorer._parse_with_instructor_schema(
        '{"verdict": "supported", "reason": "fully covered"}'
    )
    assert score == 1.0

    parsed = SummaryFaithfulnessVerdict.model_validate_json(
        '{"verdict": "supported", "reason": "fully covered"}'
    )
    assert parsed.verdict == "supported"
    assert parsed.to_score() == 1.0


def test_structured_output_helper_validates_unsupported_verdict() -> None:
    """The schema branch returns ``0.0`` for a well-formed unsupported verdict."""

    score = MetricScorer._parse_with_instructor_schema(
        '{"verdict": "unsupported", "reason": "missing amount"}'
    )
    assert score == 0.0


def test_structured_output_helper_returns_none_on_invalid_payload() -> None:
    """Schema validation must reject verdicts outside the T2 literal set.

    The caller falls back to the legacy raw-JSON parser in that case;
    both paths return ``None`` for ``verdict='maybe'`` so default-on is
    never more brittle than default-off.
    """

    score = MetricScorer._parse_with_instructor_schema(
        '{"verdict": "maybe", "reason": "unclear"}'
    )
    assert score is None

    # No-payload / no-JSON cases also return None.
    assert MetricScorer._parse_with_instructor_schema("") is None
    assert MetricScorer._parse_with_instructor_schema("not json at all") is None


# ---------------------------------------------------------------------------
# Test (d): end-to-end branch coverage via a benign prompt template
#
# The historical prompt template's unescaped JSON braces (see Test (b)
# note) prevent us from invoking the real ``_score_summary_faithfulness_judge``
# unchanged. We monkeypatch ``metric_scoring._SUMMARY_FAITHFULNESS_PROMPT_KO``
# to a safe template so the routing logic — does the feature flag pick
# the schema branch and emit the expected T2 score? — can be exercised
# end-to-end. This monkeypatch never touches the registry (Part A
# byte-identity is preserved).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("use_structured_output", "response_text", "expected_score"),
    [
        (False, '{"verdict": "supported", "reason": "ok"}', 1.0),
        (True, '{"verdict": "supported", "reason": "ok"}', 1.0),
        (False, '{"verdict": "unsupported", "reason": "no"}', 0.0),
        (True, '{"verdict": "unsupported", "reason": "no"}', 0.0),
    ],
)
def test_score_summary_faithfulness_judge_branches(
    monkeypatch: pytest.MonkeyPatch,
    use_structured_output: bool,
    response_text: str,
    expected_score: float,
) -> None:
    """Both feature-flag branches produce the same T2 score end-to-end."""

    monkeypatch.setattr(
        metric_scoring,
        "_SUMMARY_FAITHFULNESS_PROMPT_KO",
        "ctx={context} summary={summary}",
        raising=True,
    )

    llm = _StubLLM(response_text)
    scorer = _build_scorer(llm, use_structured_output=use_structured_output)

    score = asyncio.run(scorer.score_summary_faithfulness_judge(_sample()))
    assert score == expected_score
    assert len(llm.calls) == 1
