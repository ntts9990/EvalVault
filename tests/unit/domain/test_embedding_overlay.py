"""Tests for embedding overlay helpers."""

from evalvault.domain.services.embedding_overlay import build_cluster_facts


def test_build_cluster_facts_groups_clusters_and_limits_text() -> None:
    rows = [
        {
            "cluster_id": 1,
            "question": "보험료는 어떻게 계산되나요?",
            "contexts": "보험료=기본료+특약",
            "umap_x": 0.2,
            "umap_y": 0.5,
            "example_id": "ex-1",
        },
        {
            "cluster_id": 1,
            "question": "연납 보험료 산식은?",
            "contexts": "연납=월납*12",
            "umap_x": 0.25,
            "umap_y": 0.45,
            "example_id": "ex-2",
        },
        {
            "cluster_id": 2,
            "question": "청구 기한은?",
            "contexts": "30일",
            "umap_x": -0.1,
            "umap_y": -0.3,
            "example_id": "ex-3",
        },
    ]

    facts = build_cluster_facts(
        rows,
        domain="insurance",
        language="ko",
        min_cluster_size=2,
        sample_size=2,
    )

    assert len(facts) == 1
    fact = facts[0]
    assert fact.subject == "Phoenix cluster 1"
    assert "보험료" in fact.object
    assert fact.verification_count == 2
    assert fact.source_document_ids == ["ex-1", "ex-2"]


def test_build_cluster_facts_skips_small_clusters() -> None:
    rows = [
        {"cluster_id": 9, "question": "단일 질문", "example_id": "only-1"},
    ]

    facts = build_cluster_facts(
        rows,
        domain="insurance",
        language="ko",
        min_cluster_size=2,
    )

    assert facts == []
