"""Dashboard card components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class MetricSummaryCard:
    """메트릭 요약 카드.

    대시보드에서 주요 지표를 표시하는 카드 컴포넌트입니다.
    """

    title: str
    value: float
    delta: float | None = None
    format_type: Literal["percent", "number", "currency"] = "number"
    inverse: bool = False  # True면 값이 낮을수록 좋음 (비용 등)
    icon: str | None = None
    help_text: str | None = None

    @property
    def formatted_value(self) -> str:
        """포맷된 값 반환."""
        if self.format_type == "percent":
            return f"{self.value * 100:.1f}%"
        elif self.format_type == "currency":
            return f"${self.value:.2f}"
        else:
            # 숫자 천단위 구분
            if isinstance(self.value, float) and self.value == int(self.value):
                return f"{int(self.value):,}"
            elif isinstance(self.value, int):
                return f"{self.value:,}"
            else:
                return f"{self.value:,.2f}"

    @property
    def formatted_delta(self) -> str | None:
        """포맷된 델타 값 반환."""
        if self.delta is None:
            return None

        sign = "+" if self.delta > 0 else ""
        if self.format_type == "percent":
            return f"{sign}{self.delta * 100:.1f}%"
        elif self.format_type == "currency":
            return f"{sign}${abs(self.delta):.2f}"
        else:
            return f"{sign}{self.delta:,.0f}"

    @property
    def delta_color(self) -> Literal["normal", "inverse", "off"]:
        """Streamlit metric delta 색상 결정.

        - normal: 증가=녹색, 감소=빨강
        - inverse: 증가=빨강, 감소=녹색
        - off: 색상 없음
        """
        if self.delta is None:
            return "off"

        # inverse가 True면 낮을수록 좋음 (비용 등)
        if self.inverse:
            return "normal" if self.delta < 0 else "inverse"
        else:
            return "normal" if self.delta >= 0 else "inverse"


@dataclass
class StatCard:
    """간단한 통계 카드."""

    label: str
    value: str
    description: str | None = None
    color: str = "#3B82F6"  # 기본 파란색
