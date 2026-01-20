from __future__ import annotations


class SummaryRiskCoverage:
    """Measure coverage of expected insurance risk tags in summary."""

    name = "summary_risk_coverage"

    _TAG_KEYWORDS = {
        "exclusion": ["면책", "보장 제외", "지급 불가", "exclusion"],
        "deductible": ["자기부담", "본인부담금", "deductible", "copay"],
        "limit": ["한도", "상한", "최대", "limit", "cap"],
        "waiting_period": ["면책기간", "대기기간", "waiting period"],
        "condition": ["조건", "단서", "다만", "condition"],
        "documents_required": ["서류", "진단서", "영수증", "documents"],
        "needs_followup": ["확인 필요", "추가 확인", "담당자 확인", "재문의", "follow up"],
    }

    def score(self, answer: str, contexts: list[str], metadata: dict | None = None) -> float:
        expected_tags = self._extract_expected_tags(metadata)
        if not expected_tags:
            return 1.0

        text = answer or ""
        covered = 0
        for tag in expected_tags:
            if self._has_tag_keyword(text, tag):
                covered += 1

        return covered / len(expected_tags)

    def _extract_expected_tags(self, metadata: dict | None) -> list[str]:
        if not metadata:
            return []
        raw = metadata.get("summary_tags")
        if not raw:
            return []
        if isinstance(raw, list):
            return [str(item).strip().lower() for item in raw if str(item).strip()]
        return [str(raw).strip().lower()]

    def _has_tag_keyword(self, text: str, tag: str) -> bool:
        keywords = self._TAG_KEYWORDS.get(tag, [])
        lowered = text.lower()
        return any(keyword in text or keyword.lower() in lowered for keyword in keywords)
