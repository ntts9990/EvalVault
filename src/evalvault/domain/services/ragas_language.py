"""Dataset language detection helpers.

Extracted from ``RagasEvaluator`` (D-S5f). Pure functions that infer the
working language ("ko"/"en"/None) of a dataset from explicit metadata hints
or, failing that, by sampling the test-case text. Behaviour is intentionally
identical to the previous in-class implementation.
"""

from __future__ import annotations

from typing import Any

from evalvault.domain.entities import Dataset

DEFAULT_LANGUAGE_SAMPLE_LIMIT = 5


def contains_korean(text: str) -> bool:
    return any("가" <= ch <= "힣" for ch in text)


def contains_latin(text: str) -> bool:
    return any("A" <= ch <= "Z" or "a" <= ch <= "z" for ch in text)


def normalize_language_hint(value: Any) -> str | None:
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


def resolve_dataset_language(
    dataset: Dataset,
    *,
    prompt_language: str | None = None,
    sample_limit: int = DEFAULT_LANGUAGE_SAMPLE_LIMIT,
) -> str | None:
    if prompt_language:
        return prompt_language
    metadata = dataset.metadata if isinstance(dataset.metadata, dict) else {}
    for key in ("language", "lang", "locale"):
        normalized = normalize_language_hint(metadata.get(key))
        if normalized:
            return normalized

    languages = metadata.get("languages")
    if isinstance(languages, list | tuple | set):
        for entry in languages:
            normalized = normalize_language_hint(entry)
            if normalized:
                return normalized

    english_found = False
    for test_case in dataset.test_cases[:sample_limit]:
        if contains_korean(test_case.question) or contains_korean(test_case.answer):
            return "ko"
        if contains_latin(test_case.question) or contains_latin(test_case.answer):
            english_found = True
        for ctx in test_case.contexts:
            if contains_korean(ctx):
                return "ko"
            if contains_latin(ctx):
                english_found = True
    if english_found:
        return "en"
    return None
