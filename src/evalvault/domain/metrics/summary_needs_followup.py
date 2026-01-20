from __future__ import annotations


class SummaryNeedsFollowup:
    """Check if follow-up guidance appears when required."""

    name = "summary_needs_followup"

    _FOLLOWUP_KEYWORDS = [
        "확인 필요",
        "추가 확인",
        "담당자 확인",
        "재문의",
        "추가 문의",
        "서류 확인",
        "follow up",
        "follow-up",
    ]

    def score(self, answer: str, contexts: list[str], metadata: dict | None = None) -> float:
        text = answer or ""
        has_followup = self._has_followup(text)
        expected = self._expects_followup(metadata)

        if expected:
            return 1.0 if has_followup else 0.0
        return 1.0 if not has_followup else 0.0

    def _expects_followup(self, metadata: dict | None) -> bool:
        if not metadata:
            return False
        raw = metadata.get("summary_tags")
        if not raw:
            return False
        if isinstance(raw, list):
            tags = [str(item).strip().lower() for item in raw if str(item).strip()]
        else:
            tags = [str(raw).strip().lower()]
        return "needs_followup" in tags

    def _has_followup(self, text: str) -> bool:
        lowered = text.lower()
        return any(
            keyword in text or keyword.lower() in lowered for keyword in self._FOLLOWUP_KEYWORDS
        )
