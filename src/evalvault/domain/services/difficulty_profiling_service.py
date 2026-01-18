from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.services.difficulty_profile_reporter import DifficultyProfileReporter
from evalvault.ports.outbound.storage_port import StoragePort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DifficultyProfileRequest:
    dataset_name: str | None
    run_id: str | None
    limit_runs: int | None
    metrics: tuple[str, ...] | None
    bucket_count: int
    min_samples: int
    output_path: Path
    artifacts_dir: Path
    parallel: bool
    concurrency: int | None


@dataclass(frozen=True)
class DifficultyCaseProfile:
    run_id: str
    test_case_id: str
    metric_scores: dict[str, float]
    avg_score: float
    difficulty_score: float
    bucket: str
    passed: bool


@dataclass(frozen=True)
class DifficultyBucketSummary:
    label: str
    count: int
    ratio: float
    avg_score: float | None
    pass_rate: float | None


class DifficultyProfilingService:
    def __init__(self, *, storage: StoragePort, reporter: DifficultyProfileReporter) -> None:
        self._storage = storage
        self._reporter = reporter

    def profile(self, request: DifficultyProfileRequest) -> dict[str, Any]:
        started_at = datetime.now(UTC)
        logger.info(
            "difficulty profiling started",
            extra={
                "dataset_name": request.dataset_name,
                "run_id": request.run_id,
                "bucket_count": request.bucket_count,
                "parallel": request.parallel,
            },
        )

        runs = self._load_runs(request)
        metrics = self._resolve_metrics(request, runs)
        cases = self._collect_cases(runs, metrics)

        if len(cases) < request.min_samples:
            logger.warning(
                "difficulty profiling aborted: insufficient samples",
                extra={"sample_count": len(cases), "min_samples": request.min_samples},
            )
            raise ValueError("insufficient history to build difficulty profile")

        case_profiles, bucket_summaries = self._assign_buckets(
            cases, bucket_count=request.bucket_count
        )
        breakdown = _build_breakdown(bucket_summaries)
        failure_concentration = _build_failure_concentration(bucket_summaries)

        data = {
            "run_id": request.run_id,
            "dataset_name": request.dataset_name,
            "run_ids": sorted({case.run_id for case in case_profiles}),
            "metrics": list(metrics),
            "bucket_count": request.bucket_count,
            "min_samples": request.min_samples,
            "total_cases": len(case_profiles),
            "dataset_difficulty_distribution": breakdown,
            "accuracy_by_difficulty": _build_accuracy(bucket_summaries),
            "failure_concentration": failure_concentration,
            "buckets": [
                {
                    "label": bucket.label,
                    "count": bucket.count,
                    "ratio": bucket.ratio,
                    "avg_score": bucket.avg_score,
                    "pass_rate": bucket.pass_rate,
                }
                for bucket in bucket_summaries
            ],
        }

        finished_at = datetime.now(UTC)
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        envelope = {
            "command": "profile-difficulty",
            "version": 1,
            "status": "ok",
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_ms": duration_ms,
            "artifacts": {},
            "data": data,
        }

        artifacts_payload = {
            "breakdown": {
                "run_id": request.run_id,
                "dataset_difficulty_distribution": breakdown,
                "accuracy_by_difficulty": _build_accuracy(bucket_summaries),
                "failure_concentration": failure_concentration,
            },
            "cases": [
                {
                    "run_id": case.run_id,
                    "test_case_id": case.test_case_id,
                    "metric_scores": case.metric_scores,
                    "avg_score": case.avg_score,
                    "difficulty_score": case.difficulty_score,
                    "bucket": case.bucket,
                    "passed": case.passed,
                }
                for case in case_profiles
            ],
        }

        artifacts_index = self._reporter.write(
            output_path=request.output_path,
            artifacts_dir=request.artifacts_dir,
            envelope=envelope,
            artifacts=artifacts_payload,
        )
        envelope["artifacts"] = artifacts_index
        logger.info(
            "difficulty profiling completed",
            extra={"artifact_dir": artifacts_index.get("dir"), "case_count": len(case_profiles)},
        )
        return envelope

    def _load_runs(self, request: DifficultyProfileRequest) -> list[EvaluationRun]:
        if request.run_id:
            run = self._storage.get_run(request.run_id)
            return [run]
        if not request.dataset_name:
            raise ValueError("dataset_name or run_id is required")
        limit = request.limit_runs or 50
        runs = self._storage.list_runs(limit=limit, dataset_name=request.dataset_name)
        if not runs:
            raise ValueError("no runs found for dataset")
        return runs

    def _resolve_metrics(
        self, request: DifficultyProfileRequest, runs: list[EvaluationRun]
    ) -> tuple[str, ...]:
        if request.metrics:
            return request.metrics
        metrics: set[str] = set()
        for run in runs:
            metrics.update(run.metrics_evaluated)
        if not metrics:
            raise ValueError("no metrics available for difficulty profiling")
        return tuple(sorted(metrics))

    def _collect_cases(
        self, runs: list[EvaluationRun], metrics: tuple[str, ...]
    ) -> list[tuple[str, TestCaseResult, dict[str, float], bool]]:
        cases = []
        for run in runs:
            for result in run.results:
                metric_scores, passed = _extract_metric_scores(result, metrics)
                if not metric_scores:
                    continue
                cases.append((run.run_id, result, metric_scores, passed))
        return cases

    def _assign_buckets(
        self, cases: list[tuple[str, TestCaseResult, dict[str, float], bool]], *, bucket_count: int
    ) -> tuple[list[DifficultyCaseProfile], list[DifficultyBucketSummary]]:
        sorted_cases = sorted(cases, key=lambda item: _difficulty_score(item[2]))
        total_cases = len(sorted_cases)
        if total_cases == 0:
            return [], []
        labels = _bucket_labels(bucket_count)

        bucket_map: dict[str, list[DifficultyCaseProfile]] = {label: [] for label in labels}

        for index, (run_id, result, metric_scores, passed) in enumerate(sorted_cases):
            bucket_index = min(int(index / total_cases * bucket_count), bucket_count - 1)
            label = labels[bucket_index]
            avg_score = sum(metric_scores.values()) / len(metric_scores)
            difficulty_score = _difficulty_score(metric_scores)
            profile = DifficultyCaseProfile(
                run_id=run_id,
                test_case_id=result.test_case_id,
                metric_scores=metric_scores,
                avg_score=avg_score,
                difficulty_score=difficulty_score,
                bucket=label,
                passed=passed,
            )
            bucket_map[label].append(profile)

        bucket_summaries: list[DifficultyBucketSummary] = []
        case_profiles: list[DifficultyCaseProfile] = []
        for label in labels:
            bucket_cases = bucket_map[label]
            case_profiles.extend(bucket_cases)
            count = len(bucket_cases)
            ratio = count / total_cases if total_cases else 0.0
            avg_score = _safe_average([case.avg_score for case in bucket_cases])
            pass_rate = _safe_average([1.0 if case.passed else 0.0 for case in bucket_cases])
            bucket_summaries.append(
                DifficultyBucketSummary(
                    label=label,
                    count=count,
                    ratio=ratio,
                    avg_score=avg_score,
                    pass_rate=pass_rate,
                )
            )
        return case_profiles, bucket_summaries


