"""Tests for ParallelKGBuilder."""

from __future__ import annotations

from evalvault.adapters.outbound.kg.parallel_kg_builder import ParallelKGBuilder

DOCS = [
    "삼성생명 종신보험은 사망보험금 1억원을 보장합니다.",
    "한화생명 정기보험은 20년 동안 보장합니다.",
]


def test_parallel_kg_builder_serial_builds_graph() -> None:
    builder = ParallelKGBuilder(workers=1, batch_size=1, store_documents=True)
    result = builder.build(DOCS)

    graph = result.graph
    assert graph.has_entity("삼성생명")
    assert graph.has_entity("종신보험")
    assert graph.get_edge_count() > 0
    assert result.documents_by_id["doc-0"] == DOCS[0]
    assert result.stats.documents_processed == 2


def test_parallel_kg_builder_progress_callback() -> None:
    updates: list[int] = []

    def on_progress(stats) -> None:
        updates.append(stats.chunks_processed)

    builder = ParallelKGBuilder(workers=1, batch_size=1, progress_callback=on_progress)
    builder.build(DOCS)

    assert updates
    assert updates[-1] == 2


def test_parallel_kg_builder_streaming_iterable() -> None:
    def doc_gen():
        yield from DOCS

    builder = ParallelKGBuilder(workers=1, batch_size=2)
    result = builder.build(doc_gen())

    assert result.stats.documents_processed == 2
    assert result.documents_by_id == {}
