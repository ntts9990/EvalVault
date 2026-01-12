from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorStage(str, Enum):
    preprocess = "preprocess"
    evaluate = "evaluate"
    analyze = "analyze"
    compare = "compare"
    storage = "storage"


class McpError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    retryable: bool = False
    stage: ErrorStage | None = None


class RunSummaryPayload(BaseModel):
    run_id: str
    dataset_name: str
    model_name: str
    pass_rate: float
    total_test_cases: int
    passed_test_cases: int
    started_at: str
    finished_at: str | None = None
    metrics_evaluated: list[str] = Field(default_factory=list)
    threshold_profile: str | None = None
    run_mode: str | None = None
    evaluation_task: str | None = None
    project_name: str | None = None
    avg_metric_scores: dict[str, float] | None = None
    thresholds: dict[str, float] | None = None

    model_config = ConfigDict(extra="allow")


class ListRunsRequest(BaseModel):
    limit: int = Field(50, ge=1, le=500)
    dataset_name: str | None = None
    model_name: str | None = None
    run_mode: str | None = None
    project_names: list[str] | None = None
    db_path: Path | None = None


class ListRunsResponse(BaseModel):
    runs: list[RunSummaryPayload] = Field(default_factory=list)
    errors: list[McpError] = Field(default_factory=list)


class GetRunSummaryRequest(BaseModel):
    run_id: str
    db_path: Path | None = None


class GetRunSummaryResponse(BaseModel):
    summary: RunSummaryPayload | None = None
    errors: list[McpError] = Field(default_factory=list)


class ArtifactsKind(str, Enum):
    analysis = "analysis"
    comparison = "comparison"


class GetArtifactsRequest(BaseModel):
    run_id: str
    kind: ArtifactsKind = ArtifactsKind.analysis
    comparison_run_id: str | None = None
    base_dir: Path | None = None


class ArtifactsPayload(BaseModel):
    kind: Literal["analysis", "comparison"]
    report_path: str | None = None
    output_path: str | None = None
    artifacts_dir: str | None = None
    artifacts_index_path: str | None = None


class GetArtifactsResponse(BaseModel):
    run_id: str
    artifacts: ArtifactsPayload | None = None
    errors: list[McpError] = Field(default_factory=list)


class RunEvaluationRequest(BaseModel):
    dataset_path: Path
    metrics: list[str]
    profile: str | None = None
    model_name: str | None = None
    evaluation_task: str | None = None
    db_path: Path | None = None
    thresholds: dict[str, float] | None = None
    threshold_profile: str | None = None
    parallel: bool = True
    batch_size: int = 5
    auto_analyze: bool = False
    analysis_output: Path | None = None
    analysis_report: Path | None = None
    analysis_dir: Path | None = None


class EvaluationArtifactsPayload(BaseModel):
    analysis_report_path: str | None = None
    analysis_output_path: str | None = None
    analysis_artifacts_dir: str | None = None
    analysis_artifacts_index_path: str | None = None


class RunEvaluationResponse(BaseModel):
    run_id: str
    metrics: dict[str, float | None] = Field(default_factory=dict)
    thresholds: dict[str, float] | None = None
    artifacts: EvaluationArtifactsPayload | None = None
    errors: list[McpError] = Field(default_factory=list)


class AnalyzeCompareRequest(BaseModel):
    run_id_a: str
    run_id_b: str
    metrics: list[str] | None = None
    test_type: Literal["t-test", "mann-whitney"] = "t-test"
    profile: str | None = None
    db_path: Path | None = None
    output: Path | None = None
    report: Path | None = None
    output_dir: Path | None = None


class MetricsDeltaPayload(BaseModel):
    avg: dict[str, float] = Field(default_factory=dict)
    by_metric: dict[str, float] = Field(default_factory=dict)
    notes: list[str] | None = None


class ComparisonArtifactsPayload(BaseModel):
    json_path: str | None = None
    report_path: str | None = None
    artifacts_dir: str | None = None
    artifacts_index_path: str | None = None


class AnalyzeCompareResponse(BaseModel):
    baseline_run_id: str
    candidate_run_id: str
    comparison_report_path: str | None = None
    metrics_delta: MetricsDeltaPayload = Field(default_factory=MetricsDeltaPayload)
    artifacts: ComparisonArtifactsPayload | None = None
    errors: list[McpError] = Field(default_factory=list)
