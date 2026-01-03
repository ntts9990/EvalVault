"""Summary helpers for experiments."""

from __future__ import annotations

from evalvault.domain.entities.experiment import Experiment


class ExperimentStatisticsCalculator:
    """Builds summary dictionaries for consumption by adapters."""

    def build_summary(self, experiment: Experiment) -> dict:
        """Return a serializable summary for the experiment."""
        groups_summary = {
            group.name: {
                "description": group.description,
                "num_runs": len(group.run_ids),
                "run_ids": list(group.run_ids),
            }
            for group in experiment.groups
        }

        return {
            "experiment_id": experiment.experiment_id,
            "name": experiment.name,
            "description": experiment.description,
            "hypothesis": experiment.hypothesis,
            "status": experiment.status,
            "created_at": experiment.created_at.isoformat(),
            "metrics_to_compare": list(experiment.metrics_to_compare),
            "groups": groups_summary,
            "conclusion": experiment.conclusion,
        }
