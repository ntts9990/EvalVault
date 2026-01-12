"""Tests for analysis metric registry."""

from evalvault.domain.metrics.analysis_registry import (
    list_analysis_metric_keys,
    list_analysis_metric_specs,
)


def test_analysis_metric_registry_keys_unique() -> None:
    keys = list_analysis_metric_keys()
    assert len(keys) == len(set(keys))


def test_analysis_metric_registry_has_retrieval_specs() -> None:
    keys = list_analysis_metric_keys()
    assert "retrieval.avg_contexts" in keys


def test_analysis_metric_registry_specs_have_required_fields() -> None:
    specs = list_analysis_metric_specs()
    assert specs
    for spec in specs:
        assert spec.key
        assert spec.label
        assert spec.description
