"""Tests for phoenix_support helper utilities."""

from types import SimpleNamespace

from evalvault.config.phoenix_support import (
    PhoenixExperimentResolver,
    extract_phoenix_links,
    format_phoenix_links,
)


def test_extract_phoenix_links_returns_expected_mapping() -> None:
    metadata = {
        "phoenix": {
            "trace_url": " http://phoenix/traces/abc ",
            "experiment": {"url": "http://phoenix/experiments/exp-1"},
            "dataset": {"url": "http://phoenix/datasets/ds-1"},
            "embedding_export": {
                "cli": "uv run evalvault phoenix export-embeddings --dataset ds-1"
            },
        }
    }

    links = extract_phoenix_links(metadata)

    assert links["phoenix_trace_url"] == "http://phoenix/traces/abc"
    assert links["phoenix_experiment_url"] == "http://phoenix/experiments/exp-1"
    assert links["phoenix_dataset_url"] == "http://phoenix/datasets/ds-1"
    assert links["phoenix_embedding_export_cli"].startswith("uv run evalvault")


def test_format_phoenix_links_renders_markdown_and_slack() -> None:
    metadata = {
        "phoenix": {
            "trace_url": "http://phoenix/traces/abc",
            "experiment": {"url": "http://phoenix/experiments/exp-1"},
        }
    }

    markdown = format_phoenix_links(metadata, style="markdown")
    assert "[Phoenix Trace](http://phoenix/traces/abc)" in markdown

    slack = format_phoenix_links(metadata, style="slack")
    assert "<http://phoenix/traces/abc|Phoenix Trace>" in slack


def test_resolver_extracts_precision_and_drift_from_service() -> None:
    class DummyService:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str]] = []

        def get_experiment_summary(self, *, dataset_id: str, experiment_id: str) -> dict:
            self.calls.append((dataset_id, experiment_id))
            return {
                "metrics": {
                    "precision_at_k": {"value": 0.82},
                    "embedding_drift_score": 0.12,
                },
                "metadata": {},
            }

    settings = SimpleNamespace(
        phoenix_endpoint="http://localhost:6006/v1/traces",
        phoenix_api_token=None,
    )
    dummy_service = DummyService()
    resolver = PhoenixExperimentResolver(
        settings=settings,
        service_factory=lambda _settings: dummy_service,
    )

    metadata = {
        "phoenix": {
            "dataset": {"dataset_id": "ds_123", "url": "http://phoenix/datasets/ds_123"},
            "experiment": {
                "experiment_id": "exp_456",
                "url": "http://phoenix/experiments/exp_456",
            },
        }
    }

    stats = resolver.get_stats(metadata)

    assert stats is not None
    assert stats.precision_at_k == 0.82
    assert stats.drift_score == 0.12
    assert stats.experiment_url.endswith("exp_456")
    # Cached result avoids duplicate calls
    resolver.get_stats(metadata)
    assert len(dummy_service.calls) == 1
