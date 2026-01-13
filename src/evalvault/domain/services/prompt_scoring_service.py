from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any

from evalvault.domain.entities import (
    Dataset,
    EvaluationRun,
    PromptCandidate,
    PromptCandidateSampleScore,
    PromptCandidateScore,
    TestCase,
)
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.ports.outbound.llm_port import GenerationOptions, LLMPort

logger = logging.getLogger(__name__)

_PROMPT_LABELS_KO = {
    "system": "시스템",
    "context": "컨텍스트",
    "question": "질문",
    "answer": "답변",
}
_PROMPT_LABELS_EN = {
    "system": "System",
    "context": "Context",
    "question": "Question",
    "answer": "Answer",
}


class PromptScoringService:
    def __init__(self, evaluator: RagasEvaluator, llm: LLMPort) -> None:
        self._evaluator = evaluator
        self._llm = llm

    async def score_candidates(
        self,
        *,
        base_run: EvaluationRun,
        dev_dataset: Dataset,
        holdout_dataset: Dataset,
        candidates: list[PromptCandidate],
        metrics: list[str],
        weights: dict[str, float],
        generation_options: GenerationOptions | None = None,
        selection_policy: str = "best",
        selection_index: int | None = None,
        prompt_language: str | None = None,
    ) -> list[PromptCandidateScore]:
        if not metrics:
            raise ValueError("metrics must not be empty")
        resolved_weights = _resolve_weights(metrics, weights)
        scoring_dataset = _resolve_scoring_dataset(dev_dataset, holdout_dataset)

        sample_count = _resolve_sample_count(generation_options)
        resolved_language = _resolve_prompt_language(scoring_dataset, prompt_language)

        scored: list[PromptCandidateScore] = []
        for candidate in candidates:
            sample_scores: list[PromptCandidateSampleScore] = []
            for sample_index in range(sample_count):
                sample_options = _normalize_generation_options(
                    generation_options,
                    sample_index,
                )
                generated, responses = await self._generate_candidate_dataset(
                    dataset=scoring_dataset,
                    system_prompt=candidate.content,
                    base_run_id=base_run.run_id,
                    generation_options=sample_options,
                    prompt_language=resolved_language,
                )
                run = await self._evaluator.evaluate(
                    dataset=generated,
                    metrics=metrics,
                    llm=self._llm,
                    thresholds=generated.thresholds,
                    parallel=False,
                    batch_size=5,
                )
                scores = _extract_scores(metrics, run)
                weighted_score = _weighted_score(scores, resolved_weights)
                sample_scores.append(
                    PromptCandidateSampleScore(
                        sample_index=sample_index,
                        scores=scores,
                        weighted_score=weighted_score,
                        responses=responses,
                    )
                )

            selected = _select_sample_score(
                sample_scores,
                selection_policy=selection_policy,
                selection_index=selection_index,
            )
            scored.append(
                PromptCandidateScore(
                    candidate_id=candidate.candidate_id,
                    scores=selected.scores,
                    weighted_score=selected.weighted_score,
                    sample_scores=sample_scores,
                    selected_sample_index=selected.sample_index,
                )
            )
        return scored

    async def _generate_candidate_dataset(
        self,
        *,
        dataset: Dataset,
        system_prompt: str,
        base_run_id: str,
        generation_options: GenerationOptions | None,
        prompt_language: str,
    ) -> tuple[Dataset, list[dict[str, Any]]]:
        test_cases: list[TestCase] = []
        responses: list[dict[str, Any]] = []
        for test_case in dataset.test_cases:
            prompt = _build_generation_prompt(
                system_prompt,
                test_case,
                language=prompt_language,
            )
            try:
                answer = await self._llm.agenerate_text(
                    prompt,
                    options=generation_options,
                )
            except Exception as exc:
                logger.warning("Prompt candidate generation failed: %s", exc)
                answer = ""
            test_cases.append(
                replace(
                    test_case,
                    answer=answer,
                    metadata={
                        **(test_case.metadata or {}),
                        "prompt_candidate": True,
                    },
                )
            )
            responses.append(
                {
                    "test_case_id": test_case.id,
                    "question": test_case.question,
                    "answer": answer,
                    "contexts": list(test_case.contexts or []),
                    "ground_truth": test_case.ground_truth,
                }
            )
        metadata = dict(dataset.metadata)
        metadata.setdefault("base_run_id", base_run_id)
        return (
            Dataset(
                name=dataset.name,
                version=dataset.version,
                test_cases=test_cases,
                metadata=metadata,
                source_file=dataset.source_file,
                thresholds=dict(dataset.thresholds),
            ),
            responses,
        )


