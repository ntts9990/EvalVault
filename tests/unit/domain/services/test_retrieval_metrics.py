"""Retrieval metric utility tests."""

from __future__ import annotations

import pytest

from evalvault.domain.services.retrieval_metrics import compute_retrieval_metrics


def test_compute_retrieval_metrics_basic() -> None:
    retrieved = ["doc-1", "doc-2", "doc-3"]
    relevant = ["doc-2"]

    metrics = compute_retrieval_metrics(retrieved, relevant, recall_k=3, ndcg_k=3)

    assert metrics["precision_at_3"] == pytest.approx(1 / 3)
    assert metrics["recall_at_3"] == 1.0
    assert metrics["mrr"] == pytest.approx(0.5)
    assert metrics["ndcg_at_3"] == pytest.approx(1 / 1.5849625007, rel=1e-6)


def test_compute_retrieval_metrics_empty_relevance() -> None:
    metrics = compute_retrieval_metrics(["doc-1"], [], recall_k=5, ndcg_k=5)

    assert metrics["precision_at_5"] == 0.0
    assert metrics["recall_at_5"] == 0.0
    assert metrics["mrr"] == 0.0
    assert metrics["ndcg_at_5"] == 0.0
