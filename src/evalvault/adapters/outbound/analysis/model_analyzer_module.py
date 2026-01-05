"""Model analyzer module."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output, safe_mean
from evalvault.domain.entities import EvaluationRun


class ModelAnalyzerModule(BaseAnalysisModule):
    """Aggregate run metrics by model."""

    module_id = "model_analyzer"
    name = "Model Analyzer"
    description = "Summarize metrics by model across multiple runs."
    input_types = ["runs"]
    output_types = ["model_summary", "statistics"]
    requires = ["run_loader"]
    tags = ["analysis", "comparison"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        runs_output = get_upstream_output(inputs, "load_runs", "run_loader") or {}
        runs = runs_output.get("runs", [])

        if not runs:
            return {
                "summary": {},
                "models": {},
                "insights": ["No runs available for model comparison."],
            }

        model_map: dict[str, list[EvaluationRun]] = defaultdict(list)
        for run in runs:
            model_map[run.model_name or "unknown"].append(run)

        models: dict[str, Any] = {}
        for model_name, model_runs in model_map.items():
            pass_rates = [run.pass_rate for run in model_runs]
            metric_scores: dict[str, list[float]] = defaultdict(list)
            for run in model_runs:
                for metric_name in run.metrics_evaluated:
                    avg = run.get_avg_score(metric_name)
                    if avg is not None:
                        metric_scores[metric_name].append(avg)

            avg_metric_scores = {
                metric: round(safe_mean(values), 4) for metric, values in metric_scores.items()
            }

            overall_score = safe_mean(avg_metric_scores.values())
            if overall_score == 0.0:
                overall_score = safe_mean(pass_rates)

            models[model_name] = {
                "run_count": len(model_runs),
                "run_ids": [run.run_id for run in model_runs],
                "avg_pass_rate": round(safe_mean(pass_rates), 4),
                "avg_metric_scores": avg_metric_scores,
                "overall_score": round(overall_score, 4),
            }

        summary = {
            "model_count": len(models),
            "total_runs": len(runs),
        }

        return {
            "summary": summary,
            "models": models,
            "insights": [],
        }
