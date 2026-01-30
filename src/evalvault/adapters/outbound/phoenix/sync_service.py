"""Phoenix dataset / experiment synchronization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from evalvault.domain.entities import Dataset, EvaluationRun, TestCase


class PhoenixSyncError(RuntimeError):
    """Raised when Phoenix synchronization fails."""


def _normalize_base_url(endpoint: str) -> str:
    """Convert OTLP endpoint (…/v1/traces) to Phoenix REST base URL."""

    if not endpoint:
        return "http://localhost:6006"
    base = endpoint.strip()
    suffix = "/v1/traces"
    if base.endswith(suffix):
        base = base[: -len(suffix)]
    return base.rstrip("/") or "http://localhost:6006"


def _as_serializable(value: Any) -> Any:
    """Best-effort conversion to JSON-serializable structures."""

    if isinstance(value, str | int | float | bool) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _as_serializable(v) for k, v in value.items()}
    if isinstance(value, list | tuple | set):
        return [_as_serializable(v) for v in value]
    return str(value)


@dataclass
class PhoenixDatasetInfo:
    dataset_id: str
    dataset_name: str
    dataset_version_id: str
    url: str
    description: str | None = None
    example_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_name": self.dataset_name,
            "dataset_version_id": self.dataset_version_id,
            "url": self.url,
            "description": self.description,
            "example_count": self.example_count,
        }


@dataclass
class PhoenixExperimentInfo:
    experiment_id: str
    dataset_id: str
    url: str
    dataset_url: str
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "dataset_id": self.dataset_id,
            "url": self.url,
            "dataset_url": self.dataset_url,
            "description": self.description,
        }


class PhoenixSyncService:
    """Wraps `phoenix.client.Client` to push datasets/experiments."""

    def __init__(self, *, endpoint: str, api_token: str | None = None):
        try:
            from phoenix.client import Client
        except ImportError as exc:  # pragma: no cover - requires optional extra
            raise PhoenixSyncError(
                "Phoenix client not installed. Install with: uv sync --extra phoenix"
            ) from exc

        base_url = _normalize_base_url(endpoint)
        self._client = Client(base_url=base_url, api_key=api_token or None)

    def upload_dataset(
        self,
        *,
        dataset: Dataset,
        dataset_name: str,
        description: str | None = None,
    ) -> PhoenixDatasetInfo:
        """Upload the EvalVault dataset as a Phoenix dataset."""

        try:
            phoenix_dataset = self._client.datasets.create_dataset(
                name=dataset_name,
                examples=self._build_examples(dataset),
                dataset_description=description,
            )
        except Exception as exc:  # pragma: no cover - HTTP/serialization errors
            message = str(exc)
            if "already exists" in message:
                existing = self._find_dataset_by_name(dataset_name)
                if existing:
                    dataset_obj = self._client.datasets.get_dataset(dataset=existing["id"])
                    dataset_url = self._client.experiments.get_dataset_experiments_url(
                        dataset_obj.id
                    )
                    return PhoenixDatasetInfo(
                        dataset_id=dataset_obj.id,
                        dataset_name=dataset_obj.name,
                        dataset_version_id=dataset_obj.version_id,
                        url=dataset_url,
                        description=description,
                        example_count=getattr(dataset_obj, "examples", None),
                    )
            raise PhoenixSyncError(f"Dataset upload failed: {exc}") from exc

        dataset_url = self._client.experiments.get_dataset_experiments_url(phoenix_dataset.id)

        return PhoenixDatasetInfo(
            dataset_id=phoenix_dataset.id,
            dataset_name=phoenix_dataset.name,
            dataset_version_id=phoenix_dataset.version_id,
            url=dataset_url,
            description=description,
            example_count=len(dataset),
        )

    def create_experiment_record(
        self,
        *,
        dataset_info: PhoenixDatasetInfo,
        experiment_name: str,
        description: str | None,
        metadata: dict[str, Any],
        repetitions: int = 1,
    ) -> PhoenixExperimentInfo:
        """Create a Phoenix experiment entry tied to an uploaded dataset."""

        try:
            experiment = self._client.experiments.create(
                dataset_id=dataset_info.dataset_id,
                dataset_version_id=dataset_info.dataset_version_id,
                experiment_name=experiment_name,
                experiment_description=description,
                experiment_metadata=_as_serializable(metadata),
                repetitions=repetitions,
            )
        except Exception as exc:  # pragma: no cover - HTTP errors
            raise PhoenixSyncError(f"Experiment creation failed: {exc}") from exc

        dataset_url = self._client.experiments.get_dataset_experiments_url(dataset_info.dataset_id)
        experiment_url = self._client.experiments.get_experiment_url(
            dataset_id=dataset_info.dataset_id,
            experiment_id=experiment["id"],
        )

        return PhoenixExperimentInfo(
            experiment_id=experiment["id"],
            dataset_id=dataset_info.dataset_id,
            url=experiment_url,
            dataset_url=dataset_url,
            description=description,
        )

    def _build_examples(self, dataset: Dataset) -> list[dict[str, Any]]:
        """Convert EvalVault dataset to Phoenix dataset examples."""

        shared_metadata = _as_serializable(dataset.metadata)
        examples: list[dict[str, Any]] = []
        for test_case in dataset.test_cases:
            examples.append(
                {
                    "input": self._build_input_payload(test_case),
                    "output": self._build_output_payload(test_case),
                    "metadata": self._build_example_metadata(
                        dataset=dataset,
                        test_case=test_case,
                        shared_metadata=shared_metadata,
                    ),
                }
            )
        return examples

    def _find_dataset_by_name(self, dataset_name: str) -> dict[str, Any] | None:
        try:
            datasets = self._client.datasets.list()
        except Exception:
            return None
        for entry in datasets:
            if entry.get("name") == dataset_name:
                return entry
        return None

    def sync_prompts(
        self,
        *,
        prompt_entries: list[dict[str, Any]],
        model_name: str,
        model_provider: str,
        prompt_set_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Create prompt versions in Phoenix Prompt Management."""

        if not prompt_entries:
            return []

        try:
            from phoenix.client.resources.prompts import PromptVersion
        except Exception as exc:  # pragma: no cover - optional dependency
            raise PhoenixSyncError("Phoenix prompt client unavailable") from exc

        synced: list[dict[str, Any]] = []
        for index, entry in enumerate(prompt_entries, start=1):
            name = entry.get("name") or entry.get("role") or f"prompt_{index}"
            content = entry.get("content") or entry.get("content_preview") or ""
            if not content:
                continue
            prompt_version = PromptVersion(
                [{"role": "system", "content": content}],
                model_name=model_name,
                model_provider=model_provider,
                template_format="NONE",
            )
            prompt_metadata = {
                "kind": entry.get("kind"),
                "role": entry.get("role"),
                "checksum": entry.get("checksum"),
                "status": entry.get("status"),
                "source": entry.get("source") or entry.get("path"),
                "order": index,
            }
            if prompt_set_name:
                prompt_metadata["prompt_set"] = prompt_set_name
            try:
                version = self._client.prompts.create(
                    version=prompt_version,
                    name=name,
                    prompt_description=entry.get("notes"),
                    prompt_metadata=_as_serializable(prompt_metadata),
                )
                synced.append(
                    {
                        **entry,
                        "phoenix_prompt_version_id": getattr(version, "id", None),
                    }
                )
            except Exception as exc:  # pragma: no cover - HTTP errors
                raise PhoenixSyncError(f"Prompt sync failed: {exc}") from exc

        return synced

    def _build_input_payload(self, test_case: TestCase) -> dict[str, Any]:
        return {
            "question": test_case.question,
            "contexts": list(test_case.contexts),
        }

    def _build_output_payload(self, test_case: TestCase) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "answer": test_case.answer,
        }
        if test_case.ground_truth:
            payload["reference"] = test_case.ground_truth
        return payload

    def _build_example_metadata(
        self,
        *,
        dataset: Dataset,
        test_case: TestCase,
        shared_metadata: Any,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "test_case_id": test_case.id,
            "dataset_name": dataset.name,
            "dataset_version": dataset.version,
        }
        if shared_metadata:
            metadata["dataset_metadata"] = shared_metadata
        if dataset.thresholds:
            metadata["thresholds"] = _as_serializable(dataset.thresholds)
        if test_case.metadata:
            metadata["test_case_metadata"] = _as_serializable(test_case.metadata)
        return metadata

    def get_experiment_summary(
        self,
        *,
        dataset_id: str,
        experiment_id: str,
    ) -> dict[str, Any]:
        """Fetch experiment summary/metrics from Phoenix."""

        try:
            experiment = self._client.experiments.get_experiment(
                dataset_id=dataset_id,
                experiment_id=experiment_id,
            )
        except Exception as exc:  # pragma: no cover - HTTP errors
            raise PhoenixSyncError(f"Experiment fetch failed: {exc}") from exc

        return {
            "experiment_id": experiment.get("id") or experiment_id,
            "dataset_id": dataset_id,
            "metrics": experiment.get("metrics") or {},
            "metadata": experiment.get("metadata") or {},
            "updated_at": experiment.get("updated_at"),
        }


