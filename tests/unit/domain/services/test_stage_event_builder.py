"""Unit tests for StageEventBuilder."""

from evalvault.domain.entities.result import EvaluationRun, TestCaseResult
from evalvault.domain.services.stage_event_builder import StageEventBuilder


def test_build_for_run_includes_required_stages() -> None:
    run = EvaluationRun(
        run_id="run-100",
        dataset_name="insurance_qa",
        dataset_version="v1",
        model_name="gpt-test",
        results=[
            TestCaseResult(
                test_case_id="tc-001",
                metrics=[],
                tokens_used=120,
                latency_ms=450,
                question="보험 약관 요약해줘",
                answer="요약 답변",
                contexts=["ctx-1", "ctx-2"],
            )
        ],
    )

    builder = StageEventBuilder(max_text_length=50)
    events = builder.build_for_run(
        run,
        prompt_metadata=[{"path": "prompt.txt", "status": "synced", "current_checksum": "abc"}],
    )

    stage_types = [event.stage_type for event in events]
    assert "system_prompt" in stage_types
    assert "input" in stage_types
    assert "retrieval" in stage_types
    assert "output" in stage_types

    retrieval_event = next(event for event in events if event.stage_type == "retrieval")
    output_event = next(event for event in events if event.stage_type == "output")

    assert retrieval_event.attributes["doc_ids"] == ["context_1", "context_2"]
    assert output_event.parent_stage_id == retrieval_event.stage_id
    assert output_event.attributes["citations"] == ["context_1", "context_2"]


def test_build_for_run_uses_retrieval_metadata() -> None:
    run = EvaluationRun(
        run_id="run-200",
        dataset_name="insurance_qa",
        dataset_version="v1",
        model_name="gpt-test",
        results=[
            TestCaseResult(
                test_case_id="tc-001",
                metrics=[],
                question="보험 약관 요약해줘",
                answer="요약 답변",
                contexts=["ctx-1"],
            )
        ],
    )

    retrieval_metadata = {"tc-001": {"doc_ids": ["doc-9"], "scores": [0.91], "top_k": 1}}

    builder = StageEventBuilder()
    events = builder.build_for_run(run, retrieval_metadata=retrieval_metadata)

    retrieval_event = next(event for event in events if event.stage_type == "retrieval")

    assert retrieval_event.attributes["doc_ids"] == ["doc-9"]
    assert retrieval_event.attributes["scores"] == [0.91]
    assert retrieval_event.attributes["top_k"] == 1


def test_build_for_run_includes_retrieval_time_ms() -> None:
    run = EvaluationRun(
        run_id="run-201",
        dataset_name="insurance_qa",
        dataset_version="v1",
        model_name="gpt-test",
        results=[
            TestCaseResult(
                test_case_id="tc-002",
                metrics=[],
                question="보험 약관 요약해줘",
                answer="요약 답변",
                contexts=[],
            )
        ],
    )

    retrieval_metadata = {"tc-002": {"doc_ids": [], "top_k": 2, "retrieval_time_ms": 12.5}}

    events = StageEventBuilder().build_for_run(run, retrieval_metadata=retrieval_metadata)
    retrieval_event = next(event for event in events if event.stage_type == "retrieval")

    assert retrieval_event.attributes["retrieval_time_ms"] == 12.5
    assert retrieval_event.duration_ms == 12.5


def test_build_for_run_includes_retrieval_perf_attributes() -> None:
    run = EvaluationRun(
        run_id="run-202",
        dataset_name="insurance_qa",
        dataset_version="v1",
        model_name="gpt-test",
        results=[
            TestCaseResult(
                test_case_id="tc-003",
                metrics=[],
                question="보험 약관 요약해줘",
                answer="요약 답변",
                contexts=[],
            )
        ],
    )

    retrieval_metadata = {
        "tc-003": {
            "doc_ids": ["doc-1"],
            "top_k": 1,
            "retrieval_time_ms": 8.0,
            "index_build_time_ms": 120.0,
            "cache_hit": True,
            "batch_size": 32,
            "total_docs_searched": 1000,
            "index_size": 1000,
            "faiss_gpu_active": False,
        }
    }

    events = StageEventBuilder().build_for_run(run, retrieval_metadata=retrieval_metadata)
    retrieval_event = next(event for event in events if event.stage_type == "retrieval")

    assert retrieval_event.attributes["index_build_time_ms"] == 120.0
    assert retrieval_event.attributes["cache_hit"] is True
    assert retrieval_event.attributes["batch_size"] == 32
    assert retrieval_event.attributes["total_docs_searched"] == 1000
    assert retrieval_event.attributes["index_size"] == 1000
    assert retrieval_event.attributes["faiss_gpu_active"] is False


def test_build_for_run_includes_graphrag_attributes() -> None:
    run = EvaluationRun(
        run_id="run-203",
        dataset_name="insurance_qa",
        dataset_version="v1",
        model_name="gpt-test",
        results=[
            TestCaseResult(
                test_case_id="tc-004",
                metrics=[],
                question="보험 약관 요약해줘",
                answer="요약 답변",
                contexts=[],
            )
        ],
    )

    retrieval_metadata = {
        "tc-004": {
            "doc_ids": ["doc-1"],
            "top_k": 1,
            "retrieval_time_ms": 5.0,
            "graph_nodes": 3,
            "graph_edges": 2,
            "subgraph_size": 5,
            "community_id": "c-1",
        }
    }

    events = StageEventBuilder().build_for_run(run, retrieval_metadata=retrieval_metadata)
    retrieval_event = next(event for event in events if event.stage_type == "retrieval")

    assert retrieval_event.attributes["graph_nodes"] == 3
    assert retrieval_event.attributes["graph_edges"] == 2
    assert retrieval_event.attributes["subgraph_size"] == 5
    assert retrieval_event.attributes["community_id"] == "c-1"
