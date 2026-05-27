"""Korean-language prompt overrides for Ragas metrics.

This module isolates the Korean-locale instruction strings, few-shot examples,
and prompt-mutation helpers that the `RagasEvaluator` uses when applying
locale-aware defaults to Ragas metrics. Behavior is intentionally identical to
the previous in-class implementation; this is a pure relocation.
"""

from __future__ import annotations

from contextlib import suppress
from typing import Any

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


def apply_korean_answer_relevancy_prompt(metric: Any) -> bool:
    prompt = getattr(metric, "question_generation", None)
    if prompt is None:
        return False

    if isinstance(prompt, str):
        metric.question_generation = ANSWER_RELEVANCY_KOREAN_INSTRUCTION
        return True
    if not hasattr(prompt, "instruction"):
        return False
    prompt.instruction = ANSWER_RELEVANCY_KOREAN_INSTRUCTION

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
                for example in ANSWER_RELEVANCY_KOREAN_EXAMPLES
            ]

    if hasattr(prompt, "language"):
        with suppress(Exception):  # pragma: no cover - best effort metadata
            prompt.language = "ko"
    return True


def apply_korean_summary_score_prompts(metric: Any) -> bool:
    question_prompt = getattr(metric, "question_generation_prompt", None)
    answer_prompt = getattr(metric, "answer_generation_prompt", None)
    keyphrase_prompt = getattr(metric, "extract_keyphrases_prompt", None)
    applied = False

    if question_prompt and hasattr(question_prompt, "instruction"):
        question_prompt.instruction = SUMMARY_SCORE_QUESTION_INSTRUCTION
        if hasattr(question_prompt, "language"):
            with suppress(Exception):
                question_prompt.language = "ko"
        applied = True

    if answer_prompt and hasattr(answer_prompt, "instruction"):
        answer_prompt.instruction = SUMMARY_SCORE_ANSWER_INSTRUCTION
        if hasattr(answer_prompt, "language"):
            with suppress(Exception):
                answer_prompt.language = "ko"
        applied = True

    if keyphrase_prompt and hasattr(keyphrase_prompt, "instruction"):
        keyphrase_prompt.instruction = SUMMARY_SCORE_KEYPHRASE_INSTRUCTION
        if hasattr(keyphrase_prompt, "language"):
            with suppress(Exception):
                keyphrase_prompt.language = "ko"
        applied = True

    return applied


def apply_korean_summary_faithfulness_prompts(metric: Any) -> bool:
    statement_prompt = getattr(metric, "statement_generator_prompt", None)
    nli_prompt = getattr(metric, "nli_statements_prompt", None)
    applied = False

    if statement_prompt and hasattr(statement_prompt, "instruction"):
        statement_prompt.instruction = SUMMARY_FAITHFULNESS_STATEMENT_INSTRUCTION
        if hasattr(statement_prompt, "language"):
            with suppress(Exception):
                statement_prompt.language = "ko"
        applied = True

    if nli_prompt and hasattr(nli_prompt, "instruction"):
        nli_prompt.instruction = SUMMARY_FAITHFULNESS_NLI_INSTRUCTION
        if hasattr(nli_prompt, "language"):
            with suppress(Exception):
                nli_prompt.language = "ko"
        applied = True

    return applied


def apply_korean_factual_correctness_prompts(metric: Any) -> bool:
    claim_prompt = getattr(metric, "claim_decomposition_prompt", None)
    nli_prompt = getattr(metric, "nli_prompt", None)
    applied = False

    if claim_prompt and hasattr(claim_prompt, "instruction"):
        claim_prompt.instruction = FACTUAL_CORRECTNESS_CLAIM_INSTRUCTION
        input_model = getattr(claim_prompt, "input_model", None)
        output_model = getattr(claim_prompt, "output_model", None)
        if input_model and output_model:
            with suppress(Exception):  # pragma: no cover - best effort prompt tuning
                claim_prompt.examples = [
                    (
                        input_model(response=example["response"]),
                        output_model(claims=example["claims"]),
                    )
                    for example in FACTUAL_CORRECTNESS_CLAIM_EXAMPLES
                ]
        if hasattr(claim_prompt, "language"):
            with suppress(Exception):  # pragma: no cover - best effort metadata
                claim_prompt.language = "ko"
        applied = True

    if nli_prompt and hasattr(nli_prompt, "instruction"):
        nli_prompt.instruction = FACTUAL_CORRECTNESS_NLI_INSTRUCTION
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
                    for example in FACTUAL_CORRECTNESS_NLI_EXAMPLES
                ]
        if hasattr(nli_prompt, "language"):
            with suppress(Exception):  # pragma: no cover - best effort metadata
                nli_prompt.language = "ko"
        applied = True

    return applied
