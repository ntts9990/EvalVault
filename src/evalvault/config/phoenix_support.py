"""Helpers for enabling Phoenix instrumentation across CLI commands."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Literal

from rich.console import Console

from evalvault.config.instrumentation import (
    get_tracer_provider,
    is_instrumentation_enabled,
    setup_phoenix_instrumentation,
)
from evalvault.config.settings import Settings


def ensure_phoenix_instrumentation(
    settings: Settings,
    *,
    console: Console | None = None,
    force: bool = False,
) -> bool:
    """Enable Phoenix instrumentation based on settings or explicit request.

    Args:
        settings: Runtime settings populated from environment/profile.
        console: Optional Rich console for user feedback.
        force: Force-enable instrumentation regardless of settings.phoenix_enabled.

    Returns:
        True if instrumentation is active (or already enabled), False otherwise.
    """

    raw_flag = getattr(settings, "phoenix_enabled", False)
    config_flag = raw_flag if isinstance(raw_flag, bool) else False
    should_enable = force or config_flag
    if not should_enable:
        return False
    if is_instrumentation_enabled():
        return True

    endpoint = getattr(settings, "phoenix_endpoint", "http://localhost:6006/v1/traces")
    if not isinstance(endpoint, str) or not endpoint:
        endpoint = "http://localhost:6006/v1/traces"

    sample_rate = getattr(settings, "phoenix_sample_rate", 1.0)
    if not isinstance(sample_rate, int | float):
        sample_rate = 1.0

    api_token = getattr(settings, "phoenix_api_token", None)
    if api_token is not None and not isinstance(api_token, str):
        api_token = None

    headers: dict[str, str] | None = None
    if api_token:
        headers = {"api-key": api_token}

    project_name = getattr(settings, "phoenix_project_name", None)
    if project_name is not None and not isinstance(project_name, str):
        project_name = None

    try:
        setup_phoenix_instrumentation(
            endpoint=endpoint,
            service_name="evalvault",
            project_name=project_name,
            sample_rate=sample_rate,
            headers=headers,
        )
        if console:
            console.print(f"[dim]Phoenix instrumentation enabled (endpoint: {endpoint}).[/dim]")
        return True
    except ImportError:
        if console:
            console.print(
                "[yellow]Warning:[/yellow] Phoenix instrumentation dependencies missing. "
                "Install with: uv sync --extra phoenix"
            )
        return False
    except Exception as exc:  # pragma: no cover - diagnostics for CLI
        if console:
            console.print(
                f"[yellow]Warning:[/yellow] Failed to initialize Phoenix instrumentation: {exc}"
            )
        return False


def extract_phoenix_links(metadata: dict[str, Any] | None) -> dict[str, str]:
    """Extract canonical Phoenix links/commands from tracker metadata."""

    if not metadata:
        return {}
    phoenix_meta = metadata.get("phoenix")
    if not isinstance(phoenix_meta, dict):
        return {}

    def _as_str(value: Any) -> str | None:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
        return None

    links: OrderedDict[str, str] = OrderedDict()
    trace_url = _as_str(phoenix_meta.get("trace_url"))
    if trace_url:
        links["phoenix_trace_url"] = trace_url

    experiment_meta = phoenix_meta.get("experiment")
    if isinstance(experiment_meta, dict):
        experiment_url = _as_str(experiment_meta.get("url"))
        if experiment_url:
            links["phoenix_experiment_url"] = experiment_url

    dataset_meta = phoenix_meta.get("dataset")
    if isinstance(dataset_meta, dict):
        dataset_url = _as_str(dataset_meta.get("url"))
        if dataset_url:
            links["phoenix_dataset_url"] = dataset_url

    embedding_meta = phoenix_meta.get("embedding_export")
    if isinstance(embedding_meta, dict):
        cli_cmd = _as_str(embedding_meta.get("cli"))
        if cli_cmd:
            links["phoenix_embedding_export_cli"] = cli_cmd

    return dict(links)


def get_phoenix_trace_url(metadata: dict[str, Any] | None) -> str | None:
    """Extract Phoenix trace URL from tracker metadata."""

    links = extract_phoenix_links(metadata)
    return links.get("phoenix_trace_url")


_LINK_LABELS = {
    "phoenix_trace_url": "Trace",
    "phoenix_experiment_url": "Experiment",
    "phoenix_dataset_url": "Dataset",
    "phoenix_embedding_export_cli": "Embedding Export CLI",
}


def format_phoenix_links(
    metadata: dict[str, Any] | None,
    *,
    style: Literal["markdown", "plain", "slack"] = "markdown",
) -> str:
    """Format Phoenix links for human-friendly surfaces (README, Slack, etc.)."""

    links = extract_phoenix_links(metadata)
    if not links:
        return ""

    bullets: list[str] = []
    for key in ("phoenix_trace_url", "phoenix_experiment_url", "phoenix_dataset_url"):
        url = links.get(key)
        if not url:
            continue
        label = _LINK_LABELS.get(key, key)
        if style == "markdown":
            bullets.append(f"- [Phoenix {label}]({url})")
        elif style == "slack":
            bullets.append(f"• <{url}|Phoenix {label}>")
        else:
            bullets.append(f"- Phoenix {label}: {url}")

    cli_cmd = links.get("phoenix_embedding_export_cli")
    if cli_cmd:
        if style == "markdown":
            bullets.append("")
            bullets.append("```bash")
            bullets.append(cli_cmd)
            bullets.append("```")
        elif style == "slack":
            bullets.append(f"• Embedding Export CLI: `{cli_cmd}`")
        else:
            bullets.append(f"- Embedding Export CLI: {cli_cmd}")

    return "\n".join(bullets).strip()


def _coerce_numeric(value: Any) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    if isinstance(value, dict):
        for key in ("value", "score", "mean", "avg", "average"):
            if key in value:
                coerced = _coerce_numeric(value[key])
                if coerced is not None:
                    return coerced
    return None


def _extract_metric_value(container: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key not in container:
            continue
        value = _coerce_numeric(container[key])
        if value is not None:
            return value
    return None


@dataclass
class PhoenixExperimentStats:
    """Summarized Phoenix experiment metrics."""

    precision_at_k: float | None = None
    drift_score: float | None = None
    experiment_url: str | None = None
    dataset_url: str | None = None
    raw_metrics: dict[str, Any] = field(default_factory=dict)
    raw_metadata: dict[str, Any] = field(default_factory=dict)


class PhoenixExperimentResolver:
    """Fetch and cache Phoenix experiment metrics for downstream surfaces."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        service_factory: Callable[[Settings], Any] | None = None,
    ) -> None:
        self._settings = settings
        self._service_factory = service_factory
        self._service: Any | None = None
        self._cache: dict[tuple[str, str], dict[str, Any] | None] = {}
        self._checked_service = False

    def _ensure_settings(self) -> Settings | None:
        if self._settings is not None:
            return self._settings
        try:
            self._settings = Settings()
        except Exception:
            self._settings = None
        return self._settings

    def _ensure_service(self) -> Any | None:
        if self._service is not None:
            return self._service
        if self._checked_service:
            return None

        settings = self._ensure_settings()
        if settings is None:
            self._checked_service = True
            return None

        endpoint = getattr(settings, "phoenix_endpoint", None)
        if not isinstance(endpoint, str) or not endpoint:
            self._checked_service = True
            return None

        service: Any | None = None
        if self._service_factory:
            service = self._service_factory(settings)
        else:  # pragma: no cover - real service instantiation
            from evalvault.adapters.outbound.phoenix.sync_service import (
                PhoenixSyncError,
                PhoenixSyncService,
            )

            api_token = getattr(settings, "phoenix_api_token", None)
            try:
                service = PhoenixSyncService(endpoint=endpoint, api_token=api_token)
            except PhoenixSyncError:
                service = None

        self._checked_service = True
        self._service = service
        return self._service

    @property
    def is_available(self) -> bool:
        """Whether Phoenix client/service is ready."""

        return self._ensure_service() is not None

    def can_resolve(self, metadata: dict[str, Any] | None) -> bool:
        """Check whether tracker metadata contains Phoenix IDs."""

        dataset_id, experiment_id = self._extract_ids(metadata)
        return bool(dataset_id and experiment_id)

    def get_stats(self, metadata: dict[str, Any] | None) -> PhoenixExperimentStats | None:
        """Fetch Phoenix experiment metrics for the given tracker metadata."""

        dataset_id, experiment_id = self._extract_ids(metadata)
        if not dataset_id or not experiment_id:
            return None

        summary = self._fetch_summary(dataset_id, experiment_id)
        if not summary:
            return None

        metrics = summary.get("metrics") or {}
        meta = summary.get("metadata") or {}

        precision = _extract_metric_value(
            metrics,
            ("retrieval_precision_at_k", "precision_at_k", "precision"),
        )
        drift = _extract_metric_value(
            metrics,
            ("embedding_drift_score", "query_drift", "drift_score"),
        )
        if drift is None:
            drift = _extract_metric_value(
                meta,
                ("embedding_drift_score", "query_drift", "drift_score"),
            )

        links = extract_phoenix_links(metadata)

        return PhoenixExperimentStats(
            precision_at_k=precision,
            drift_score=drift,
            experiment_url=links.get("phoenix_experiment_url"),
            dataset_url=links.get("phoenix_dataset_url"),
            raw_metrics=metrics,
            raw_metadata=meta,
        )

    def _fetch_summary(self, dataset_id: str, experiment_id: str) -> dict[str, Any] | None:
        key = (dataset_id, experiment_id)
        if key in self._cache:
            return self._cache[key]

        service = self._ensure_service()
        if service is None:
            self._cache[key] = None
            return None

        try:
            summary = service.get_experiment_summary(
                dataset_id=dataset_id,
                experiment_id=experiment_id,
            )
        except Exception:  # pragma: no cover - network errors
            summary = None

        self._cache[key] = summary
        return summary

    @staticmethod
    def _extract_ids(metadata: dict[str, Any] | None) -> tuple[str | None, str | None]:
        if not metadata:
            return None, None
        phoenix_meta = metadata.get("phoenix")
        if not isinstance(phoenix_meta, dict):
            return None, None

        dataset_meta = phoenix_meta.get("dataset") or {}
        experiment_meta = phoenix_meta.get("experiment") or {}

        dataset_id = dataset_meta.get("dataset_id") or phoenix_meta.get("dataset_id")
        experiment_id = experiment_meta.get("experiment_id") or phoenix_meta.get("experiment_id")
        return dataset_id, experiment_id


