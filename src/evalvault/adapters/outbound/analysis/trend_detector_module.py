"""Trend detector module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output


class TrendDetectorModule(BaseAnalysisModule):
    """Detect simple trends from time series data."""

    module_id = "trend_detector"
    name = "Trend Detector"
    description = "Detect upward/downward trends in pass rates."
    input_types = ["time_series"]
    output_types = ["trend_detection"]
    requires = ["time_series_analyzer"]
    tags = ["analysis", "trend"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        series_output = get_upstream_output(inputs, "time_series", "time_series_analyzer") or {}
        series = series_output.get("series", [])

        if len(series) < 2:
            return {
                "trends": [],
                "summary": {"note": "Insufficient history"},
            }

        start = series[0]["pass_rate"]
        end = series[-1]["pass_rate"]
        delta = round(end - start, 4)

        if delta > 0.02:
            direction = "up"
            recommendation = "Recent runs show improving performance."
        elif delta < -0.02:
            direction = "down"
            recommendation = "Performance is trending down; investigate changes."
        else:
            direction = "flat"
            recommendation = "Performance is stable across recent runs."

        trends = [
            {
                "metric": "pass_rate",
                "direction": direction,
                "delta": delta,
            }
        ]

        return {
            "trends": trends,
            "summary": {
                "start": start,
                "end": end,
                "delta": delta,
            },
            "recommendations": [recommendation],
        }
