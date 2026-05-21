"""Centralized catalog of LLM-facing prompt strings used by the evaluator.

EvalVault treats every LLM-facing prompt as a carefully tuned artifact
(memory ``feedback_llm_prompt_discipline.md``). Historically those prompt
strings were scattered across :mod:`ragas_korean_prompts` (locale-aware
Ragas overrides) and :mod:`metric_scoring` (summary-faithfulness judge
templates). This module is the single place that holds them as
byte-identical constants so:

* code review can audit every prompt the system can emit in one file;
* downstream call sites read prompts from a stable lookup table
  (``PROMPT_REGISTRY[...]``) instead of importing scattered constants;
* the few-shot example collections live alongside the instructions they
  augment (``EXAMPLE_REGISTRY``);
* structured-output schemas (``SummaryFaithfulnessVerdict``) live next
  to the prompt they describe, supporting the opt-in Instructor wrapper
  for the summary-faithfulness judge call site.

This module is a centralization, not a redesign — every string is
byte-identical to its previous home. The original modules
(``ragas_korean_prompts``, ``metric_scoring``) keep their original
constant names as re-exports so existing imports continue to work.

The module name is ``prompt_catalog`` (not ``prompt_registry``) because
``prompt_registry`` is already taken by an unrelated tracker-side
snapshot/checksum utility for ``PromptSetBundle`` storage.

T2 discipline (memory ``project_decision_authority_t2.md``): the
structured-output schema below carries T2 evaluation semantics
(``supported``/``unsupported``) only. No promote/rollback verdicts are
introduced.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

try:  # pragma: no cover - import guard
    from instructor import OpenAISchema as _StructuredOutputBase
except Exception:  # pragma: no cover - fallback if instructor is unavailable
    from pydantic import BaseModel as _StructuredOutputBase  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Korean Ragas prompt overrides (relocated from ``ragas_korean_prompts``)
# ---------------------------------------------------------------------------
_ANSWER_RELEVANCY_KOREAN_INSTRUCTION = (
    "다음 답변에 대해 질문을 생성하고, 답변이 회피적, "
    "모호, 불확실하면 noncommittal=1, 명확하면 0으로 표시하세요. "
    "질문은 답변과 동일한 언어(한국어)로 작성하세요."
)
_FACTUAL_CORRECTNESS_CLAIM_INSTRUCTION = (
    "다음 문장을 독립적인 사실 주장으로 분해하세요. "
    "각 주장은 다른 주장과 독립적으로 "
    "참/거짓 판단이 가능해야 합니다. "
    "예시의 원자성 수준을 따르세요."
)
_FACTUAL_CORRECTNESS_NLI_INSTRUCTION = (
    "주어진 컨텍스트를 보고 각 진술이 직접적으로 도출 가능한지 판단하세요. "
    "가능하면 verdict=1, 불가능하면 verdict=0을 JSON으로 반환하세요."
)
_SUMMARY_SCORE_QUESTION_INSTRUCTION = (
    "다음 텍스트와 핵심 키워드를 기반으로, "
    "텍스트에 근거해 반드시 1로 답할 수 있는 폐쇄형 질문을 생성하세요. "
    "질문은 한국어로 작성하세요."
)
_SUMMARY_SCORE_ANSWER_INSTRUCTION = (
    "다음 질문 목록에 대해, 제공된 요약이 각 질문에 답할 수 있으면 '1', "
    "그렇지 않으면 '0'을 JSON 배열로 반환하세요."
)
_SUMMARY_SCORE_KEYPHRASE_INSTRUCTION = (
    "다음 텍스트에서 인물, 기관, 위치, 날짜/시간, 금액, 비율과 같은 핵심 키워드를 추출하세요."
)
_SUMMARY_FAITHFULNESS_STATEMENT_INSTRUCTION = (
    "질문과 답변을 보고 각 문장을 이해 가능한 주장으로 분해하세요. "
    "각 주장은 대명사 없이 독립적으로 이해 가능해야 합니다."
)
_SUMMARY_FAITHFULNESS_NLI_INSTRUCTION = (
    "주어진 컨텍스트를 보고 각 진술이 직접적으로 도출 가능한지 판단하세요. "
    "가능하면 verdict=1, 불가능하면 verdict=0을 JSON으로 반환하세요."
)


# ---------------------------------------------------------------------------
# Summary-faithfulness judge templates (relocated from ``metric_scoring``)
# ---------------------------------------------------------------------------
_SUMMARY_FAITHFULNESS_JUDGE_PROMPT_KO = (
    "당신은 요약 충실도 판정자입니다.\n"
    "컨텍스트와 요약을 보고 요약의 모든 주장이 컨텍스트에 의해 뒷받침되는지 판단하세요.\n"
    "숫자, 조건, 면책, 기간, 자격 등이 누락되거나 추가되거나 모순되면 verdict는 unsupported입니다.\n"
    'JSON만 반환: {"verdict": "supported|unsupported", "reason": "..."}\n\n'
    "컨텍스트:\n{context}\n\n요약:\n{summary}\n"
)
_SUMMARY_FAITHFULNESS_JUDGE_PROMPT_EN = (
    "You are a strict summarization faithfulness judge.\n"
    "Given the CONTEXT and SUMMARY, determine whether every claim in SUMMARY is supported by CONTEXT.\n"
    "If any numbers, conditions, exclusions, durations, or eligibility are missing, added, or "
    "contradicted, verdict is unsupported.\n"
    'Return JSON only: {"verdict": "supported|unsupported", "reason": "..."}\n\n'
    "CONTEXT:\n{context}\n\nSUMMARY:\n{summary}\n"
)


# ---------------------------------------------------------------------------
# Few-shot example collections (relocated from ``ragas_korean_prompts``)
# ---------------------------------------------------------------------------
_ANSWER_RELEVANCY_KOREAN_EXAMPLES: list[dict[str, Any]] = [
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
_FACTUAL_CORRECTNESS_CLAIM_EXAMPLES: list[dict[str, Any]] = [
    {
        "response": "대인배상 I은 사망 시 1억 5천만원까지 보장합니다.",
        "claims": ["대인배상 I은 사망 시 1억 5천만원까지 보장한다."],
    },
    {
        "response": "마일리지 특약은 3천km 이하 주행 시 47% 할인됩니다.",
        "claims": ["마일리지 특약은 3천km 이하 주행 시 47% 할인된다."],
    },
]
_FACTUAL_CORRECTNESS_NLI_EXAMPLES: list[dict[str, Any]] = [
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


# ---------------------------------------------------------------------------
# Public lookup tables
# ---------------------------------------------------------------------------
#: Named registry of every LLM prompt string the evaluator can emit.
#: Keys are stable identifiers; values are byte-identical to the legacy
#: location they replaced. Call sites should prefer reading via these
#: keys (or the named re-exports below).
PROMPT_REGISTRY: dict[str, str] = {
    "answer_relevancy_korean_instruction": _ANSWER_RELEVANCY_KOREAN_INSTRUCTION,
    "factual_correctness_claim_instruction_ko": _FACTUAL_CORRECTNESS_CLAIM_INSTRUCTION,
    "factual_correctness_nli_instruction_ko": _FACTUAL_CORRECTNESS_NLI_INSTRUCTION,
    "summary_score_question_instruction_ko": _SUMMARY_SCORE_QUESTION_INSTRUCTION,
    "summary_score_answer_instruction_ko": _SUMMARY_SCORE_ANSWER_INSTRUCTION,
    "summary_score_keyphrase_instruction_ko": _SUMMARY_SCORE_KEYPHRASE_INSTRUCTION,
    "summary_faithfulness_statement_instruction_ko": _SUMMARY_FAITHFULNESS_STATEMENT_INSTRUCTION,
    "summary_faithfulness_nli_instruction_ko": _SUMMARY_FAITHFULNESS_NLI_INSTRUCTION,
    "summary_faithfulness_judge_prompt_ko": _SUMMARY_FAITHFULNESS_JUDGE_PROMPT_KO,
    "summary_faithfulness_judge_prompt_en": _SUMMARY_FAITHFULNESS_JUDGE_PROMPT_EN,
}

#: Named registry of few-shot example collections used to prime Ragas
#: prompts (kept separate from the string registry because the values
#: are lists of dicts, not strings).
EXAMPLE_REGISTRY: dict[str, list[dict[str, Any]]] = {
    "answer_relevancy_korean_examples": _ANSWER_RELEVANCY_KOREAN_EXAMPLES,
    "factual_correctness_claim_examples_ko": _FACTUAL_CORRECTNESS_CLAIM_EXAMPLES,
    "factual_correctness_nli_examples_ko": _FACTUAL_CORRECTNESS_NLI_EXAMPLES,
}


# ---------------------------------------------------------------------------
# Structured-output schemas (Part B — opt-in Instructor wrapper)
# ---------------------------------------------------------------------------
class SummaryFaithfulnessVerdict(_StructuredOutputBase):
    """Structured-output schema for the summary-faithfulness judge call.

    Mirrors the JSON contract embedded in
    ``summary_faithfulness_judge_prompt_{ko,en}``::

        {"verdict": "supported|unsupported", "reason": "..."}

    The schema inherits from :class:`instructor.OpenAISchema` so the
    Instructor library can use it as an OpenAI function/tool schema when
    the opt-in structured-output feature flag is enabled. When
    ``instructor`` is unavailable (e.g. in an offline minimal install),
    the schema falls back to :class:`pydantic.BaseModel` so the catalog
    module still imports cleanly.

    T2 discipline: ``verdict`` only carries evaluation semantics
    (supported vs. unsupported). No promote/rollback states.
    """

    verdict: Literal["supported", "unsupported"] = Field(
        description="Whether every claim in the summary is supported by the context.",
    )
    reason: str = Field(
        default="",
        description="Short natural-language justification produced by the judge.",
    )

    def to_score(self) -> float:
        """Return the numeric score the legacy parser would produce."""
        return 1.0 if self.verdict == "supported" else 0.0


__all__ = [
    "PROMPT_REGISTRY",
    "EXAMPLE_REGISTRY",
    "SummaryFaithfulnessVerdict",
]
