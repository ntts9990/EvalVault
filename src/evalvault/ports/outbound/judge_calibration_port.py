from __future__ import annotations

from typing import Protocol

from evalvault.domain.entities import EvaluationRun, SatisfactionFeedback
from evalvault.domain.entities.judge_calibration import JudgeCalibrationResult


class JudgeCalibrationPort(Protocol):
    def calibrate(
        self,
        run: EvaluationRun,
        feedbacks: list[SatisfactionFeedback],
        *,
        labels_source: str,
        method: str,
        metrics: list[str],
        holdout_ratio: float,
        seed: int,
        parallel: bool = False,
        concurrency: int = 8,
    ) -> JudgeCalibrationResult: ...
