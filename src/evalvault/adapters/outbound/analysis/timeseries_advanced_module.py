from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from importlib import import_module
from typing import Any

import numpy as np

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import (
    get_upstream_output,
    to_serializable,
)


@dataclass
class AnomalyResult:
    run_id: str
    anomaly_score: float
    pass_rate: float
    timestamp: str
    is_anomaly: bool = False
    severity: str = "none"


@dataclass
class AnomalyDetectionResult:
    anomalies: list[AnomalyResult] = field(default_factory=list)
    threshold: float = 0.95
    total_runs: int = 0
    detection_method: str = "STOMP"
    insights: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ForecastResult:
    metric_name: str
    horizon: int
    predicted_values: list[float] = field(default_factory=list)
    confidence_intervals: list[tuple[float, float]] = field(default_factory=list)
    method: str = "ExponentialSmoothing"


@dataclass
class TimeSeriesAnalysisResult:
    pass_rates: list[float] = field(default_factory=list)
    run_ids: list[str] = field(default_factory=list)
    anomaly_detection: AnomalyDetectionResult | None = None
    forecast: ForecastResult | None = None
    insights: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class TimeSeriesAdvancedModule(BaseAnalysisModule):
    module_id = "timeseries_advanced"
    name = "Time Series Advanced"
    description = "Detect anomalies and forecast pass rate trends."
    input_types = ["runs"]
    output_types = ["anomaly_detection", "forecast"]
    requires = ["run_loader"]
    tags = ["analysis", "timeseries"]

    def __init__(self, window_size: int = 200) -> None:
        self.window_size = window_size
        self._stomp_cls: Any | None = None
        self._exp_smoothing_cls: Any | None = None

    def _load_dependencies(self) -> None:
        try:
            stomp_mod = import_module("aeon.anomaly_detection.series.distance_based")
            forecasting_mod = import_module("aeon.forecasting")
        except ModuleNotFoundError as exc:
            raise ImportError(
                "aeon library not found. Install with: uv sync --extra timeseries"
            ) from exc

        stomp_cls = getattr(stomp_mod, "STOMP", None)
        exp_cls = getattr(forecasting_mod, "ExponentialSmoothing", None)
        if stomp_cls is None or exp_cls is None:
            raise ImportError(
                "aeon library missing expected classes. Install with: uv sync --extra timeseries"
            )

        self._stomp_cls = stomp_cls
        self._exp_smoothing_cls = exp_cls

    def detect_anomalies(
        self,
        run_history: list[dict[str, Any]],
        min_runs: int = 5,
    ) -> AnomalyDetectionResult:
        if len(run_history) < min_runs:
            return AnomalyDetectionResult(
                anomalies=[],
                threshold=0.95,
                total_runs=len(run_history),
                detection_method="STOMP (insufficient data)",
                insights=[f"Need at least {min_runs} runs for anomaly detection."],
            )

        if self._stomp_cls is None:
            self._load_dependencies()
        assert self._stomp_cls is not None

        pass_rates = np.array([float(run.get("pass_rate", 0.0)) for run in run_history])
        run_ids = [str(run.get("run_id", "")) for run in run_history]

        window = min(self.window_size, max(1, len(pass_rates) // 2))
        detector = self._stomp_cls(window_size=window)
        anomaly_scores = detector.fit_predict(pass_rates)

        threshold = float(np.percentile(anomaly_scores, 95))

        anomalies: list[AnomalyResult] = []
        for score, run_id, pass_rate in zip(anomaly_scores, run_ids, pass_rates, strict=False):
            score_val = float(score)
            pass_rate_val = float(pass_rate)
            is_anomaly = score_val > threshold
            severity = self._calculate_severity(score_val, threshold)
            anomalies.append(
                AnomalyResult(
                    run_id=run_id,
                    anomaly_score=score_val,
                    pass_rate=pass_rate_val,
                    timestamp=datetime.now().isoformat(),
                    is_anomaly=is_anomaly,
                    severity=severity,
                )
            )

        insights = self._generate_anomaly_insights(anomalies, threshold)

        return AnomalyDetectionResult(
            anomalies=anomalies,
            threshold=threshold,
            total_runs=len(run_history),
            detection_method="STOMP",
            insights=insights,
        )

    def forecast_performance(
        self,
        run_history: list[dict[str, Any]],
        horizon: int = 3,
        min_runs: int = 10,
    ) -> ForecastResult:
        if len(run_history) < min_runs:
            return ForecastResult(
                metric_name="pass_rate",
                horizon=horizon,
                predicted_values=[],
                method="ExponentialSmoothing (insufficient data)",
            )

        if self._exp_smoothing_cls is None:
            self._load_dependencies()
        assert self._exp_smoothing_cls is not None

        pass_rates = np.array([float(run.get("pass_rate", 0.0)) for run in run_history])

        forecaster = self._exp_smoothing_cls(sp=0.2)
        forecaster.fit(pass_rates)

        fh = list(range(1, horizon + 1))
        predictions = forecaster.predict(fh=fh)

        return ForecastResult(
            metric_name="pass_rate",
            horizon=horizon,
            predicted_values=[float(p) for p in predictions],
            method="ExponentialSmoothing",
        )

    def analyze_time_series(
        self,
        run_history: list[dict[str, Any]],
        detect_anomalies: bool = True,
        forecast_horizon: int | None = None,
    ) -> TimeSeriesAnalysisResult:
        pass_rates = [float(run.get("pass_rate", 0.0)) for run in run_history]
        run_ids = [str(run.get("run_id", "")) for run in run_history]

        result = TimeSeriesAnalysisResult(pass_rates=pass_rates, run_ids=run_ids)

        if detect_anomalies:
            result.anomaly_detection = self.detect_anomalies(run_history)

        if forecast_horizon:
            result.forecast = self.forecast_performance(run_history, horizon=forecast_horizon)

        result.insights = self._generate_insights(result)
        return result

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        context = inputs.get("__context__", {})
        additional_params = context.get("additional_params", {}) or {}

        mode = params.get("mode") or additional_params.get("mode") or "anomaly"
        window_size = additional_params.get("window_size") or params.get("window_size")
        if window_size is not None:
            self.window_size = int(window_size)

        horizon = (
            additional_params.get("forecast_horizon")
            or additional_params.get("horizon")
            or params.get("forecast_horizon")
            or params.get("horizon")
        )

        runs_output = get_upstream_output(inputs, "load_runs", "run_loader") or {}
        runs = runs_output.get("runs", [])
        run_history: list[dict[str, Any]] = []
        for run in runs:
            started_at = getattr(run, "started_at", None)
            run_history.append(
                {
                    "run_id": getattr(run, "run_id", ""),
                    "pass_rate": getattr(run, "pass_rate", 0.0),
                    "timestamp": started_at.isoformat() if started_at else None,
                }
            )

        if not run_history:
            return {
                "mode": mode,
                "anomaly_detection": None,
                "forecast": None,
                "insights": ["No runs available for time series analysis."],
            }

        if mode == "forecast":
            forecast_horizon = int(horizon or 3)
            forecast_result = self.forecast_performance(run_history, horizon=forecast_horizon)
            return {
                "mode": mode,
                "forecast": to_serializable(forecast_result),
                "anomaly_detection": None,
                "insights": [],
            }

        if mode == "anomaly":
            anomaly_result = self.detect_anomalies(run_history)
            return {
                "mode": mode,
                "anomaly_detection": to_serializable(anomaly_result),
                "forecast": None,
                "insights": anomaly_result.insights,
            }

        forecast_horizon = int(horizon) if horizon else None
        analysis_result = self.analyze_time_series(
            run_history,
            detect_anomalies=True,
            forecast_horizon=forecast_horizon,
        )
        return {
            "mode": mode,
            "anomaly_detection": to_serializable(analysis_result.anomaly_detection),
            "forecast": to_serializable(analysis_result.forecast),
            "insights": analysis_result.insights,
        }

    def _calculate_severity(self, score: float, threshold: float) -> str:
        ratio = score / threshold if threshold > 0 else 0.0
        if ratio < 1.2:
            return "low"
        if ratio < 1.5:
            return "medium"
        return "high"

    def _generate_anomaly_insights(
        self, anomalies: list[AnomalyResult], threshold: float
    ) -> list[str]:
        if not anomalies:
            return ["No anomalies detected in the run history."]

        severity_counts: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
        for anomaly in anomalies:
            if anomaly.is_anomaly:
                severity_counts[anomaly.severity] += 1

        insights: list[str] = []
        insights.append(
            f"Detected {len(anomalies)} total anomalies using threshold {threshold:.2f}"
        )
        insights.append(
            "Severity breakdown: "
            f"High={severity_counts['high']}, Medium={severity_counts['medium']}, "
            f"Low={severity_counts['low']}"
        )

        recent_anomalies = [a for a in anomalies if a.is_anomaly][-3:]
        if recent_anomalies:
            most_recent = recent_anomalies[-1]
            insights.append(
                f"Most recent anomaly: {most_recent.run_id[:8]}... "
                f"with severity {most_recent.severity}"
            )

        if len(recent_anomalies) >= 2:
            insights.append("Multiple anomalies detected - investigate potential degradation")

        return insights

    def _generate_insights(self, result: TimeSeriesAnalysisResult) -> list[str]:
        insights: list[str] = []

        if len(result.pass_rates) >= 3:
            recent_avg = float(np.mean(result.pass_rates[-3:]))
            overall_avg = float(np.mean(result.pass_rates))

            if recent_avg > overall_avg + 0.05:
                insights.append("Performance trend: IMPROVING (recent average +5%)")
            elif recent_avg < overall_avg - 0.05:
                insights.append("Performance trend: DECLINING (recent average -5%)")
            else:
                insights.append("Performance trend: STABLE")

        if len(result.pass_rates) >= 5:
            std_dev = float(np.std(result.pass_rates))
            if std_dev > 0.1:
                insights.append(f"High volatility detected (std dev: {std_dev:.3f})")
            elif std_dev > 0.05:
                insights.append(f"Moderate volatility detected (std dev: {std_dev:.3f})")
            else:
                insights.append("Low volatility - performance is consistent")

        if result.anomaly_detection is not None:
            insights.extend(result.anomaly_detection.insights)

        if result.forecast is not None and result.forecast.predicted_values:
            avg_forecast = float(np.mean(result.forecast.predicted_values))
            insights.append(
                f"Forecasted average pass rate: {avg_forecast:.1%} over {result.forecast.horizon} runs"
            )
            low_forecasts = [p for p in result.forecast.predicted_values if p < 0.7]
            if low_forecasts:
                insights.append(
                    f"Warning: {len(low_forecasts)}/{len(result.forecast.predicted_values)} forecasted runs below threshold"
                )

        return insights
