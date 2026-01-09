"""Run metric comparator module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.common import AnalysisDataProcessor
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output, safe_mean
from evalvault.adapters.outbound.analysis.statistical_adapter import (
    StatisticalAnalysisAdapter,
)
from evalvault.domain.entities import EvaluationRun


class RunMetricComparatorModule(BaseAnalysisModule):
    """Compare two runs with statistical tests per metric."""

    module_id = "run_metric_comparator"
    name = "Run Metric Comparator"
    description = "Compute per-metric comparisons with effect sizes."
    input_types = ["runs"]
    output_types = ["comparison_details"]
    requires = ["run_loader"]
    tags = ["comparison", "statistics"]

    def __init__(self, adapter: StatisticalAnalysisAdapter | None = None) -> None:
        self._adapter = adapter or StatisticalAnalysisAdapter()
        self._processor = AnalysisDataProcessor()

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        context = inputs.get("__context__", {})
        additional = context.get("additional_params", {}) or {}

        runs_output = get_upstream_output(inputs, "load_runs", "run_loader") or {}
        runs: list[EvaluationRun] = runs_output.get("runs", [])
        if len(runs) < 2:
            return {
                "summary": {"note": "Not enough runs to compare."},
                "comparisons": [],
                "notable_changes": [],
            }

        run_a, run_b = runs[0], runs[1]
        metrics = params.get("metrics")
        if metrics is None:
            metrics = additional.get("compare_metrics") or additional.get("metrics")
        metric_list: list[str] | None = None
        if isinstance(metrics, str):
            metric_list = [item.strip() for item in metrics.split(",") if item.strip()]
        elif isinstance(metrics, list):
            metric_list = [str(item) for item in metrics if str(item)]

        test_type = params.get("test_type")
        if test_type is None:
            test_type = additional.get("test_type", "t-test")

        comparisons = self._adapter.compare_runs(
            run_a,
            run_b,
            metrics=metric_list or None,
            test_type=str(test_type),
        )

        comparison_payloads = []
        for comp in comparisons:
            payload = self._processor.to_serializable(comp)
            diff = comp.diff
            if diff > 0:
                direction = "up"
            elif diff < 0:
                direction = "down"
            else:
                direction = "flat"
            payload["direction"] = direction
            comparison_payloads.append(payload)

        notable = self._build_notable_changes(comparisons)
        summary = self._build_summary(run_a, run_b, comparisons)

        return {
            "summary": summary,
            "comparisons": comparison_payloads,
            "notable_changes": notable,
        }

    def _build_summary(
        self,
        run_a: EvaluationRun,
        run_b: EvaluationRun,
        comparisons: list[Any],
    ) -> dict[str, Any]:
        significant = [comp for comp in comparisons if getattr(comp, "is_significant", False)]
        wins = {
            run_a.run_id: 0,
            run_b.run_id: 0,
        }
        for comp in significant:
            winner = getattr(comp, "winner", None)
            if winner in wins:
                wins[winner] += 1

        avg_a = safe_mean(
            [run_a.get_avg_score(metric) or 0.0 for metric in run_a.metrics_evaluated]
        )
        avg_b = safe_mean(
            [run_b.get_avg_score(metric) or 0.0 for metric in run_b.metrics_evaluated]
        )

        return {
            "run_a": run_a.run_id,
            "run_b": run_b.run_id,
            "total_metrics": len(comparisons),
            "significant_metrics": len(significant),
            "wins": wins,
            "pass_rate_a": round(run_a.pass_rate, 4),
            "pass_rate_b": round(run_b.pass_rate, 4),
            "pass_rate_diff": round(run_b.pass_rate - run_a.pass_rate, 4),
            "avg_score_a": round(avg_a, 4),
            "avg_score_b": round(avg_b, 4),
            "avg_score_diff": round(avg_b - avg_a, 4),
        }

    def _build_notable_changes(self, comparisons: list[Any]) -> list[dict[str, Any]]:
        sorted_changes = sorted(
            comparisons,
            key=lambda comp: abs(getattr(comp, "diff", 0.0)),
            reverse=True,
        )
        notable = []
        for comp in sorted_changes[:5]:
            notable.append(
                {
                    "metric": comp.metric,
                    "diff": round(comp.diff, 4),
                    "diff_percent": round(comp.diff_percent, 2),
                    "p_value": round(comp.p_value, 4),
                    "effect_size": round(comp.effect_size, 3),
                    "effect_level": comp.effect_level.value,
                    "winner": comp.winner,
                }
            )
        return notable
