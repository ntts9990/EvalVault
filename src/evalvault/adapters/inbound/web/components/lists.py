"""Dashboard list components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evalvault.ports.inbound.web_port import RunSummary


@dataclass
class RecentRunsList:
    """최근 평가 실행 목록.

    대시보드에서 최근 평가 결과를 표시하는 리스트 컴포넌트입니다.
    """

    runs: list[RunSummary]
    max_items: int = 5

    @property
    def displayed_runs(self) -> list[RunSummary]:
        """표시할 실행 목록 (최대 max_items개)."""
        return self.runs[: self.max_items]

    @property
    def is_empty(self) -> bool:
        """목록이 비어있는지 확인."""
        return len(self.runs) == 0

    @property
    def has_more(self) -> bool:
        """더 많은 항목이 있는지 확인."""
        return len(self.runs) > self.max_items

    @property
    def remaining_count(self) -> int:
        """표시되지 않은 항목 수."""
        return max(0, len(self.runs) - self.max_items)

    def get_pass_rate_status(self, pass_rate: float) -> str:
        """통과율에 따른 상태 반환.

        Args:
            pass_rate: 통과율 (0.0 ~ 1.0)

        Returns:
            상태 문자열 (excellent, good, warning, critical)
        """
        if pass_rate >= 0.9:
            return "excellent"
        elif pass_rate >= 0.7:
            return "good"
        elif pass_rate >= 0.5:
            return "warning"
        else:
            return "critical"

    def get_pass_rate_emoji(self, pass_rate: float) -> str:
        """통과율에 따른 이모지 반환.

        Args:
            pass_rate: 통과율 (0.0 ~ 1.0)

        Returns:
            상태 이모지
        """
        status = self.get_pass_rate_status(pass_rate)
        emoji_map = {
            "excellent": "🟢",
            "good": "🟡",
            "warning": "🟠",
            "critical": "🔴",
        }
        return emoji_map.get(status, "⚪")
