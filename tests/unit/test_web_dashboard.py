"""Unit tests for Web UI dashboard components."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest

from evalvault.ports.inbound.web_port import RunSummary

if TYPE_CHECKING:
    pass


class TestPassRateChart:
    """PassRateChart 컴포넌트 테스트."""

    def test_chart_can_be_imported(self):
        """차트 모듈 임포트 확인."""
        from evalvault.adapters.inbound.web.components.charts import create_pass_rate_chart

        assert create_pass_rate_chart is not None
        assert callable(create_pass_rate_chart)

    def test_create_chart_with_data(self):
        """데이터로 차트 생성."""
        from evalvault.adapters.inbound.web.components.charts import create_pass_rate_chart

        runs = [
            RunSummary(
                run_id="run-1",
                dataset_name="dataset-1",
                model_name="gpt-5-nano",
                pass_rate=0.85,
                total_test_cases=100,
                started_at=datetime(2025, 12, 25),
                finished_at=datetime(2025, 12, 25),
                metrics_evaluated=["faithfulness"],
            ),
            RunSummary(
                run_id="run-2",
                dataset_name="dataset-2",
                model_name="gpt-5-nano",
                pass_rate=0.72,
                total_test_cases=50,
                started_at=datetime(2025, 12, 26),
                finished_at=datetime(2025, 12, 26),
                metrics_evaluated=["faithfulness", "answer_relevancy"],
            ),
        ]

        fig = create_pass_rate_chart(runs)

        assert fig is not None
        # Plotly Figure 객체여야 함
        assert hasattr(fig, "data")
        assert hasattr(fig, "layout")

    def test_create_chart_empty_data(self):
        """빈 데이터로 차트 생성."""
        from evalvault.adapters.inbound.web.components.charts import create_pass_rate_chart

        fig = create_pass_rate_chart([])

        assert fig is not None


class TestMetricBreakdownChart:
    """MetricBreakdownChart 컴포넌트 테스트."""

    def test_chart_can_be_imported(self):
        """차트 모듈 임포트 확인."""
        from evalvault.adapters.inbound.web.components.charts import (
            create_metric_breakdown_chart,
        )

        assert create_metric_breakdown_chart is not None
        assert callable(create_metric_breakdown_chart)

    def test_create_breakdown_chart(self):
        """메트릭 분포 차트 생성."""
        from evalvault.adapters.inbound.web.components.charts import (
            create_metric_breakdown_chart,
        )

        metric_scores = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.72,
            "context_precision": 0.90,
        }

        fig = create_metric_breakdown_chart(metric_scores)

        assert fig is not None
        assert hasattr(fig, "data")

    def test_create_breakdown_chart_empty(self):
        """빈 메트릭으로 차트 생성."""
        from evalvault.adapters.inbound.web.components.charts import (
            create_metric_breakdown_chart,
        )

        fig = create_metric_breakdown_chart({})

        assert fig is not None


class TestTrendChart:
    """TrendChart 컴포넌트 테스트."""

    def test_chart_can_be_imported(self):
        """차트 모듈 임포트 확인."""
        from evalvault.adapters.inbound.web.components.charts import create_trend_chart

        assert create_trend_chart is not None
        assert callable(create_trend_chart)

    def test_create_trend_chart(self):
        """트렌드 차트 생성."""
        from evalvault.adapters.inbound.web.components.charts import create_trend_chart

        runs = [
            RunSummary(
                run_id=f"run-{i}",
                dataset_name="dataset",
                model_name="gpt-5-nano",
                pass_rate=0.7 + i * 0.05,
                total_test_cases=100,
                started_at=datetime(2025, 12, 20 + i),
                finished_at=datetime(2025, 12, 20 + i),
                metrics_evaluated=["faithfulness"],
            )
            for i in range(5)
        ]

        fig = create_trend_chart(runs)

        assert fig is not None
        assert hasattr(fig, "data")


class TestMetricSummaryCard:
    """MetricSummaryCard 컴포넌트 테스트."""

    def test_card_can_be_imported(self):
        """카드 모듈 임포트 확인."""
        from evalvault.adapters.inbound.web.components.cards import MetricSummaryCard

        assert MetricSummaryCard is not None

    def test_card_creation(self):
        """카드 생성."""
        from evalvault.adapters.inbound.web.components.cards import MetricSummaryCard

        card = MetricSummaryCard(
            title="Pass Rate",
            value=0.85,
            delta=0.05,
            format_type="percent",
        )

        assert card.title == "Pass Rate"
        assert card.value == 0.85
        assert card.delta == 0.05
        assert card.format_type == "percent"

    def test_card_format_percent(self):
        """퍼센트 포맷."""
        from evalvault.adapters.inbound.web.components.cards import MetricSummaryCard

        card = MetricSummaryCard(
            title="Pass Rate",
            value=0.85,
            format_type="percent",
        )

        assert card.formatted_value == "85.0%"

    def test_card_format_number(self):
        """숫자 포맷."""
        from evalvault.adapters.inbound.web.components.cards import MetricSummaryCard

        card = MetricSummaryCard(
            title="Test Cases",
            value=1234,
            format_type="number",
        )

        assert card.formatted_value == "1,234"

    def test_card_format_currency(self):
        """통화 포맷."""
        from evalvault.adapters.inbound.web.components.cards import MetricSummaryCard

        card = MetricSummaryCard(
            title="Cost",
            value=12.50,
            format_type="currency",
        )

        assert card.formatted_value == "$12.50"

    def test_card_delta_color_positive(self):
        """양수 델타 색상."""
        from evalvault.adapters.inbound.web.components.cards import MetricSummaryCard

        card = MetricSummaryCard(
            title="Pass Rate",
            value=0.85,
            delta=0.05,
        )

        assert card.delta_color == "normal"  # 증가는 좋은 것

    def test_card_delta_color_negative(self):
        """음수 델타 색상."""
        from evalvault.adapters.inbound.web.components.cards import MetricSummaryCard

        card = MetricSummaryCard(
            title="Pass Rate",
            value=0.80,
            delta=-0.05,
        )

        assert card.delta_color == "inverse"  # 감소는 나쁜 것

    def test_card_delta_color_inverse_metric(self):
        """반전 메트릭 (비용 등) 델타 색상."""
        from evalvault.adapters.inbound.web.components.cards import MetricSummaryCard

        card = MetricSummaryCard(
            title="Cost",
            value=10.00,
            delta=-2.00,
            inverse=True,  # 비용은 낮을수록 좋음
        )

        assert card.delta_color == "normal"  # 비용 감소는 좋은 것


class TestRecentRunsList:
    """RecentRunsList 컴포넌트 테스트."""

    def test_list_can_be_imported(self):
        """리스트 모듈 임포트 확인."""
        from evalvault.adapters.inbound.web.components.lists import RecentRunsList

        assert RecentRunsList is not None

    def test_list_creation(self):
        """리스트 생성."""
        from evalvault.adapters.inbound.web.components.lists import RecentRunsList

        runs = [
            RunSummary(
                run_id="run-1",
                dataset_name="dataset-1",
                model_name="gpt-5-nano",
                pass_rate=0.85,
                total_test_cases=100,
                started_at=datetime(2025, 12, 25),
                finished_at=datetime(2025, 12, 25),
                metrics_evaluated=["faithfulness"],
            ),
        ]

        recent_list = RecentRunsList(runs=runs, max_items=5)

        assert recent_list.runs == runs
        assert recent_list.max_items == 5

    def test_list_truncation(self):
        """리스트 자르기."""
        from evalvault.adapters.inbound.web.components.lists import RecentRunsList

        runs = [
            RunSummary(
                run_id=f"run-{i}",
                dataset_name=f"dataset-{i}",
                model_name="gpt-5-nano",
                pass_rate=0.85,
                total_test_cases=100,
                started_at=datetime(2025, 12, 25),
                finished_at=datetime(2025, 12, 25),
                metrics_evaluated=["faithfulness"],
            )
            for i in range(10)
        ]

        recent_list = RecentRunsList(runs=runs, max_items=5)

        assert len(recent_list.displayed_runs) == 5

    def test_list_empty(self):
        """빈 리스트."""
        from evalvault.adapters.inbound.web.components.lists import RecentRunsList

        recent_list = RecentRunsList(runs=[], max_items=5)

        assert recent_list.displayed_runs == []
        assert recent_list.is_empty is True


class TestDashboardStats:
    """DashboardStats 컴포넌트 테스트."""

    def test_stats_can_be_imported(self):
        """통계 모듈 임포트 확인."""
        from evalvault.adapters.inbound.web.components.stats import DashboardStats

        assert DashboardStats is not None

    def test_calculate_stats(self):
        """통계 계산."""
        from evalvault.adapters.inbound.web.components.stats import DashboardStats

        runs = [
            RunSummary(
                run_id="run-1",
                dataset_name="dataset-1",
                model_name="gpt-5-nano",
                pass_rate=0.80,
                total_test_cases=100,
                started_at=datetime(2025, 12, 25),
                finished_at=datetime(2025, 12, 25),
                metrics_evaluated=["faithfulness"],
                total_tokens=1000,
                total_cost_usd=0.10,
            ),
            RunSummary(
                run_id="run-2",
                dataset_name="dataset-2",
                model_name="gpt-5-nano",
                pass_rate=0.90,
                total_test_cases=50,
                started_at=datetime(2025, 12, 26),
                finished_at=datetime(2025, 12, 26),
                metrics_evaluated=["faithfulness", "answer_relevancy"],
                total_tokens=500,
                total_cost_usd=0.05,
            ),
        ]

        stats = DashboardStats.from_runs(runs)

        assert stats.total_runs == 2
        assert stats.total_test_cases == 150
        assert stats.avg_pass_rate == pytest.approx(0.85)
        assert stats.total_tokens == 1500
        assert stats.total_cost == pytest.approx(0.15)

    def test_stats_empty_runs(self):
        """빈 실행 목록 통계."""
        from evalvault.adapters.inbound.web.components.stats import DashboardStats

        stats = DashboardStats.from_runs([])

        assert stats.total_runs == 0
        assert stats.total_test_cases == 0
        assert stats.avg_pass_rate == 0.0

    def test_stats_previous_period_comparison(self):
        """이전 기간 대비."""
        from evalvault.adapters.inbound.web.components.stats import DashboardStats

        current_stats = DashboardStats(
            total_runs=10,
            total_test_cases=1000,
            avg_pass_rate=0.85,
            total_tokens=10000,
            total_cost=1.00,
        )

        previous_stats = DashboardStats(
            total_runs=8,
            total_test_cases=800,
            avg_pass_rate=0.80,
            total_tokens=8000,
            total_cost=0.80,
        )

        delta = current_stats.compare_to(previous_stats)

        assert delta["total_runs"] == 2
        assert delta["avg_pass_rate"] == pytest.approx(0.05)
