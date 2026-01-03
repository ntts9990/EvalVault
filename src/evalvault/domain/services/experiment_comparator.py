"""Utilities for comparing experiment groups."""

from __future__ import annotations

from dataclasses import dataclass

from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.experiment import Experiment
from evalvault.ports.outbound.storage_port import StoragePort


@dataclass
class MetricComparison:
    """메트릭 비교 결과."""

    metric_name: str
    group_scores: dict[str, float]
    best_group: str
    improvement: float


class ExperimentComparator:
    """Aggregates EvaluationRun scores and highlights group deltas."""

    def __init__(self, storage: StoragePort):
        self._storage = storage

    def compare(self, experiment: Experiment) -> list[MetricComparison]:
        """Compare groups for the supplied experiment."""
        group_runs = self._collect_group_runs(experiment)
        if not any(group_runs.values()):
            return []

        metrics_to_compare = list(experiment.metrics_to_compare)
        if not metrics_to_compare:
            for runs in group_runs.values():
                if runs:
                    metrics_to_compare = list(runs[0].metrics_evaluated)
                    break

        if not metrics_to_compare:
            return []

        comparisons: list[MetricComparison] = []
        for metric in metrics_to_compare:
            group_scores: dict[str, float] = {}
            for group_name, runs in group_runs.items():
                scores = self._collect_metric_scores(runs, metric)
                if scores:
                    group_scores[group_name] = sum(scores) / len(scores)

            if not group_scores:
                continue

            best_group = max(group_scores, key=group_scores.get)  # type: ignore[arg-type]
            best_score = group_scores[best_group]
            worst_score = min(group_scores.values())
            improvement = (
                ((best_score - worst_score) / worst_score) * 100 if worst_score > 0 else 0.0
            )

            comparisons.append(
                MetricComparison(
                    metric_name=metric,
                    group_scores=group_scores,
                    best_group=best_group,
                    improvement=improvement,
                )
            )

        return comparisons

    def _collect_group_runs(self, experiment: Experiment) -> dict[str, list[EvaluationRun]]:
        """Load EvaluationRun instances for every group."""
        group_runs: dict[str, list[EvaluationRun]] = {}
        for group in experiment.groups:
            runs: list[EvaluationRun] = []
            for run_id in group.run_ids:
                try:
                    run = self._storage.get_run(run_id)
                except KeyError:
                    continue
                runs.append(run)
            group_runs[group.name] = runs
        return group_runs

    @staticmethod
    def _collect_metric_scores(runs: list[EvaluationRun], metric: str) -> list[float]:
        """Gather metric scores across runs, ignoring missing data."""
        scores: list[float] = []
        for run in runs:
            avg_score = run.get_avg_score(metric)
            if avg_score is not None:
                scores.append(avg_score)
        return scores


__all__ = ["ExperimentComparator", "MetricComparison"]
