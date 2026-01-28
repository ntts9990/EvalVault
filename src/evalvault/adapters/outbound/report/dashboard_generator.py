from __future__ import annotations

import contextlib
import json
import os
import random
import sys
from importlib import import_module
from pathlib import Path
from typing import Any


def _import_matplotlib_pyplot() -> Any:
    try:
        if "matplotlib.pyplot" in sys.modules:
            return import_module("matplotlib.pyplot")
        os.environ.setdefault("MPLBACKEND", "Agg")
        matplotlib = import_module("matplotlib")
        with contextlib.suppress(Exception):
            matplotlib.use("Agg", force=True)
        return import_module("matplotlib.pyplot")
    except ModuleNotFoundError as exc:
        raise ImportError(
            "matplotlib is required for dashboard generation. Install with: uv sync --extra dashboard"
        ) from exc


class DashboardGenerator:
    def __init__(self, style: str = "seaborn-v0_8-darkgrid") -> None:
        plt = _import_matplotlib_pyplot()

        try:
            plt.style.use(style)
        except Exception:
            plt.style.use("default")

        plt.rcParams["figure.figsize"] = (14, 10)
        plt.rcParams["font.size"] = 10
        plt.rcParams["axes.labelsize"] = 11
        plt.rcParams["axes.titlesize"] = 12
        plt.rcParams["legend.fontsize"] = 10

    def generate_evaluation_dashboard(
        self,
        run_id: str,
        analysis_json_path: str | None = None,
        analysis_data: dict[str, Any] | None = None,
    ) -> Any:
        plt = _import_matplotlib_pyplot()

        analysis_payload: dict[str, Any] = {}
        if analysis_data is None:
            if analysis_json_path and Path(analysis_json_path).exists():
                with open(analysis_json_path, encoding="utf-8") as f:
                    analysis_payload = json.load(f)
        elif isinstance(analysis_data, dict):
            analysis_payload = analysis_data

        fig, axes = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
        fig.suptitle(
            f"Evaluation Dashboard: {run_id[:8]}...",
            fontsize=16,
            fontweight="bold",
        )

        self._plot_metric_distribution(axes[0, 0], analysis_payload)
        self._plot_correlation_heatmap(axes[0, 1], analysis_payload)
        self._plot_pass_rates(axes[1, 0], analysis_payload)
        self._plot_failure_causes(axes[1, 1], analysis_payload)

        return fig

    def _plot_metric_distribution(self, ax: Any, analysis_data: dict[str, Any]) -> None:
        ax.set_title("Metric Score Distribution", fontweight="bold")

        metrics_summary = analysis_data.get("metrics_summary") if analysis_data else None
        if not isinstance(metrics_summary, dict) or not metrics_summary:
            metrics = ["faithfulness", "answer_relevancy", "context_precision"]
            data = [[_clamp01(random.gauss(0.7, 0.15)) for _ in range(50)] for _ in metrics]
            ax.boxplot(data, labels=metrics)
            ax.axhline(y=0.7, color="r", linestyle="--", label="Threshold")
            ax.set_ylabel("Score")
            ax.legend(loc="lower left")
            return

        metrics = list(metrics_summary.keys())
        data = []
        for metric in metrics:
            stats = metrics_summary.get(metric, {})
            if not isinstance(stats, dict):
                stats = {}
            mean = float(stats.get("mean", 0.7))
            std = float(stats.get("std", 0.15))
            samples = [_clamp01(random.gauss(mean, std)) for _ in range(30)]
            data.append(samples)

        ax.boxplot(data, labels=metrics)
        ax.axhline(y=0.7, color="r", linestyle="--", label="Threshold")
        ax.set_ylabel("Score")
        ax.legend(loc="lower left")

    def _plot_correlation_heatmap(self, ax: Any, analysis_data: dict[str, Any]) -> None:
        plt = _import_matplotlib_pyplot()

        ax.set_title("Metric Correlation Heatmap", fontweight="bold")

        correlation_matrix = analysis_data.get("correlation_matrix") if analysis_data else None
        correlation_metrics = analysis_data.get("correlation_metrics") if analysis_data else None

        if not correlation_matrix or not correlation_metrics:
            metrics = ["faithfulness", "answer_relevancy", "context_precision"]
            corr = [
                [1.0, 0.75, 0.82],
                [0.75, 1.0, 0.68],
                [0.82, 0.68, 1.0],
            ]
            im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
            ax.set_xticks(range(len(metrics)))
            ax.set_yticks(range(len(metrics)))
            ax.set_xticklabels(metrics, rotation=45, ha="right")
            ax.set_yticklabels(metrics)
            plt.colorbar(im, ax=ax)
            return

        im = ax.imshow(correlation_matrix, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_xticks(range(len(correlation_metrics)))
        ax.set_yticks(range(len(correlation_metrics)))
        ax.set_xticklabels(correlation_metrics, rotation=45, ha="right")
        ax.set_yticklabels(correlation_metrics)
        plt.colorbar(im, ax=ax, label="Correlation Coefficient")

    def _plot_pass_rates(self, ax: Any, analysis_data: dict[str, Any]) -> None:
        ax.set_title("Pass Rate by Metric", fontweight="bold")

        metric_pass_rates = analysis_data.get("metric_pass_rates") if analysis_data else None
        if not isinstance(metric_pass_rates, dict) or not metric_pass_rates:
            metrics = ["faithfulness", "answer_relevancy", "context_precision"]
            pass_rates = [0.85, 0.45, 0.78]
            colors = ["green" if rate >= 0.7 else "red" for rate in pass_rates]
            ax.bar(metrics, pass_rates, color=colors, alpha=0.7)
            ax.axhline(y=0.7, color="r", linestyle="--", label="Threshold")
            ax.set_ylabel("Pass Rate")
            ax.set_ylim(0, 1.0)
            ax.legend(loc="lower right")
            return

        metrics = list(metric_pass_rates.keys())
        pass_rates = [float(v) for v in metric_pass_rates.values()]
        colors = ["green" if rate >= 0.7 else "red" for rate in pass_rates]

        ax.bar(metrics, pass_rates, color=colors, alpha=0.7)
        ax.axhline(y=0.7, color="r", linestyle="--", label="Threshold")
        ax.set_ylabel("Pass Rate")
        ax.set_ylim(0, 1.0)
        ax.legend(loc="lower right")

    def _plot_failure_causes(self, ax: Any, analysis_data: dict[str, Any]) -> None:
        ax.set_title("Failure Cause Distribution", fontweight="bold")

        low_performers = analysis_data.get("low_performers") if analysis_data else None
        if not low_performers:
            causes = {
                "Low Context Recall": 35,
                "Hallucination": 25,
                "Irrelevant Answer": 20,
                "Missing Information": 20,
            }
            labels = list(causes.keys())
            sizes = list(causes.values())
            ax.pie(
                sizes,
                labels=labels,
                autopct="%1.1f%%",
                startangle=90,
                colors=["#ff9999", "#66b3ff", "#99ff99", "#ffcc99"],
            )
            return

        cause_counts = {"Low Context Recall": 0, "Hallucination": 0, "Other": 0}
        for low_perf in low_performers:
            if not isinstance(low_perf, dict):
                continue
            causes = low_perf.get("potential_causes", [])
            if not isinstance(causes, list):
                continue
            for cause in causes:
                cause_str = str(cause).lower()
                if "context" in cause_str or "recall" in cause_str:
                    cause_counts["Low Context Recall"] += 1
                elif "hallucination" in cause_str or "fact" in cause_str:
                    cause_counts["Hallucination"] += 1
                else:
                    cause_counts["Other"] += 1

        cause_counts = {k: v for k, v in cause_counts.items() if v > 0}
        if not cause_counts:
            ax.text(0.5, 0.5, "No failure cause data", ha="center", va="center")
            return

        labels = list(cause_counts.keys())
        sizes = list(cause_counts.values())
        ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            colors=["#ff9999", "#66b3ff", "#99ff99", "#ffcc99"],
        )


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
