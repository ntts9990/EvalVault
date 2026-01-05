"""Run comparator module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output, safe_mean
from evalvault.domain.entities import EvaluationRun


class RunComparatorModule(BaseAnalysisModule):
    """Compare runs using overall score heuristics."""

    module_id = "run_comparator"
    name = "Run Comparator"
    description = "Compare evaluation runs by average metric scores."
    input_types = ["runs"]
    output_types = ["comparison"]
    requires = ["run_loader"]
    tags = ["comparison", "runs"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        runs_output = get_upstream_output(inputs, "load_runs", "run_loader") or {}
        runs: list[EvaluationRun] = runs_output.get("runs", [])

        if not runs:
            return {"winner": "N/A"}

        scores: dict[str, float] = {}
        for run in runs:
            metric_scores = []
            for metric_name in run.metrics_evaluated:
                avg = run.get_avg_score(metric_name)
                if avg is not None:
                    metric_scores.append(avg)
            overall = safe_mean(metric_scores) if metric_scores else run.pass_rate
            scores[run.run_id] = overall

        winner = max(scores, key=scores.get)
        comparison: dict[str, Any] = {"winner": winner}
        for run_id, score in scores.items():
            comparison[run_id] = {"score": round(score, 4)}

        return comparison
