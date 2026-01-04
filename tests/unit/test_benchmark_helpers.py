"""Benchmark CLI helper utilities tests."""

from __future__ import annotations

import json

import pytest
import typer

from evalvault.adapters.inbound.cli.commands import benchmark as benchmark_module


def test_parse_methods_normalizes_aliases() -> None:
    methods = benchmark_module._parse_methods("bm25,graph,graphrag,hybrid")
    assert methods == ["bm25", "graphrag", "hybrid"]


def test_parse_methods_rejects_unknown() -> None:
    with pytest.raises(typer.BadParameter):
        benchmark_module._parse_methods("bm25,unknown")


def test_normalize_documents_uses_fallback_fields() -> None:
    docs = [
        {"doc_id": "doc-1", "content": "text-1"},
        {"id": "doc-2", "text": "text-2"},
        {"document": "text-3"},
    ]

    doc_ids, contents = benchmark_module._normalize_documents(docs)

    assert doc_ids == ["doc-1", "doc-2", "doc_3"]
    assert contents == ["text-1", "text-2", "text-3"]


def test_normalize_retrieval_test_cases_handles_legacy_fields() -> None:
    test_cases = [
        {"query": "질문", "relevant_doc_ids": ["doc-1"]},
        {"question": "질문2", "relevant_docs": ["doc-2"], "id": "tc-2"},
        {"relevant_docs": ["doc-3"]},
    ]

    normalized = benchmark_module._normalize_retrieval_test_cases(test_cases)

    assert len(normalized) == 2
    assert normalized[0]["query"] == "질문"
    assert normalized[0]["relevant_doc_ids"] == ["doc-1"]
    assert normalized[1]["test_id"] == "tc-2"
    assert normalized[1]["relevant_doc_ids"] == ["doc-2"]


def test_normalize_embedding_profile() -> None:
    assert benchmark_module._normalize_embedding_profile("dev") == "dev"
    assert benchmark_module._normalize_embedding_profile("Prod") == "prod"
    with pytest.raises(typer.BadParameter):
        benchmark_module._normalize_embedding_profile("invalid")


def test_resolve_ollama_embedding_model_prefers_explicit() -> None:
    model = benchmark_module._resolve_ollama_embedding_model(
        embedding_profile="dev",
        embedding_model="qwen3-embedding:custom",
    )
    assert model == "qwen3-embedding:custom"


def test_resolve_ollama_embedding_model_by_profile() -> None:
    assert (
        benchmark_module._resolve_ollama_embedding_model(
            embedding_profile="dev",
            embedding_model=None,
        )
        == "qwen3-embedding:0.6b"
    )
    assert (
        benchmark_module._resolve_ollama_embedding_model(
            embedding_profile="prod",
            embedding_model=None,
        )
        == "qwen3-embedding:8b"
    )


def test_format_metric_label_variants() -> None:
    assert benchmark_module._format_metric_label("precision_at_5") == "Precision@5"
    assert benchmark_module._format_metric_label("recall_at_10") == "Recall@10"
    assert benchmark_module._format_metric_label("ndcg_at_5") == "nDCG@5"
    assert benchmark_module._format_metric_label("mrr") == "MRR"


def test_build_overall_summary_selects_best() -> None:
    results = {
        "bm25": {"recall_at_5": 0.5, "precision_at_5": 0.2, "mrr": 0.1, "ndcg_at_5": 0.3},
        "dense": {"recall_at_5": 0.6, "precision_at_5": 0.1, "mrr": 0.2, "ndcg_at_5": 0.4},
    }

    summary = benchmark_module._build_overall_summary(
        results,
        "recall_at_5",
        "precision_at_5",
        "ndcg_at_5",
    )

    best = summary["best_by_metric"]
    assert best["recall_at_5"]["method"] == "dense"
    assert best["precision_at_5"]["method"] == "bm25"


def test_write_retrieval_output_csv(tmp_path) -> None:
    path = tmp_path / "out.csv"
    results = {
        "bm25": {
            "recall_at_5": 0.5,
            "precision_at_5": 0.2,
            "mrr": 0.3,
            "ndcg_at_5": 0.4,
            "test_cases": 2,
            "backend": "",
        }
    }
    payload = {"methods_compared": ["bm25"], "results": results, "overall": {}}

    benchmark_module._write_retrieval_output(
        path,
        payload,
        results,
        "recall_at_5",
        "precision_at_5",
        "ndcg_at_5",
    )

    contents = path.read_text(encoding="utf-8").splitlines()
    assert contents[0].startswith("method,recall_at_5,precision_at_5")
    assert "bm25,0.5,0.2,0.3,0.4,2," in contents[1]


def test_write_retrieval_output_json(tmp_path) -> None:
    path = tmp_path / "out.json"
    results = {"bm25": {"recall_at_5": 0.5}}
    payload = {"methods_compared": ["bm25"], "results": results, "overall": {"best": "bm25"}}

    benchmark_module._write_retrieval_output(
        path,
        payload,
        results,
        "recall_at_5",
        "precision_at_5",
        "ndcg_at_5",
    )

    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["methods_compared"] == ["bm25"]
    assert loaded["overall"]["best"] == "bm25"
