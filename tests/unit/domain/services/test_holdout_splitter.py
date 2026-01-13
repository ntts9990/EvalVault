from evalvault.domain.entities import Dataset, TestCase
from evalvault.domain.services.holdout_splitter import split_dataset_holdout


def _build_dataset(count: int) -> Dataset:
    return Dataset(
        name="sample",
        version="1",
        test_cases=[
            TestCase(
                id=f"tc-{idx}",
                question=f"Q{idx}",
                answer=f"A{idx}",
                contexts=[f"C{idx}"],
            )
            for idx in range(count)
        ],
        thresholds={"faithfulness": 0.7},
    )


def test_split_dataset_holdout_sizes():
    dataset = _build_dataset(10)

    dev, holdout = split_dataset_holdout(dataset=dataset, holdout_ratio=0.2, seed=42)

    assert len(dev.test_cases) == 8
    assert len(holdout.test_cases) == 2
    assert dev.metadata["split"] == "dev"
    assert holdout.metadata["split"] == "holdout"
    assert dev.metadata["holdout_ratio"] == 0.2
    assert holdout.metadata["holdout_ratio"] == 0.2
    assert dev.metadata["split_seed"] == 42
    assert holdout.metadata["split_seed"] == 42


def test_split_dataset_holdout_deterministic():
    dataset = _build_dataset(12)

    dev_a, holdout_a = split_dataset_holdout(dataset=dataset, holdout_ratio=0.25, seed=7)
    dev_b, holdout_b = split_dataset_holdout(dataset=dataset, holdout_ratio=0.25, seed=7)

    assert [case.id for case in dev_a.test_cases] == [case.id for case in dev_b.test_cases]
    assert [case.id for case in holdout_a.test_cases] == [case.id for case in holdout_b.test_cases]


def test_split_dataset_holdout_zero_ratio():
    dataset = _build_dataset(5)

    dev, holdout = split_dataset_holdout(dataset=dataset, holdout_ratio=0.0, seed=1)

    assert len(holdout.test_cases) == 0
    assert len(dev.test_cases) == 5
