"""Unit tests for StageMetricService."""

from evalvault.domain.entities.stage import StageEvent
from evalvault.domain.services.stage_metric_service import StageMetricService


def _metric_by_name(metrics):
    return {metric.metric_name: metric for metric in metrics}


def test_retrieval_metrics_with_relevance_map() -> None:
    event = StageEvent(
        run_id="run-001",
        stage_id="stg-retrieval-01",
        stage_type="retrieval",
        duration_ms=120.0,
        attributes={
            "doc_ids": ["doc-1", "doc-2", "doc-3"],
            "scores": [0.9, 0.5, 0.2],
            "top_k": 2,
        },
        metadata={"test_case_id": "tc-001"},
    )

    service = StageMetricService()
    metrics = service.build_metrics([event], relevance_map={"tc-001": ["doc-1", "doc-x"]})
    by_name = _metric_by_name(metrics)

    assert by_name["retrieval.latency_ms"].score == 120.0
    assert by_name["retrieval.latency_ms"].threshold == 500.0
    assert by_name["retrieval.latency_ms"].passed is True
    assert by_name["retrieval.result_count"].score == 3.0
    assert by_name["retrieval.avg_score"].score == (0.9 + 0.5 + 0.2) / 3
    assert by_name["retrieval.score_gap"].score == 0.9 - 0.2
    assert by_name["retrieval.precision_at_k"].score == 0.5
    assert by_name["retrieval.recall_at_k"].score == 0.5
    assert by_name["retrieval.precision_at_k"].threshold == 0.2
    assert by_name["retrieval.recall_at_k"].threshold == 0.6
    assert by_name["retrieval.recall_at_k"].passed is False
    assert by_name["retrieval.result_count"].threshold == 1.0
    assert by_name["retrieval.result_count"].passed is True


def test_rerank_metrics_keep_rate() -> None:
    event = StageEvent(
        run_id="run-001",
        stage_id="stg-rerank-01",
        stage_type="rerank",
        duration_ms=600.0,
        attributes={"input_count": 10, "output_count": 4, "scores": [0.8, 0.75]},
    )

    service = StageMetricService()
    metrics = service.build_metrics([event])
    by_name = _metric_by_name(metrics)

    assert by_name["rerank.keep_rate"].score == 0.4
    assert by_name["rerank.avg_score"].score == (0.8 + 0.75) / 2
    assert by_name["rerank.score_gap"].score == 0.8 - 0.75
    assert by_name["rerank.latency_ms"].threshold == 800.0
    assert by_name["rerank.latency_ms"].passed is True
    assert by_name["rerank.keep_rate"].threshold == 0.25
    assert by_name["rerank.keep_rate"].passed is True
    assert by_name["rerank.score_gap"].threshold == 0.1
    assert by_name["rerank.score_gap"].passed is False


def test_output_metrics_token_ratio() -> None:
    event = StageEvent(
        run_id="run-001",
        stage_id="stg-output-01",
        stage_type="output",
        duration_ms=1500.0,
        attributes={
            "tokens_in": 1000,
            "tokens_out": 250,
            "citations": ["doc-1", "doc-2"],
        },
    )

    service = StageMetricService()
    metrics = service.build_metrics([event])
    by_name = _metric_by_name(metrics)

    assert by_name["output.token_ratio"].score == 0.25
    assert by_name["output.citation_count"].score == 2.0
    assert by_name["output.citation_count"].threshold == 1.0
    assert by_name["output.citation_count"].passed is True
    assert by_name["output.latency_ms"].threshold == 3000.0
    assert by_name["output.latency_ms"].passed is True


def test_output_metrics_missing_citations() -> None:
    event = StageEvent(
        run_id="run-001",
        stage_id="stg-output-02",
        stage_type="output",
        duration_ms=900.0,
        attributes={"tokens_in": 400, "tokens_out": 100},
    )

    service = StageMetricService()
    metrics = service.build_metrics([event])
    by_name = _metric_by_name(metrics)

    assert by_name["output.citation_count"].score == 0.0
    assert by_name["output.citation_count"].threshold == 1.0
    assert by_name["output.citation_count"].passed is False
    assert by_name["output.citation_count"].evidence["missing"] is True


def test_input_metrics_query_length() -> None:
    event = StageEvent(
        run_id="run-003",
        stage_id="stg-input-01",
        stage_type="input",
        attributes={"query": "보험 약관 요약"},
    )

    metrics = StageMetricService().build_metrics([event])
    by_name = _metric_by_name(metrics)

    assert by_name["input.query_length"].score == float(len("보험 약관 요약"))


def test_language_detection_metrics() -> None:
    event = StageEvent(
        run_id="run-004",
        stage_id="stg-lang-01",
        stage_type="language_detection",
        attributes={"predicted_label": "ko", "label": "ko", "confidence": 0.92},
    )

    metrics = StageMetricService().build_metrics([event])
    by_name = _metric_by_name(metrics)

    assert by_name["language_detection.accuracy"].score == 1.0
    assert by_name["language_detection.confidence"].score == 0.92


def test_safety_check_metrics() -> None:
    event = StageEvent(
        run_id="run-005",
        stage_id="stg-safe-01",
        stage_type="safety_check",
        attributes={"violations": ["pii"], "blocked": True},
    )

    metrics = StageMetricService().build_metrics([event])
    by_name = _metric_by_name(metrics)

    assert by_name["safety_check.violation_rate"].score == 1.0
    assert by_name["safety_check.block_rate"].score == 1.0
    assert by_name["safety_check.violation_rate"].evidence["comparison"] == "max"


def test_retrieval_metrics_empty_docs() -> None:
    event = StageEvent(
        run_id="run-006",
        stage_id="stg-retrieval-empty",
        stage_type="retrieval",
        attributes={},
    )

    metrics = StageMetricService().build_metrics([event])
    by_name = _metric_by_name(metrics)

    assert by_name["retrieval.result_count"].score == 0.0
