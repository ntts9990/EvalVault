"""Run loader module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import build_run_from_metrics
from evalvault.domain.entities import EvaluationRun
from evalvault.ports.outbound.storage_port import StoragePort


class RunLoaderModule(BaseAnalysisModule):
    """Load one or more evaluation runs for comparison analysis."""

    module_id = "run_loader"
    name = "Run Loader"
    description = "Load evaluation runs for run/model comparison pipelines."
    input_types = ["context"]
    output_types = ["runs", "summaries"]
    tags = ["loader", "runs"]

    def __init__(self, storage: StoragePort | None = None) -> None:
        self._storage = storage

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = inputs.get("__context__", {})
        run_id = context.get("run_id")
        additional_params = context.get("additional_params", {}) or {}
        params = params or {}

        run_ids = additional_params.get("run_ids") or params.get("run_ids") or []
        limit = int(additional_params.get("limit") or params.get("limit") or 2)
        allow_sample = params.get("allow_sample")
        if allow_sample is None:
            allow_sample = additional_params.get("allow_sample", True)
        if isinstance(allow_sample, str):
            allow_sample = allow_sample.strip().lower() in {"1", "true", "yes", "y", "on"}

        runs: list[EvaluationRun] = []
        seen_ids: set[str] = set()
        missing_run_ids: list[str] = []

        if run_ids:
            for candidate in run_ids:
                run = self._load_run(candidate)
                if run:
                    runs.append(run)
                    seen_ids.add(run.run_id)
                else:
                    missing_run_ids.append(candidate)
        elif run_id:
            run = self._load_run(run_id)
            if run:
                runs.append(run)
                seen_ids.add(run.run_id)
            runs.extend(self._load_additional_runs(limit=limit, exclude_ids=seen_ids))
        else:
            runs.extend(self._load_additional_runs(limit=limit, exclude_ids=seen_ids))

        if not runs and allow_sample:
            runs = self._sample_runs()

        summaries = [run.to_summary_dict() for run in runs]
        return {
            "runs": runs,
            "summaries": summaries,
            "count": len(runs),
            "missing_run_ids": missing_run_ids,
        }

    def _load_run(self, run_id: str) -> EvaluationRun | None:
        if not run_id or self._storage is None:
            return None
        try:
            return self._storage.get_run(run_id)
        except KeyError:
            return None

    def _load_additional_runs(
        self,
        *,
        limit: int,
        exclude_ids: set[str],
    ) -> list[EvaluationRun]:
        if self._storage is None or limit <= 0:
            return []
        runs = []
        for run in self._storage.list_runs(limit=limit + len(exclude_ids)):
            if run.run_id in exclude_ids:
                continue
            runs.append(run)
            if len(runs) >= limit:
                break
        return runs

    def _sample_runs(self) -> list[EvaluationRun]:
        metrics_a = {
            "faithfulness": [0.72, 0.75, 0.7, 0.77],
            "answer_relevancy": [0.68, 0.7, 0.66, 0.72],
        }
        metrics_b = {
            "faithfulness": [0.8, 0.83, 0.79, 0.81],
            "answer_relevancy": [0.74, 0.76, 0.73, 0.78],
        }
        run_a = build_run_from_metrics(metrics_a, dataset_name="sample", model_name="A")
        run_b = build_run_from_metrics(metrics_b, dataset_name="sample", model_name="B")
        return [run_a, run_b]