def _normalize_attribute_value(value: Any) -> str | int | float | bool:
    if isinstance(value, str | int | float | bool):
        return value
    return str(value)


def _get_tracer():
    if not is_instrumentation_enabled():
        return None
    try:
        from opentelemetry import trace
    except ImportError:
        return None
    provider = get_tracer_provider()
    if provider is None:
        return None
    return trace.get_tracer("evalvault")


@contextmanager
def instrumentation_span(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> Iterator[Any]:
    """Start a Phoenix/OpenTelemetry span when instrumentation is enabled."""

    tracer = _get_tracer()
    if tracer is None:
        yield None
        return

    with tracer.start_as_current_span(name) as span:
        if attributes:
            set_span_attributes(span, attributes)
        yield span


def set_span_attributes(span: Any, attributes: dict[str, Any]) -> None:
    """Safely attach attributes to a span if instrumentation is active."""

    if span is None or not attributes:
        return

    for key, value in attributes.items():
        if value is None:
            continue
        try:
            span.set_attribute(key, _normalize_attribute_value(value))
        except Exception:  # pragma: no cover - defensive
            continue


__all__ = [
    "ensure_phoenix_instrumentation",
    "extract_phoenix_links",
    "format_phoenix_links",
    "get_phoenix_trace_url",
    "instrumentation_span",
    "PhoenixExperimentResolver",
    "PhoenixExperimentStats",
    "set_span_attributes",
]
