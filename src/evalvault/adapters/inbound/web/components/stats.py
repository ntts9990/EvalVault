"""Dashboard statistics components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evalvault.ports.inbound.web_port import RunSummary


@dataclass
class DashboardStats:
    """대시보드 통계.

    전체 평가 실행에 대한 집계 통계를 제공합니다.
    """

    total_runs: int
    total_test_cases: int
    avg_pass_rate: float
    total_tokens: int = 0
    total_cost: float = 0.0

    @classmethod
    def from_runs(cls, runs: list[RunSummary]) -> DashboardStats:
        """실행 목록에서 통계 계산.

        Args:
            runs: 평가 실행 요약 목록

        Returns:
            DashboardStats 인스턴스
        """
        if not runs:
            return cls(
                total_runs=0,
                total_test_cases=0,
                avg_pass_rate=0.0,
                total_tokens=0,
                total_cost=0.0,
            )

        total_runs = len(runs)
        total_test_cases = sum(run.total_test_cases for run in runs)
        avg_pass_rate = sum(run.pass_rate for run in runs) / total_runs
        total_tokens = sum(run.total_tokens for run in runs)
        total_cost = sum(run.total_cost_usd or 0.0 for run in runs)

        return cls(
            total_runs=total_runs,
            total_test_cases=total_test_cases,
            avg_pass_rate=avg_pass_rate,
            total_tokens=total_tokens,
            total_cost=total_cost,
        )

    def compare_to(self, previous: DashboardStats) -> dict[str, float]:
        """이전 통계와 비교.

        Args:
            previous: 이전 기간 통계

        Returns:
            각 지표별 변화량 (delta)
        """
        return {
            "total_runs": self.total_runs - previous.total_runs,
            "total_test_cases": self.total_test_cases - previous.total_test_cases,
            "avg_pass_rate": self.avg_pass_rate - previous.avg_pass_rate,
            "total_tokens": self.total_tokens - previous.total_tokens,
            "total_cost": self.total_cost - previous.total_cost,
        }

    def to_cards(self) -> list[dict]:
        """통계를 카드 데이터로 변환.

        Returns:
            MetricSummaryCard 생성에 필요한 데이터 목록
        """
        return [
            {
                "title": "Total Runs",
                "value": self.total_runs,
                "format_type": "number",
                "icon": "📊",
            },
            {
                "title": "Total Test Cases",
                "value": self.total_test_cases,
                "format_type": "number",
                "icon": "🧪",
            },
            {
                "title": "Avg Pass Rate",
                "value": self.avg_pass_rate,
                "format_type": "percent",
                "icon": "✅",
            },
            {
                "title": "Total Cost",
                "value": self.total_cost,
                "format_type": "currency",
                "icon": "💰",
                "inverse": True,
            },
        ]
