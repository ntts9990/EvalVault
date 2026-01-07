"""Integration test for the summary evaluation minimal fixture."""

from pathlib import Path

from evalvault.adapters.outbound.dataset.json_loader import JSONDatasetLoader


def test_summary_eval_fixture_loads() -> None:
    fixture = Path(__file__).parent.parent / "fixtures" / "e2e" / "summary_eval_minimal.json"
    loader = JSONDatasetLoader()

    dataset = loader.load(fixture)

    assert dataset.name == "summary-eval-minimal"
    assert len(dataset.test_cases) == 8
    assert set(dataset.thresholds.keys()) == {
        "summary_faithfulness",
        "summary_score",
        "entity_preservation",
    }

    for test_case in dataset.test_cases:
        assert 2 <= len(test_case.contexts) <= 3
