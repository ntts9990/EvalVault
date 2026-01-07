"""Tests for the summary evaluation minimal fixture."""

import json
import re
from pathlib import Path
from typing import Any

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "e2e" / "summary_eval_minimal.json"


def _load_cases() -> list[dict[str, Any]]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return payload["test_cases"]


def _contains_korean(text: str) -> bool:
    return bool(re.search(r"[\uAC00-\uD7A3]", text))


def _contains_english(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text))


def test_summary_fixture_case_shape() -> None:
    cases = _load_cases()
    assert len(cases) == 8

    pass_cases = [case for case in cases if "-pass-" in str(case["id"])]
    fail_cases = [case for case in cases if "-fail-" in str(case["id"])]
    assert len(pass_cases) == 5
    assert len(fail_cases) == 3

    ground_truth_count = 0
    for case in cases:
        assert case["id"]
        assert case["question"]
        assert case["answer"]

        contexts = case["contexts"]
        assert isinstance(contexts, list)
        assert 2 <= len(contexts) <= 3

        if "ground_truth" in case:
            ground_truth_count += 1

    assert ground_truth_count == 1


def test_summary_fixture_language_mix_distribution() -> None:
    cases = _load_cases()
    ko_only = 0
    en_only = 0
    mixed = 0

    for case in cases:
        context_text = " ".join(case["contexts"])
        has_ko = _contains_korean(context_text)
        has_en = _contains_english(context_text)
        assert has_ko or has_en

        if has_ko and has_en:
            mixed += 1
        elif has_ko:
            ko_only += 1
        else:
            en_only += 1

    assert ko_only == 4
    assert en_only == 2
    assert mixed == 2
