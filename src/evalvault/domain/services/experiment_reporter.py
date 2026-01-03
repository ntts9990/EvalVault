"""Generate experiment reports that combine statistics and comparisons."""

from __future__ import annotations

from datetime import datetime

from evalvault.domain.entities.experiment import Experiment
from evalvault.domain.services.experiment_comparator import ExperimentComparator
from evalvault.domain.services.experiment_statistics import ExperimentStatisticsCalculator


class ExperimentReportGenerator:
    """Produces structured experiment reports for CLI/Web adapters."""

    def __init__(
        self,
        comparator: ExperimentComparator,
        statistics_calculator: ExperimentStatisticsCalculator,
    ):
        self._comparator = comparator
        self._statistics = statistics_calculator

    def generate(self, experiment: Experiment) -> dict:
        """Build a report that joins summary stats with metric comparisons."""
        summary = self._statistics.build_summary(experiment)
        comparisons = self._comparator.compare(experiment)

        return {
            "generated_at": datetime.now().isoformat(),
            "experiment": summary,
            "comparisons": [
                {
                    "metric_name": comp.metric_name,
                    "best_group": comp.best_group,
                    "improvement": comp.improvement,
                    "group_scores": comp.group_scores,
                }
                for comp in comparisons
            ],
        }
