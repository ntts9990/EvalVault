from __future__ import annotations

from evalvault.domain.entities import EvaluationRun, SatisfactionFeedback
from evalvault.domain.entities.judge_calibration import JudgeCalibrationResult
from evalvault.domain.services.judge_calibration_service import JudgeCalibrationService
from evalvault.ports.outbound.judge_calibration_port import JudgeCalibrationPort


class JudgeCalibrationAdapter(JudgeCalibrationPort):
    def __init__(self) -> None:
        self._service = JudgeCalibrationService()

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
    ) -> JudgeCalibrationResult:
        return self._service.calibrate(
            run,
            feedbacks,
            labels_source=labels_source,
            method=method,
            metrics=metrics,
            holdout_ratio=holdout_ratio,
            seed=seed,
            parallel=parallel,
            concurrency=concurrency,
        )
