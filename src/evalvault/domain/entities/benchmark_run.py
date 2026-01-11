"""Benchmark run domain entity for storing benchmark evaluation results."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class BenchmarkType(str, Enum):
    KMMLU = "kmmlu"
    MMLU = "mmlu"
    CUSTOM = "custom"


class BenchmarkStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class BenchmarkTaskScore:
    task_name: str
    accuracy: float
    num_samples: int
    metrics: dict[str, float] = field(default_factory=dict)
    version: str = "0"


@dataclass
class BenchmarkRun:
    run_id: str
    benchmark_type: BenchmarkType
    model_name: str
    backend: str
    tasks: list[str]
    status: BenchmarkStatus = BenchmarkStatus.PENDING
    task_scores: list[BenchmarkTaskScore] = field(default_factory=list)
    overall_accuracy: float | None = None
    num_fewshot: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    duration_seconds: float = 0.0
    error_message: str | None = None
    phoenix_trace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        benchmark_type: BenchmarkType,
        model_name: str,
        backend: str,
        tasks: list[str],
        num_fewshot: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> BenchmarkRun:
        return cls(
            run_id=f"bench_{uuid.uuid4().hex[:12]}",
            benchmark_type=benchmark_type,
            model_name=model_name,
            backend=backend,
            tasks=tasks,
            num_fewshot=num_fewshot,
            metadata=metadata or {},
        )

    def start(self) -> None:
        self.status = BenchmarkStatus.RUNNING
        self.started_at = datetime.now(UTC)

    def complete(self, task_scores: list[BenchmarkTaskScore]) -> None:
        self.status = BenchmarkStatus.COMPLETED
        self.finished_at = datetime.now(UTC)
        self.task_scores = task_scores
        self.duration_seconds = (self.finished_at - self.started_at).total_seconds()
        self._calculate_overall_accuracy()

    def fail(self, error_message: str) -> None:
        self.status = BenchmarkStatus.FAILED
        self.finished_at = datetime.now(UTC)
        self.error_message = error_message
        if self.started_at:
            self.duration_seconds = (self.finished_at - self.started_at).total_seconds()

    def set_phoenix_trace_id(self, trace_id: str) -> None:
        self.phoenix_trace_id = trace_id

    def _calculate_overall_accuracy(self) -> None:
        if not self.task_scores:
            self.overall_accuracy = None
            return
        total_samples = sum(ts.num_samples for ts in self.task_scores)
        if total_samples == 0:
            self.overall_accuracy = None
            return
        weighted_sum = sum(ts.accuracy * ts.num_samples for ts in self.task_scores)
        self.overall_accuracy = weighted_sum / total_samples

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "benchmark_type": self.benchmark_type.value,
            "model_name": self.model_name,
            "backend": self.backend,
            "tasks": self.tasks,
            "status": self.status.value,
            "task_scores": [
                {
                    "task_name": ts.task_name,
                    "accuracy": ts.accuracy,
                    "num_samples": ts.num_samples,
                    "metrics": ts.metrics,
                    "version": ts.version,
                }
                for ts in self.task_scores
            ],
            "overall_accuracy": self.overall_accuracy,
            "num_fewshot": self.num_fewshot,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "phoenix_trace_id": self.phoenix_trace_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BenchmarkRun:
        task_scores = [
            BenchmarkTaskScore(
                task_name=ts["task_name"],
                accuracy=ts["accuracy"],
                num_samples=ts["num_samples"],
                metrics=ts.get("metrics", {}),
                version=ts.get("version", "0"),
            )
            for ts in data.get("task_scores", [])
        ]
        started_at = data.get("started_at")
        finished_at = data.get("finished_at")
        return cls(
            run_id=data["run_id"],
            benchmark_type=BenchmarkType(data["benchmark_type"]),
            model_name=data["model_name"],
            backend=data["backend"],
            tasks=data["tasks"],
            status=BenchmarkStatus(data["status"]),
            task_scores=task_scores,
            overall_accuracy=data.get("overall_accuracy"),
            num_fewshot=data.get("num_fewshot", 0),
            started_at=datetime.fromisoformat(started_at) if started_at else datetime.now(UTC),
            finished_at=datetime.fromisoformat(finished_at) if finished_at else None,
            duration_seconds=data.get("duration_seconds", 0.0),
            error_message=data.get("error_message"),
            phoenix_trace_id=data.get("phoenix_trace_id"),
            metadata=data.get("metadata", {}),
        )
