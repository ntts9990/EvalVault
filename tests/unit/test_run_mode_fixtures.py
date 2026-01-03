"""Fixture validation for run-mode regression datasets."""

from pathlib import Path

from evalvault.adapters.outbound.dataset import get_loader


def _load_dataset(path: Path):
    loader = get_loader(path)
    return loader.load(path)


def test_simple_mode_fixture_loads():
    """Simple mode fixture should load with required thresholds."""
    path = Path("tests/fixtures/e2e/run_mode_simple.json")
    dataset = _load_dataset(path)

    assert dataset.name == "run-mode-simple-smoke"
    assert dataset.thresholds["faithfulness"] == 0.7
    assert dataset.thresholds["answer_relevancy"] == 0.7
    assert len(dataset.test_cases) >= 2


def test_full_mode_fixture_loads_with_metadata():
    """Full mode fixture should load with domain metadata."""
    path = Path("tests/fixtures/e2e/run_mode_full_domain_memory.json")
    dataset = _load_dataset(path)

    assert dataset.metadata.get("domain") == "insurance"
    assert dataset.metadata.get("language") == "en"
    assert dataset.thresholds["context_precision"] == 0.6
    assert len(dataset.test_cases) >= 2
