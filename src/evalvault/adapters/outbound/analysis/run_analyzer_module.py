"""Run analyzer module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output, safe_mean
from evalvault.domain.entities import EvaluationRun


class RunAnalyzerModule(BaseAnalysisModule):
    """Summarize metrics for each run."""

    module_id = "run_analyzer"
    name = "Run Analyzer"
    description = "Summarize metrics for each evaluation run."
    input_types = ["runs"]
    output_types = ["run_summary", "statistics"]
    requires = ["run_loader"]
    tags = ["analysis", "comparison"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        runs_output = get_upstream_output(inputs, "load_runs", "run_loader") or {}
        runs: list[EvaluationRun] = runs_output.get("runs", [])

        if not runs:
            return {
                "summary": {},
                "runs": {},
                "insights": ["No runs available for analysis."],
            }

        runs_summary: dict[str, Any] = {}
        for run in runs:
            avg_metric_scores = {}
            for metric_name in run.metrics_evaluated:
                avg = run.get_avg_score(metric_name)
                if avg is not None:
                    avg_metric_scores[metric_name] = round(avg, 4)

            overall_score = safe_mean(avg_metric_scores.values())
            if overall_score == 0.0:
                overall_score = run.pass_rate

            runs_summary[run.run_id] = {
                "dataset_name": run.dataset_name,
                "model_name": run.model_name,
                "avg_metric_scores": avg_metric_scores,
                "pass_rate": round(run.pass_rate, 4),
                "overall_score": round(overall_score, 4),
                "started_at": run.started_at.isoformat(),
            }

        summary = {
            "run_count": len(runs_summary),
        }

        return {
            "summary": summary,
            "runs": runs_summary,
            "insights": [],
        }
