"""Korean-language prompt overrides for Ragas metrics.

This module isolates the Korean-locale instruction strings, few-shot examples,
and prompt-mutation helpers that the `RagasEvaluator` uses when applying
locale-aware defaults to Ragas metrics. Behavior is intentionally identical to
the previous in-class implementation; this is a pure relocation.

The prompt-string and few-shot example *content* now lives in
:mod:`evalvault.domain.services.prompt_catalog` (D-S5d Part A); the
constants below are re-exports that preserve the historical public
surface for external callers and tests.
"""

from __future__ import annotations

from contextlib import suppress
from typing import Any

from evalvault.domain.entities import Dataset
from evalvault.domain.services.prompt_catalog import (
    EXAMPLE_REGISTRY,
    PROMPT_REGISTRY,
)
from evalvault.domain.services.ragas_language import (
    DEFAULT_LANGUAGE_SAMPLE_LIMIT,
    resolve_dataset_language,
)

ANSWER_RELEVANCY_KOREAN_INSTRUCTION = PROMPT_REGISTRY["answer_relevancy_korean_instruction"]
ANSWER_RELEVANCY_KOREAN_EXAMPLES = EXAMPLE_REGISTRY["answer_relevancy_korean_examples"]
FACTUAL_CORRECTNESS_CLAIM_INSTRUCTION = PROMPT_REGISTRY["factual_correctness_claim_instruction_ko"]
FACTUAL_CORRECTNESS_NLI_INSTRUCTION = PROMPT_REGISTRY["factual_correctness_nli_instruction_ko"]
SUMMARY_SCORE_QUESTION_INSTRUCTION = PROMPT_REGISTRY["summary_score_question_instruction_ko"]
SUMMARY_SCORE_ANSWER_INSTRUCTION = PROMPT_REGISTRY["summary_score_answer_instruction_ko"]
SUMMARY_SCORE_KEYPHRASE_INSTRUCTION = PROMPT_REGISTRY["summary_score_keyphrase_instruction_ko"]
SUMMARY_FAITHFULNESS_STATEMENT_INSTRUCTION = PROMPT_REGISTRY[
    "summary_faithfulness_statement_instruction_ko"
]
SUMMARY_FAITHFULNESS_NLI_INSTRUCTION = PROMPT_REGISTRY["summary_faithfulness_nli_instruction_ko"]
FACTUAL_CORRECTNESS_CLAIM_EXAMPLES = EXAMPLE_REGISTRY["factual_correctness_claim_examples_ko"]
FACTUAL_CORRECTNESS_NLI_EXAMPLES = EXAMPLE_REGISTRY["factual_correctness_nli_examples_ko"]


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


def apply_answer_relevancy_prompt_defaults(
    dataset: Dataset,
    ragas_metrics: list[Any],
    prompt_overrides: dict[str, str] | None,
    *,
    prompt_language: str | None = None,
    sample_limit: int = DEFAULT_LANGUAGE_SAMPLE_LIMIT,
) -> None:
    """Apply Korean answer_relevancy defaults unless the dataset is English."""

    if not ragas_metrics:
        return
    if prompt_overrides and "answer_relevancy" in prompt_overrides:
        return
    resolved = resolve_dataset_language(
        dataset, prompt_language=prompt_language, sample_limit=sample_limit
    )
    if resolved == "en":
        return

    for metric in ragas_metrics:
        if getattr(metric, "name", None) != "answer_relevancy":
            continue
        apply_korean_answer_relevancy_prompt(metric)


def apply_summary_prompt_defaults(
    dataset: Dataset,
    ragas_metrics: list[Any],
    prompt_overrides: dict[str, str] | None,
    *,
    prompt_language: str | None = None,
    sample_limit: int = DEFAULT_LANGUAGE_SAMPLE_LIMIT,
) -> None:
    """Apply Korean summary_score/summary_faithfulness defaults unless English."""

    if not ragas_metrics:
        return
    if prompt_overrides and any(
        metric in prompt_overrides for metric in ("summary_score", "summary_faithfulness")
    ):
        return
    resolved = resolve_dataset_language(
        dataset, prompt_language=prompt_language, sample_limit=sample_limit
    )
    if resolved == "en":
        return

    for metric in ragas_metrics:
        metric_name = getattr(metric, "name", None)
        if metric_name == "summary_score":
            apply_korean_summary_score_prompts(metric)
        elif metric_name == "summary_faithfulness":
            apply_korean_summary_faithfulness_prompts(metric)


def apply_factual_correctness_prompt_defaults(
    dataset: Dataset,
    ragas_metrics: list[Any],
    prompt_overrides: dict[str, str] | None,
    *,
    prompt_language: str | None = None,
    sample_limit: int = DEFAULT_LANGUAGE_SAMPLE_LIMIT,
) -> None:
    """Apply Korean factual_correctness defaults unless the dataset is English."""

    if not ragas_metrics:
        return
    if prompt_overrides and "factual_correctness" in prompt_overrides:
        return
    resolved = resolve_dataset_language(
        dataset, prompt_language=prompt_language, sample_limit=sample_limit
    )
    if resolved == "en":
        return

    for metric in ragas_metrics:
        if getattr(metric, "name", None) != "factual_correctness":
            continue
        apply_korean_factual_correctness_prompts(metric)
