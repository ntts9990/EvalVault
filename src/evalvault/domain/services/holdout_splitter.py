from __future__ import annotations

import random

from evalvault.domain.entities import Dataset, TestCase


def split_dataset_holdout(
    *,
    dataset: Dataset,
    holdout_ratio: float,
    seed: int | None,
) -> tuple[Dataset, Dataset]:
    if holdout_ratio < 0 or holdout_ratio >= 1:
        raise ValueError("holdout_ratio must be in [0, 1).")

    total = len(dataset.test_cases)
    if total == 0:
        return _clone_dataset(dataset, "dev", []), _clone_dataset(dataset, "holdout", [])

    holdout_size = int(total * holdout_ratio)
    if holdout_ratio > 0 and holdout_size == 0:
        holdout_size = 1
    if holdout_size >= total:
        holdout_size = total - 1

    rng = random.Random(seed)
    indices = list(range(total))
    rng.shuffle(indices)

    holdout_indices = set(indices[:holdout_size])
    dev_cases: list[TestCase] = []
    holdout_cases: list[TestCase] = []

    for idx, test_case in enumerate(dataset.test_cases):
        if idx in holdout_indices:
            holdout_cases.append(test_case)
        else:
            dev_cases.append(test_case)

    return (
        _clone_dataset(dataset, "dev", dev_cases, holdout_ratio, seed),
        _clone_dataset(dataset, "holdout", holdout_cases, holdout_ratio, seed),
    )


def _clone_dataset(
    dataset: Dataset,
    split: str,
    test_cases: list[TestCase],
    holdout_ratio: float | None = None,
    seed: int | None = None,
) -> Dataset:
    metadata = dict(dataset.metadata or {})
    metadata["split"] = split
    if holdout_ratio is not None:
        metadata.setdefault("holdout_ratio", holdout_ratio)
    if seed is not None:
        metadata.setdefault("split_seed", seed)
    return Dataset(
        name=dataset.name,
        version=dataset.version,
        test_cases=list(test_cases),
        metadata=metadata,
        source_file=dataset.source_file,
        thresholds=dict(dataset.thresholds),
    )
