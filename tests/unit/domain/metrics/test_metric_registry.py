"""Tests for metric registry."""

from evalvault.domain.metrics.registry import list_metric_names, list_metric_specs


def test_metric_registry_names_unique() -> None:
    names = list_metric_names()
    assert len(names) == len(set(names))


def test_metric_registry_contains_retrieval_metrics() -> None:
    names = list_metric_names()
    assert "mrr" in names
    assert "ndcg" in names
    assert "hit_rate" in names


def test_metric_registry_specs_have_required_fields() -> None:
    specs = list_metric_specs()
    assert specs
    for spec in specs:
        assert spec.name
        assert spec.description
        assert spec.signal_group