def build_experiment_metadata(
    *,
    run: EvaluationRun,
    dataset: Dataset,
    reliability_snapshot: dict[str, float] | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a Phoenix-friendly metadata payload summarizing EvalVault run."""

    metrics: dict[str, Any] = {}
    for metric_name in run.metrics_evaluated:
        avg_score = run.get_avg_score(metric_name)
        metrics[metric_name] = {
            "average_score": avg_score,
            "threshold": run.thresholds.get(metric_name, 0.7),
        }

    payload: dict[str, Any] = {
        "run_id": run.run_id,
        "model_name": run.model_name,
        "dataset_name": dataset.name,
        "dataset_version": dataset.version,
        "pass_rate": run.pass_rate,
        "total_test_cases": run.total_test_cases,
        "metrics": metrics,
    }
    if run.results:
        latencies = [r.latency_ms for r in run.results if r.latency_ms]
        tokens = [r.tokens_used for r in run.results if r.tokens_used]
        costs = [r.cost_usd for r in run.results if r.cost_usd is not None]
        if latencies:
            payload["avg_latency_ms"] = round(sum(latencies) / len(latencies), 2)
        if tokens:
            payload["avg_tokens"] = round(sum(tokens) / len(tokens), 2)
        if costs:
            payload["avg_cost_usd"] = round(sum(costs) / len(costs), 6)
    if run.total_tokens:
        payload["total_tokens"] = run.total_tokens
    if run.total_cost_usd is not None:
        payload["total_cost_usd"] = run.total_cost_usd
    payload["error_rate"] = round(1 - run.pass_rate, 4)
    if reliability_snapshot:
        payload["reliability_snapshot"] = reliability_snapshot
    if dataset.metadata:
        payload["dataset_metadata"] = _as_serializable(dataset.metadata)
    if extra:
        payload.update(_as_serializable(extra))
    return payload


__all__ = [
    "PhoenixDatasetInfo",
    "PhoenixExperimentInfo",
    "PhoenixSyncError",
    "PhoenixSyncService",
    "build_experiment_metadata",
]