def _extract_metric_scores(
    result: TestCaseResult, metrics: tuple[str, ...]
) -> tuple[dict[str, float], bool]:
    scores: dict[str, float] = {}
    passed_all = True
    for metric_name in metrics:
        metric: MetricScore | None = result.get_metric(metric_name)
        if metric is None:
            continue
        scores[metric_name] = float(metric.score)
        passed_all = passed_all and metric.score >= metric.threshold
    if not scores:
        passed_all = False
    return scores, passed_all


def _difficulty_score(metric_scores: dict[str, float]) -> float:
    if not metric_scores:
        return 1.0
    avg_score = sum(metric_scores.values()) / len(metric_scores)
    score = 1.0 - avg_score
    return min(max(score, 0.0), 1.0)


def _safe_average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _bucket_labels(bucket_count: int) -> list[str]:
    if bucket_count == 3:
        return ["easy", "medium", "hard"]
    return [f"bucket_{index}" for index in range(1, bucket_count + 1)]


def _build_breakdown(buckets: list[DifficultyBucketSummary]) -> dict[str, float]:
    return {bucket.label: bucket.ratio for bucket in buckets}


def _build_accuracy(buckets: list[DifficultyBucketSummary]) -> dict[str, float | None]:
    return {bucket.label: bucket.pass_rate for bucket in buckets}


def _build_failure_concentration(buckets: list[DifficultyBucketSummary]) -> dict[str, Any]:
    if not buckets:
        return {
            "primary_difficulty": None,
            "primary_flags": [],
            "actionable_insight": "난이도 분포 데이터가 없습니다.",
        }
    primary = max(buckets, key=lambda bucket: (1 - (bucket.pass_rate or 0.0), bucket.count))
    flags: list[str] = []
    if primary.pass_rate is not None and primary.pass_rate < 0.5:
        flags.append("low_pass_rate")
    if primary.avg_score is not None and primary.avg_score < 0.5:
        flags.append("low_avg_score")
    insight = "난이도 분포에 큰 편차가 없습니다."
    if "low_pass_rate" in flags:
        insight = "해당 난이도 구간에서 정답률이 낮습니다."
    elif "low_avg_score" in flags:
        insight = "메트릭 평균 점수가 낮습니다."
    return {
        "primary_difficulty": primary.label,
        "primary_flags": flags,
        "actionable_insight": insight,
    }
