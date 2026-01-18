"""Dataset preprocessing guardrails for RAG evaluation."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from evalvault.domain.entities import Dataset

REFERENCE_REQUIRED_METRICS = {
    "context_precision",
    "context_recall",
    "factual_correctness",
    "semantic_similarity",
}

_WHITESPACE_RE = re.compile(r"\s+")
_PUNCT_ONLY_RE = re.compile(r"^[\W_]+$")
_HANGUL_RE = re.compile(r"[\uac00-\ud7a3]")
_LATIN_RE = re.compile(r"[A-Za-z]")

_PLACEHOLDER_TEXT = {
    "n/a",
    "na",
    "none",
    "null",
    "nil",
    "unknown",
    "tbd",
    "todo",
    "undefined",
}


@dataclass(frozen=True)
class DatasetPreprocessConfig:
    """Configuration for dataset preprocessing guardrails."""

    enabled: bool = True
    min_reference_chars: int = 6
    min_reference_words: int = 1
    max_reference_chars: int = 2000
    max_contexts: int = 20
    max_context_chars: int = 2000
    trim_whitespace: bool = True
    dedupe_contexts: bool = True
    drop_empty_questions: bool = True
    drop_empty_answers: bool = False
    drop_empty_contexts: bool = False
    fill_reference_from_answer: bool = True
    fill_reference_from_context: bool = True
    prefer_answer_reference: bool = True


@dataclass
class DatasetPreprocessReport:
    """Summary of dataset preprocessing actions."""

    schema_version: int = 1
    total_cases: int = 0
    kept_cases: int = 0
    dropped_cases: int = 0
    empty_questions: int = 0
    empty_answers: int = 0
    empty_contexts: int = 0
    contexts_removed: int = 0
    contexts_deduped: int = 0
    contexts_truncated: int = 0
    contexts_limited: int = 0
    references_missing: int = 0
    references_short: int = 0
    references_filled_from_answer: int = 0
    references_filled_from_context: int = 0
    references_truncated: int = 0

    def has_findings(self) -> bool:
        return any(
            value > 0
            for key, value in self.to_dict().items()
            if key not in {"schema_version", "total_cases", "kept_cases"}
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "schema_version": self.schema_version,
            "total_cases": self.total_cases,
            "kept_cases": self.kept_cases,
            "dropped_cases": self.dropped_cases,
            "empty_questions": self.empty_questions,
            "empty_answers": self.empty_answers,
            "empty_contexts": self.empty_contexts,
            "contexts_removed": self.contexts_removed,
            "contexts_deduped": self.contexts_deduped,
            "contexts_truncated": self.contexts_truncated,
            "contexts_limited": self.contexts_limited,
            "references_missing": self.references_missing,
            "references_short": self.references_short,
            "references_filled_from_answer": self.references_filled_from_answer,
            "references_filled_from_context": self.references_filled_from_context,
            "references_truncated": self.references_truncated,
        }


def merge_preprocess_summaries(
    base: dict[str, Any] | None,
    incoming: dict[str, Any] | None,
) -> dict[str, int] | None:
    """Merge two preprocessing summary dicts by summing numeric fields."""

    if not base and not incoming:
        return None
    if not base:
        return _coerce_summary_dict(incoming)
    if not incoming:
        return _coerce_summary_dict(base)

    merged: dict[str, int] = {"schema_version": 1}
    for key in DatasetPreprocessReport().to_dict():
        if key == "schema_version":
            continue
        merged[key] = int(base.get(key, 0) or 0) + int(incoming.get(key, 0) or 0)
    return merged


def _coerce_summary_dict(summary: dict[str, Any] | None) -> dict[str, int] | None:
    if not summary:
        return None
    coerced: dict[str, int] = {"schema_version": int(summary.get("schema_version", 1) or 1)}
    for key in DatasetPreprocessReport().to_dict():
        if key == "schema_version":
            continue
        coerced[key] = int(summary.get(key, 0) or 0)
    return coerced


class DatasetPreprocessor:
    """Apply dataset guardrails to reduce evaluation instability."""

    def __init__(self, config: DatasetPreprocessConfig | None = None) -> None:
        self._config = config or DatasetPreprocessConfig()

    def apply(
        self, dataset: Dataset, *, metrics: Sequence[str] | None = None
    ) -> DatasetPreprocessReport:
        report = DatasetPreprocessReport(total_cases=len(dataset.test_cases))
        if not self._config.enabled:
            report.kept_cases = len(dataset.test_cases)
            return report

        reference_needed = self._needs_reference(metrics)
        processed_cases = []

        for test_case in dataset.test_cases:
            question = self._normalize_text(test_case.question)
            answer = self._normalize_text(test_case.answer)
            contexts, ctx_stats = self._normalize_contexts(test_case.contexts)
            ground_truth = self._normalize_text(test_case.ground_truth)

            if not question:
                report.empty_questions += 1
            if not answer:
                report.empty_answers += 1
            if not contexts:
                report.empty_contexts += 1

            report.contexts_removed += ctx_stats["removed"]
            report.contexts_deduped += ctx_stats["deduped"]
            report.contexts_truncated += ctx_stats["truncated"]
            report.contexts_limited += ctx_stats["limited"]

            if not question and self._config.drop_empty_questions:
                report.dropped_cases += 1
                continue
            if not answer and self._config.drop_empty_answers:
                report.dropped_cases += 1
                continue
            if not contexts and self._config.drop_empty_contexts:
                report.dropped_cases += 1
                continue

            if reference_needed:
                ground_truth, ref_stats = self._normalize_reference(
                    ground_truth=ground_truth,
                    question=question,
                    answer=answer,
                    contexts=contexts,
                )
                report.references_missing += ref_stats["missing"]
                report.references_short += ref_stats["short"]
                report.references_filled_from_answer += ref_stats["filled_from_answer"]
                report.references_filled_from_context += ref_stats["filled_from_context"]
                report.references_truncated += ref_stats["truncated"]

            test_case.question = question
            test_case.answer = answer
            test_case.contexts = contexts
            test_case.ground_truth = ground_truth or None
            processed_cases.append(test_case)

        dataset.test_cases = processed_cases
        report.kept_cases = len(processed_cases)
        return report

    def _needs_reference(self, metrics: Sequence[str] | None) -> bool:
        if not metrics:
            return True
        return any(metric in REFERENCE_REQUIRED_METRICS for metric in metrics)

    def _normalize_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            text = " ".join(str(item) for item in value if item is not None)
        else:
            text = str(value)
        if self._config.trim_whitespace:
            text = text.replace("\u00a0", " ")
            text = _WHITESPACE_RE.sub(" ", text).strip()
        if self._is_noise_text(text):
            return ""
        return text

    def _is_noise_text(self, text: str) -> bool:
        if not text:
            return True
        if _PUNCT_ONLY_RE.fullmatch(text):
            return True
        lower_text = text.casefold()
        return lower_text in _PLACEHOLDER_TEXT

    def _normalize_contexts(self, contexts: Any) -> tuple[list[str], dict[str, int]]:
        removed = 0
        deduped = 0
        truncated = 0

        if contexts is None:
            raw_contexts = []
        elif isinstance(contexts, list):
            raw_contexts = contexts
        else:
            raw_contexts = [contexts]

        normalized: list[str] = []
        seen: set[str] = set()
        for item in raw_contexts:
            text = self._normalize_text(item)
            if not text:
                removed += 1
                continue
            key = text.casefold() if self._config.dedupe_contexts else ""
            if key and key in seen:
                deduped += 1
                continue
            if self._config.max_context_chars > 0:
                text, did_truncate = self._truncate_text(text, self._config.max_context_chars)
                if did_truncate:
                    truncated += 1
            normalized.append(text)
            if key:
                seen.add(key)

        limited = 0
        if self._config.max_contexts > 0 and len(normalized) > self._config.max_contexts:
            limited = len(normalized) - self._config.max_contexts
            normalized = normalized[: self._config.max_contexts]

        return normalized, {
            "removed": removed,
            "deduped": deduped,
            "truncated": truncated,
            "limited": limited,
        }

    def _normalize_reference(
        self,
        *,
        ground_truth: str,
        question: str,
        answer: str,
        contexts: list[str],
    ) -> tuple[str, dict[str, int]]:
        missing = 0
        short = 0
        filled_from_answer = 0
        filled_from_context = 0
        truncated = 0

        reference = ground_truth
        if not reference:
            missing = 1
        elif self._is_reference_short(reference):
            short = 1

        if (missing or short) and (
            self._config.fill_reference_from_answer or self._config.fill_reference_from_context
        ):
            target_language = self._resolve_target_language(
                reference=reference,
                question=question,
                answer=answer,
                contexts=contexts,
            )
            candidate, source = self._select_reference_candidate(
                reference=reference,
                target_language=target_language,
                answer=answer,
                contexts=contexts,
            )
            if candidate and candidate != reference:
                reference = candidate
                if source == "answer":
                    filled_from_answer = 1
                elif source == "context":
                    filled_from_context = 1

        if reference:
            reference = self._normalize_text(reference)

        if reference and self._config.max_reference_chars > 0:
            reference, did_truncate = self._truncate_text(
                reference, self._config.max_reference_chars
            )
            if did_truncate:
                truncated = 1

        return reference, {
            "missing": missing,
            "short": short,
            "filled_from_answer": filled_from_answer,
            "filled_from_context": filled_from_context,
            "truncated": truncated,
        }

    def _select_reference_candidate(
        self,
        *,
        reference: str,
        target_language: str,
        answer: str,
        contexts: list[str],
    ) -> tuple[str | None, str | None]:
        answer_candidate = None
        answer_fallback = None
        if (
            self._config.fill_reference_from_answer
            and answer
            and not self._is_reference_short(answer)
        ):
            if self._matches_language(target_language, answer):
                answer_candidate = answer
            else:
                answer_fallback = answer

        context_candidate = None
        context_fallback = None
        if self._config.fill_reference_from_context and contexts:
            if reference:
                for ctx in contexts:
                    if reference in ctx:
                        context_candidate = ctx
                        break
            if not context_candidate:
                for ctx in contexts:
                    if not self._is_reference_short(ctx):
                        if self._matches_language(target_language, ctx):
                            context_candidate = ctx
                            break
                        if context_fallback is None:
                            context_fallback = ctx
                        break

        if self._config.prefer_answer_reference:
            if answer_candidate:
                return answer_candidate, "answer"
            if context_candidate:
                return context_candidate, "context"
        else:
            if context_candidate:
                return context_candidate, "context"
            if answer_candidate:
                return answer_candidate, "answer"

        if self._config.prefer_answer_reference:
            if answer_fallback:
                return answer_fallback, "answer"
            if context_fallback:
                return context_fallback, "context"
        else:
            if context_fallback:
                return context_fallback, "context"
            if answer_fallback:
                return answer_fallback, "answer"

        return None, None

    def _is_reference_short(self, text: str) -> bool:
        if len(text) < self._config.min_reference_chars:
            return True
        return self._config.min_reference_words > 1 and (
            len(text.split()) < self._config.min_reference_words
        )

    @staticmethod
    def _truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
        if max_chars <= 0 or len(text) <= max_chars:
            return text, False
        return text[:max_chars].rstrip(), True

    def _resolve_target_language(
        self,
        *,
        reference: str,
        question: str,
        answer: str,
        contexts: list[str],
    ) -> str:
        for candidate in (reference, question, answer):
            lang = self._detect_language(candidate)
            if lang != "other":
                return lang
        for ctx in contexts:
            lang = self._detect_language(ctx)
            if lang != "other":
                return lang
        return "other"

    def _detect_language(self, text: str) -> str:
        if not text:
            return "other"
        if _HANGUL_RE.search(text):
            return "ko"
        if _LATIN_RE.search(text):
            return "en"
        return "other"

    def _matches_language(self, target_language: str, text: str) -> bool:
        if target_language in {"ko", "en"}:
            return self._detect_language(text) == target_language
        return True
