"""Storage-facing helper for Experiment entities."""

from __future__ import annotations

from evalvault.domain.entities.experiment import Experiment, ExperimentGroup
from evalvault.ports.outbound.storage_port import StoragePort


class ExperimentRepository:
    """Experiment CRUD helper that wraps the configured StoragePort."""

    def __init__(self, storage: StoragePort):
        self._storage = storage

    def create(
        self,
        name: str,
        description: str = "",
        hypothesis: str = "",
        metrics: list[str] | None = None,
    ) -> Experiment:
        """Persist a freshly created experiment and return it."""
        experiment = Experiment(
            name=name,
            description=description,
            hypothesis=hypothesis,
            metrics_to_compare=metrics or [],
        )
        self._storage.save_experiment(experiment)
        return experiment

    def get(self, experiment_id: str) -> Experiment:
        """Load a single experiment by ID."""
        return self._storage.get_experiment(experiment_id)

    def list(self, status: str | None = None, limit: int = 100) -> list[Experiment]:
        """List experiments with optional status filtering."""
        return self._storage.list_experiments(status=status, limit=limit)

    def save(self, experiment: Experiment) -> None:
        """Persist modifications to an experiment."""
        self._storage.update_experiment(experiment)

    def add_group(
        self,
        experiment_id: str,
        group_name: str,
        description: str = "",
    ) -> ExperimentGroup:
        """Add a new group to an experiment and persist the change."""
        experiment = self.get(experiment_id)
        group = experiment.add_group(group_name, description)
        self.save(experiment)
        return group

    def add_run(self, experiment_id: str, group_name: str, run_id: str) -> None:
        """Attach a run to a group within the experiment."""
        experiment = self.get(experiment_id)
        experiment.add_run_to_group(group_name, run_id)
        self.save(experiment)

    def conclude(self, experiment_id: str, conclusion: str) -> Experiment:
        """Mark an experiment as completed with a conclusion."""
        experiment = self.get(experiment_id)
        experiment.status = "completed"
        experiment.conclusion = conclusion
        self.save(experiment)
        return experiment