def _resolve_prompt_language(dataset: Dataset, prompt_language: str | None) -> str:
    normalized = _normalize_language_hint(prompt_language)
    if normalized:
        return normalized
    metadata = dataset.metadata if isinstance(dataset.metadata, dict) else {}
    for key in ("language", "lang", "locale"):
        normalized = _normalize_language_hint(metadata.get(key))
        if normalized:
            return normalized
    languages = metadata.get("languages")
    if isinstance(languages, list | tuple | set):
        for entry in languages:
            normalized = _normalize_language_hint(entry)
            if normalized:
                return normalized
    return "ko"


def _normalize_language_hint(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"ko", "kor", "korean", "ko-kr", "kor-hang", "kr"}:
        return "ko"
    if text in {"en", "eng", "english", "en-us", "en-gb"}:
        return "en"
    return None


def _resolve_sample_count(options: GenerationOptions | None) -> int:
    if options is None or options.n is None:
        return 1
    return max(1, options.n)


def _normalize_generation_options(
    options: GenerationOptions | None,
    sample_index: int,
) -> GenerationOptions | None:
    if options is None:
        return None
    seed = options.seed + sample_index if options.seed is not None else None
    return GenerationOptions(
        temperature=options.temperature,
        top_p=options.top_p,
        max_tokens=options.max_tokens,
        seed=seed,
    )


def _select_sample_score(
    sample_scores: list[PromptCandidateSampleScore],
    *,
    selection_policy: str,
    selection_index: int | None,
) -> PromptCandidateSampleScore:
    if not sample_scores:
        raise ValueError("No sample scores available")
    if selection_policy == "best":
        return max(sample_scores, key=lambda entry: entry.weighted_score)
    if selection_policy == "index":
        if selection_index is None:
            raise ValueError("selection_index is required for index policy")
        if selection_index < 0 or selection_index >= len(sample_scores):
            raise ValueError("selection_index out of range")
        return sample_scores[selection_index]
    raise ValueError("Unsupported selection_policy")


def _resolve_scoring_dataset(dev_dataset: Dataset, holdout_dataset: Dataset) -> Dataset:
    if holdout_dataset.test_cases:
        return holdout_dataset
    if dev_dataset.test_cases:
        return dev_dataset
    raise ValueError("No test cases available for scoring")


def _resolve_weights(metrics: list[str], weights: dict[str, float]) -> dict[str, float]:
    if not weights:
        base = 1.0 / len(metrics)
        return dict.fromkeys(metrics, base)
    resolved = {metric: float(weights.get(metric, 0.0)) for metric in metrics}
    total = sum(resolved.values())
    if total <= 0:
        base = 1.0 / len(metrics)
        return dict.fromkeys(metrics, base)
    return {metric: value / total for metric, value in resolved.items()}


def _extract_scores(metrics: list[str], run: EvaluationRun) -> dict[str, float]:
    scores: dict[str, float] = {}
    for metric in metrics:
        avg = run.get_avg_score(metric)
        scores[metric] = float(avg) if avg is not None else 0.0
    return scores


def _weighted_score(scores: dict[str, float], weights: dict[str, float]) -> float:
    return sum(scores.get(metric, 0.0) * weight for metric, weight in weights.items())


def _build_generation_prompt(
    system_prompt: str,
    test_case: TestCase,
    *,
    language: str,
) -> str:
    context_block = (
        "\n".join(f"- {ctx}" for ctx in test_case.contexts) if test_case.contexts else "-"
    )
    labels = _PROMPT_LABELS_EN if language == "en" else _PROMPT_LABELS_KO
    return (
        f"[{labels['system']}]\n{system_prompt.strip()}\n\n"
        f"[{labels['context']}]\n{context_block}\n\n"
        f"[{labels['question']}]\n{test_case.question.strip()}\n\n"
        f"[{labels['answer']}]\n"
    )
