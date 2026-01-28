from __future__ import annotations

from typing import Protocol

from evalvault.domain.entities.multiturn import (
    DriftAnalysis,
    MultiTurnEvaluationResult,
    MultiTurnTestCase,
)


class MultiTurnEvaluatorPort(Protocol):
    def evaluate_conversation(
        self,
        conversation: MultiTurnTestCase,
        metrics: list[str],
    ) -> MultiTurnEvaluationResult: ...

    def detect_drift(
        self,
        conversation: MultiTurnTestCase,
        threshold: float = 0.1,
    ) -> DriftAnalysis: ...
