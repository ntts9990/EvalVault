"""Benchmark orchestration service following hexagonal architecture."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from evalvault.domain.entities.benchmark_run import (
    BenchmarkRun,
    BenchmarkTaskScore,
    BenchmarkType,
)
from evalvault.ports.outbound.benchmark_port import (
    BenchmarkBackend,
    BenchmarkPort,
    BenchmarkRequest,
    BenchmarkResponse,
    BenchmarkStoragePort,
)

if TYPE_CHECKING:
    from evalvault.ports.outbound.tracer_port import TracerPort

logger = logging.getLogger(__name__)


class BenchmarkService:
    """Domain service for orchestrating benchmark evaluations.

    Coordinates between:
    - BenchmarkPort: External benchmark framework (lm-eval)
    - BenchmarkStoragePort: Result persistence (SQLite)
    - TracerPort: Observability (Phoenix)
    """

    def __init__(
        self,
        benchmark_adapter: BenchmarkPort,
        storage_adapter: BenchmarkStoragePort | None = None,
        tracer_adapter: TracerPort | None = None,
    ):
        self._benchmark = benchmark_adapter
        self._storage = storage_adapter
        self._tracer = tracer_adapter

    def run_kmmlu(
        self,
        subjects: list[str],
        model_name: str,
        backend: BenchmarkBackend,
        num_fewshot: int = 5,
        limit: int | None = None,
        model_args: dict | None = None,
        use_direct: bool | None = None,
    ) -> BenchmarkRun:
        should_use_direct = self._should_use_direct_tasks(backend, use_direct)
        task_prefix = "kmmlu_direct_" if should_use_direct else "kmmlu_"
        tasks = [f"{task_prefix}{s.lower().replace(' ', '_')}" for s in subjects]

        run = BenchmarkRun.create(
            benchmark_type=BenchmarkType.KMMLU,
            model_name=model_name,
            backend=backend.value,
            tasks=tasks,
            num_fewshot=num_fewshot,
            metadata={"subjects": subjects, "limit": limit, "use_direct": should_use_direct},
        )

        return self._execute_benchmark(run, model_args or {}, limit)

    def run_custom(
        self,
        tasks: list[str],
        model_name: str,
        backend: BenchmarkBackend,
        num_fewshot: int = 0,
        limit: int | None = None,
        model_args: dict | None = None,
    ) -> BenchmarkRun:
        run = BenchmarkRun.create(
            benchmark_type=BenchmarkType.CUSTOM,
            model_name=model_name,
            backend=backend.value,
            tasks=tasks,
            num_fewshot=num_fewshot,
        )

        return self._execute_benchmark(run, model_args or {}, limit)

    def _execute_benchmark(
        self,
        run: BenchmarkRun,
        model_args: dict,
        limit: int | None,
    ) -> BenchmarkRun:
        run.start()

        span_attributes = {
            "benchmark.run_id": run.run_id,
            "benchmark.type": run.benchmark_type.value,
            "benchmark.model": run.model_name,
            "benchmark.backend": run.backend,
            "benchmark.tasks": ",".join(run.tasks),
        }

        span_ctx = (
            self._tracer.span(f"benchmark_{run.benchmark_type.value}", span_attributes)
            if self._tracer
            else None
        )

        try:
            if span_ctx:
                span_ctx.__enter__()

            request = BenchmarkRequest(
                tasks=run.tasks,
                backend=BenchmarkBackend(run.backend),
                model_args=model_args,
                num_fewshot=run.num_fewshot,
                limit=limit,
            )

            response = self._benchmark.run_benchmark(request)

            if response.success:
                task_scores = self._convert_response_to_scores(response)
                run.complete(task_scores)
                logger.info(
                    "Benchmark completed: run_id=%s, accuracy=%.4f",
                    run.run_id,
                    run.overall_accuracy or 0.0,
                )
            else:
                run.fail(response.error or "Unknown error")
                logger.error("Benchmark failed: run_id=%s, error=%s", run.run_id, response.error)

        except Exception as e:
            run.fail(str(e))
            logger.exception("Benchmark execution error: run_id=%s", run.run_id)

        finally:
            if span_ctx:
                span_ctx.__exit__(None, None, None)

        if self._storage:
            self._storage.save_benchmark_run(run)
            logger.info("Benchmark run saved: run_id=%s", run.run_id)

        return run

    def _convert_response_to_scores(self, response: BenchmarkResponse) -> list[BenchmarkTaskScore]:
        scores = []
        for task_name, result in response.results.items():
            acc = (
                result.metrics.get("acc,none")
                or result.metrics.get("acc")
                or result.metrics.get("exact_match,none")
                or result.metrics.get("exact_match")
                or 0.0
            )
            scores.append(
                BenchmarkTaskScore(
                    task_name=task_name,
                    accuracy=acc or 0.0,
                    num_samples=result.num_samples,
                    metrics=result.metrics,
                    version=result.version,
                )
            )
        return scores

    @staticmethod
    def _should_use_direct_tasks(backend: BenchmarkBackend, use_direct: bool | None) -> bool:
        if use_direct is not None:
            return use_direct
        backends_without_loglikelihood = {BenchmarkBackend.OPENAI, BenchmarkBackend.OLLAMA}
        return backend in backends_without_loglikelihood

    def get_run(self, run_id: str) -> BenchmarkRun | None:
        if not self._storage:
            return None
        try:
            return self._storage.get_benchmark_run(run_id)
        except KeyError:
            return None

    def list_runs(
        self,
        benchmark_type: str | None = None,
        model_name: str | None = None,
        limit: int = 100,
    ) -> list[BenchmarkRun]:
        if not self._storage:
            return []
        return self._storage.list_benchmark_runs(
            benchmark_type=benchmark_type,
            model_name=model_name,
            limit=limit,
        )
