"""Evaluation progress components."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EvaluationProgress:
    """평가 진행률 상태.

    평가 실행 중 진행 상태를 추적합니다.
    """

    total_steps: int
    current_step: int
    current_metric: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    metrics_completed: list[str] = field(default_factory=list)

    @property
    def percent(self) -> float:
        """진행률 퍼센트 (0-100)."""
        if self.total_steps == 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100.0

    @property
    def is_complete(self) -> bool:
        """완료 여부."""
        return self.current_step >= self.total_steps

    @property
    def has_error(self) -> bool:
        """에러 발생 여부."""
        return self.error is not None

    def update(self, step: int, metric: str | None = None) -> None:
        """진행 상태 업데이트.

        Args:
            step: 현재 단계
            metric: 현재 처리 중인 메트릭
        """
        # 이전 메트릭 완료 처리
        if (
            self.current_metric
            and metric != self.current_metric
            and self.current_metric not in self.metrics_completed
        ):
            self.metrics_completed.append(self.current_metric)

        self.current_step = step
        self.current_metric = metric

    def get_status_message(self) -> str:
        """현재 상태 메시지.

        Returns:
            상태 설명 문자열
        """
        if self.has_error:
            return f"Error: {self.error}"

        if self.is_complete:
            return "Evaluation complete!"

        if self.current_metric:
            return f"Evaluating {self.current_metric}... ({self.current_step}/{self.total_steps})"

        return f"Processing... ({self.current_step}/{self.total_steps})"

    def get_elapsed_time(self) -> float | None:
        """경과 시간 (초).

        Returns:
            경과 시간 또는 None
        """
        if self.started_at is None:
            return None
        return (datetime.now() - self.started_at).total_seconds()

    def get_estimated_remaining(self) -> float | None:
        """예상 남은 시간 (초).

        Returns:
            예상 남은 시간 또는 None
        """
        elapsed = self.get_elapsed_time()
        if elapsed is None or self.current_step == 0:
            return None

        time_per_step = elapsed / self.current_step
        remaining_steps = self.total_steps - self.current_step
        return time_per_step * remaining_steps


@dataclass
class ProgressStep:
    """진행 단계 정보."""

    name: str
    status: str = "pending"  # pending, running, completed, failed
    duration: float | None = None
    message: str | None = None

    @property
    def is_done(self) -> bool:
        """완료 여부."""
        return self.status in ("completed", "failed")

    @property
    def icon(self) -> str:
        """상태 아이콘."""
        icons = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
        }
        return icons.get(self.status, "⚪")
