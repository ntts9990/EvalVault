from __future__ import annotations

import re


class SummaryNonDefinitive:
    """Penalize definitive statements in summaries."""

    name = "summary_non_definitive"

    _DEFINITIVE_PATTERNS_KO = [
        r"무조건",
        r"반드시",
        r"100%",
        r"전액\s*지급",
        r"확실히",
        r"분명히",
        r"절대",
        r"항상",
    ]
    _DEFINITIVE_PATTERNS_EN = [
        r"always",
        r"guaranteed",
        r"definitely",
        r"certainly",
        r"absolutely",
        r"100%",
    ]

    def score(self, answer: str, contexts: list[str]) -> float:
        text = answer or ""
        if self._has_definitive_pattern(text):
            return 0.0
        return 1.0

    def _has_definitive_pattern(self, text: str) -> bool:
        for pattern in self._DEFINITIVE_PATTERNS_KO:
            if re.search(pattern, text):
                return True
        lowered = text.lower()
        return any(re.search(pattern, lowered) for pattern in self._DEFINITIVE_PATTERNS_EN)
