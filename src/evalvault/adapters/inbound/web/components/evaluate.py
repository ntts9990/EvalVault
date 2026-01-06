"""Evaluation configuration and runner components."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evalvault.ports.inbound.web_port import EvalRequest


@dataclass
class EvaluationConfig:
    """평가 실행 설정.

    웹 UI에서 수집한 평가 설정을 저장합니다.
    """

    dataset_path: str
    metrics: list[str]
    model_name: str = "gpt-5-nano"
    langfuse_enabled: bool = False
    parallel: bool = True
    thresholds: dict[str, float] = field(default_factory=dict)
    project_name: str | None = None

    def is_valid(self) -> bool:
        """설정 유효성 검증.

        Returns:
            유효하면 True, 아니면 False
        """
        if not self.dataset_path:
            return False
        if not self.metrics:
            return False
        return bool(self.model_name)

    def to_eval_request(self) -> EvalRequest:
        """EvalRequest 객체로 변환.

        Returns:
            EvalRequest 인스턴스
        """
        from evalvault.ports.inbound.web_port import EvalRequest

        return EvalRequest(
            dataset_path=self.dataset_path,
            metrics=self.metrics,
            model_name=self.model_name,
            langfuse_enabled=self.langfuse_enabled,
            thresholds=self.thresholds,
            project_name=self.project_name,
        )

    def get_validation_errors(self) -> list[str]:
        """검증 오류 목록 반환.

        Returns:
            오류 메시지 목록
        """
        errors = []
        if not self.dataset_path:
            errors.append("Dataset path is required")
        if not self.metrics:
            errors.append("At least one metric must be selected")
        if not self.model_name:
            errors.append("Model name is required")
        return errors


@dataclass
class EvaluationResult:
    """평가 실행 결과 요약."""

    run_id: str
    success: bool
    pass_rate: float = 0.0
    total_test_cases: int = 0
    metrics_evaluated: list[str] = field(default_factory=list)
    error_message: str | None = None
    duration_seconds: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float | None = None

    @property
    def formatted_pass_rate(self) -> str:
        """포맷된 통과율."""
        return f"{self.pass_rate * 100:.1f}%"

    @property
    def formatted_duration(self) -> str:
        """포맷된 소요 시간."""
        if self.duration_seconds < 60:
            return f"{self.duration_seconds:.1f}s"
        minutes = int(self.duration_seconds // 60)
        seconds = self.duration_seconds % 60
        return f"{minutes}m {seconds:.1f}s"
