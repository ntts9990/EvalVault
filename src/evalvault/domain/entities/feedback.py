from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SatisfactionFeedback:
    feedback_id: str
    run_id: str
    test_case_id: str
    satisfaction_score: float | None = None
    thumb_feedback: str | None = None
    comment: str | None = None
    rater_id: str | None = None
    created_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "run_id": self.run_id,
            "test_case_id": self.test_case_id,
            "satisfaction_score": self.satisfaction_score,
            "thumb_feedback": self.thumb_feedback,
            "comment": self.comment,
            "rater_id": self.rater_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class FeedbackSummary:
    avg_satisfaction_score: float | None = None
    thumb_up_rate: float | None = None
    total_feedback: int = 0


@dataclass
class CalibrationCaseResult:
    test_case_id: str
    calibrated_satisfaction: float | None = None
    imputed: bool = False
    imputation_source: str | None = None


@dataclass
class CalibrationSummary:
    avg_satisfaction_score: float | None = None
    thumb_up_rate: float | None = None
    imputed_ratio: float | None = None
    model_metrics: dict[str, dict[str, float | None]] = field(default_factory=dict)


@dataclass
class CalibrationResult:
    summary: CalibrationSummary
    cases: dict[str, CalibrationCaseResult] = field(default_factory=dict)
