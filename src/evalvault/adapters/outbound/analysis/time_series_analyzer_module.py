"""Time series analyzer module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output, safe_mean
from evalvault.domain.entities import EvaluationRun


class TimeSeriesAnalyzerModule(BaseAnalysisModule):
    """Build a simple time series from run history."""

    module_id = "time_series_analyzer"
    name = "Time Series Analyzer"
    description = "Build a time series of pass rates across runs."
    input_types = ["runs"]
    output_types = ["time_series"]
    requires = ["run_loader"]
    tags = ["analysis", "trend"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        runs_output = get_upstream_output(inputs, "load_runs", "run_loader") or {}
        runs: list[EvaluationRun] = runs_output.get("runs", [])

        if not runs:
            return {
                "series": [],
                "summary": {},
                "insights": ["No runs available for trend analysis."],
            }

        series = [
            {
                "run_id": run.run_id,
                "timestamp": run.started_at.isoformat(),
                "pass_rate": round(run.pass_rate, 4),
                "model_name": run.model_name,
            }
            for run in runs
        ]
        series.sort(key=lambda item: item.get("timestamp") or "")

        pass_rates = [item["pass_rate"] for item in series]
        summary = {
            "run_count": len(series),
            "avg_pass_rate": round(safe_mean(pass_rates), 4),
            "start": series[0]["timestamp"],
            "end": series[-1]["timestamp"],
        }

        return {
            "series": series,
            "summary": summary,
        }
