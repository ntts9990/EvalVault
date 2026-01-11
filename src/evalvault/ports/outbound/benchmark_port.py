"""Benchmark adapter port for external benchmark frameworks.

Provides abstraction for running benchmarks like lm-evaluation-harness, HRET, etc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from evalvault.domain.entities.benchmark_run import BenchmarkRun


class BenchmarkBackend(str, Enum):
    HF = "hf"
    VLLM = "vllm"
    OPENAI = "openai"
    API = "api"
    OLLAMA = "ollama"


@dataclass
class BenchmarkRequest:
    """Request to run a benchmark evaluation.

    Attributes:
        tasks: List of task names to evaluate (e.g., ["kmmlu_insurance", "kmmlu_finance"])
        backend: Which model backend to use
        model_args: Backend-specific model arguments
        num_fewshot: Number of few-shot examples (default: 0)
        batch_size: Batch size for evaluation (default: "auto")
        limit: Limit number of examples per task (None = all)
        output_path: Path to save results (optional)
        extra_args: Additional backend-specific arguments
    """

    tasks: list[str]
    backend: BenchmarkBackend = BenchmarkBackend.VLLM
    model_args: dict[str, Any] = field(default_factory=dict)
    num_fewshot: int = 0
    batch_size: str | int = "auto"
    limit: int | None = None
    output_path: str | None = None
    extra_args: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkTaskResult:
    """Result for a single benchmark task.

    Attributes:
        task_name: Name of the task
        metrics: Dictionary of metric name -> value
        num_samples: Number of samples evaluated
        version: Task version
        config: Task configuration used
    """

    task_name: str
    metrics: dict[str, float] = field(default_factory=dict)
    num_samples: int = 0
    version: str = "0"
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResponse:
    """Response from a benchmark evaluation.

    Attributes:
        results: Dictionary of task name -> BenchmarkTaskResult
        model_name: Model identifier used
        backend: Backend used for evaluation
        total_time_seconds: Total evaluation time
        raw_output: Raw output from the benchmark framework (for debugging)
        error: Error message if evaluation failed
    """

    results: dict[str, BenchmarkTaskResult] = field(default_factory=dict)
    model_name: str = ""
    backend: BenchmarkBackend = BenchmarkBackend.VLLM
    total_time_seconds: float = 0.0
    raw_output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def success(self) -> bool:
        """Check if evaluation completed successfully."""
        return self.error is None and len(self.results) > 0

    def get_main_score(self, task_name: str, metric: str = "acc") -> float | None:
        """Get main score for a task.

        Args:
            task_name: Name of the task
            metric: Metric name (default: "acc" for accuracy)

        Returns:
            Score value or None if not found
        """
        if task_name not in self.results:
            return None
        task_result = self.results[task_name]
        # Try exact match first
        if metric in task_result.metrics:
            return task_result.metrics[metric]
        # Try with ",none" suffix (lm-eval format)
        key_with_suffix = f"{metric},none"
        if key_with_suffix in task_result.metrics:
            return task_result.metrics[key_with_suffix]
        return None

    def to_breakdown_dict(self) -> dict[str, Any]:
        """Convert to breakdown format for VisualSpaceService.

        Returns:
            Dictionary suitable for insertion into breakdown.benchmark
        """
        if not self.results:
            return {}

        # Aggregate scores by domain
        subject_accuracy: dict[str, float] = {}
        total_acc = 0.0
        count = 0

        for task_name, result in self.results.items():
            acc = result.metrics.get("acc") or result.metrics.get("acc,none")
            if acc is not None:
                # Extract subject name (e.g., "kmmlu_insurance" -> "insurance")
                subject = task_name.replace("kmmlu_", "").replace("_", " ").title()
                subject_accuracy[subject] = acc
                total_acc += acc
                count += 1

        return {
            "kmmlu_accuracy": total_acc / count if count > 0 else 0.0,
            "kmmlu_subject_accuracy": subject_accuracy,
            "model": self.model_name,
            "backend": self.backend.value,
            "evaluation_time_seconds": self.total_time_seconds,
        }


class BenchmarkPort(ABC):
    """Port interface for benchmark frameworks.

    Implementations should wrap specific frameworks like lm-evaluation-harness
    and provide a unified interface for running evaluations.
    """

    @abstractmethod
    def run_benchmark(self, request: BenchmarkRequest) -> BenchmarkResponse:
        """Run a benchmark evaluation.

        Args:
            request: Benchmark request with tasks and configuration

        Returns:
            BenchmarkResponse with results or error
        """
        pass

    @abstractmethod
    def list_available_tasks(self) -> list[str]:
        """List all available benchmark tasks.

        Returns:
            List of task names that can be evaluated
        """
        pass

    @abstractmethod
    def get_task_info(self, task_name: str) -> dict[str, Any]:
        """Get information about a specific task.

        Args:
            task_name: Name of the task

        Returns:
            Dictionary with task metadata (description, metrics, etc.)
        """
        pass

    def supports_backend(self, backend: BenchmarkBackend) -> bool:
        """Check if a backend is supported.

        Args:
            backend: Backend to check

        Returns:
            True if backend is supported
        """
        return True


class BenchmarkStoragePort(ABC):
    """Port interface for benchmark result persistence."""

    @abstractmethod
    def save_benchmark_run(self, run: "BenchmarkRun") -> str:
        """Save a benchmark run to storage.

        Args:
            run: BenchmarkRun entity to save

        Returns:
            Saved run_id
        """
        pass

    @abstractmethod
    def get_benchmark_run(self, run_id: str) -> "BenchmarkRun":
        """Retrieve a benchmark run by ID.

        Args:
            run_id: Run identifier

        Returns:
            BenchmarkRun entity

        Raises:
            KeyError: If run not found
        """
        pass

    @abstractmethod
    def list_benchmark_runs(
        self,
        benchmark_type: str | None = None,
        model_name: str | None = None,
        limit: int = 100,
    ) -> list["BenchmarkRun"]:
        """List benchmark runs with optional filtering.

        Args:
            benchmark_type: Filter by benchmark type
            model_name: Filter by model name
            limit: Maximum number of results

        Returns:
            List of BenchmarkRun entities
        """
        pass
