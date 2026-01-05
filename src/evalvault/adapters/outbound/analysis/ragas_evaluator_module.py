"""RAGAS evaluator module for pipeline."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import (
    average_scores,
    get_upstream_output,
    group_scores_by_metric,
    safe_mean,
    truncate_text,
)
from evalvault.domain.entities import EvaluationRun


class RagasEvaluatorModule(BaseAnalysisModule):
    """Summarize RAGAS-style metric scores from run data."""

    module_id = "ragas_evaluator"
    name = "RAGAS Evaluator"
    description = "Aggregate per-case RAGAS scores for downstream diagnostics."
    input_types = ["run", "metrics"]
    output_types = ["ragas_summary", "metrics"]
    requires = ["data_loader"]
    tags = ["analysis", "ragas"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")
        metrics = loader_output.get("metrics", {}) or {}

        per_case: list[dict[str, Any]] = []
        if isinstance(run, EvaluationRun):
            metrics = group_scores_by_metric(run)
            for result in run.results:
                metric_scores = {m.name: m.score for m in result.metrics}
                avg_score = safe_mean(metric_scores.values())
                per_case.append(
                    {
                        "test_case_id": result.test_case_id,
                        "metrics": metric_scores,
                        "avg_score": round(avg_score, 4),
                        "question_preview": truncate_text(result.question),
                    }
                )

        avg_scores = average_scores(metrics)
        overall = safe_mean(avg_scores.values())
        sample_count = max((len(values) for values in metrics.values()), default=0)

        summary = {
            "metric_count": len(avg_scores),
            "sample_count": sample_count,
            "overall_score": round(overall, 4),
        }

        return {
            "summary": summary,
            "metrics": avg_scores,
            "per_case": per_case,
        }
