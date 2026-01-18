from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class JudgeCalibrationCase:
    test_case_id: str
    raw_score: float
    calibrated_score: float
    label: float | None = None
    label_source: str | None = None


@dataclass
class JudgeCalibrationMetric:
    metric: str
    method: str
    sample_count: int
    label_count: int
    mae: float | None
    pearson: float | None
    spearman: float | None
    temperature: float | None = None
    parameters: dict[str, float | None] = field(default_factory=dict)
    gate_passed: bool | None = None
    warning: str | None = None


@dataclass
class JudgeCalibrationSummary:
    run_id: str
    labels_source: str
    method: str
    metrics: list[str]
    holdout_ratio: float
    seed: int
    total_labels: int
    total_samples: int
    gate_passed: bool
    gate_threshold: float | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class JudgeCalibrationResult:
    summary: JudgeCalibrationSummary
    metrics: list[JudgeCalibrationMetric] = field(default_factory=list)
    case_results: dict[str, list[JudgeCalibrationCase]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
