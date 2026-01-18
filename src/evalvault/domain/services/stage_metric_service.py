"""Stage metric computation service."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from evalvault.domain.entities.stage import StageEvent, StageMetric

DEFAULT_STAGE_THRESHOLDS: dict[str, float] = {
    "retrieval.precision_at_k": 0.2,
    "retrieval.recall_at_k": 0.6,
    "retrieval.result_count": 1.0,
    "retrieval.avg_score": 0.2,
    "retrieval.score_gap": 0.1,
    "retrieval.latency_ms": 500.0,
    "rerank.keep_rate": 0.25,
    "rerank.avg_score": 0.2,
    "rerank.score_gap": 0.1,
    "rerank.latency_ms": 800.0,
    "output.latency_ms": 3000.0,
    "output.citation_count": 1.0,
}


class StageMetricService:
    """Compute basic stage metrics from StageEvent data."""

    def build_metrics(
        self,
        events: Iterable[StageEvent],
        *,
        relevance_map: Mapping[str, Sequence[str]] | None = None,
        thresholds: Mapping[str, float] | None = None,
    ) -> list[StageMetric]:
        normalized_relevance = _normalize_relevance_map(relevance_map)
        resolved_thresholds = _resolve_thresholds(thresholds)
        metrics: list[StageMetric] = []
        for event in events:
            metrics.extend(self._metrics_for_event(event, normalized_relevance))
        if resolved_thresholds:
            for metric in metrics:
                metric.threshold = resolved_thresholds.get(metric.metric_name)
        return metrics

    def _metrics_for_event(
        self,
        event: StageEvent,
        relevance_map: Mapping[str, set[str]],
    ) -> list[StageMetric]:
        metrics: list[StageMetric] = []
        if event.duration_ms is not None:
            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name=f"{event.stage_type}.latency_ms",
                    score=float(event.duration_ms),
                    evidence={"duration_ms": event.duration_ms, "comparison": "max"},
                )
            )

        if event.stage_type == "retrieval":
            metrics.extend(self._retrieval_metrics(event, relevance_map))
        elif event.stage_type == "rerank":
            metrics.extend(self._rerank_metrics(event))
        elif event.stage_type == "output":
            metrics.extend(self._output_metrics(event))
        elif event.stage_type == "input":
            metrics.extend(self._input_metrics(event))
        elif event.stage_type in {"language_detection", "intent"}:
            metrics.extend(self._classification_metrics(event, prefix=event.stage_type))
        elif event.stage_type == "safety_check":
            metrics.extend(self._safety_metrics(event))
        elif event.stage_type == "answer_validation":
            metrics.extend(self._answer_validation_metrics(event))

        return metrics

    def _retrieval_metrics(
        self,
        event: StageEvent,
        relevance_map: Mapping[str, set[str]],
    ) -> list[StageMetric]:
        metrics: list[StageMetric] = []
        raw_doc_ids = event.attributes.get("doc_ids")
        raw_scores = event.attributes.get("scores")
        unordered_doc_ids = isinstance(raw_doc_ids, set | frozenset)
        unordered_scores = isinstance(raw_scores, set | frozenset)
        doc_ids = _to_str_list(raw_doc_ids)
        scores = _to_float_list(raw_scores)
        order_reconstructed = None
        if unordered_doc_ids:
            doc_ids = sorted(doc_ids)
            order_reconstructed = "doc_id_asc"

        metrics.append(
            StageMetric(
                run_id=event.run_id,
                stage_id=event.stage_id,
                metric_name="retrieval.result_count",
                score=float(len(doc_ids)),
                evidence=_with_order_evidence({"count": len(doc_ids)}, unordered_doc_ids, None),
            )
        )
        if unordered_doc_ids or unordered_scores:
            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name="retrieval.ordering_warning",
                    score=1.0,
                    evidence=_with_order_evidence(
                        {
                            "doc_ids_unordered": unordered_doc_ids,
                            "scores_unordered": unordered_scores,
                        },
                        True,
                        order_reconstructed,
                    ),
                )
            )

        if scores:
            avg_score = _safe_avg(scores)
            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name="retrieval.avg_score",
                    score=avg_score,
                    evidence=_with_order_evidence({"count": len(scores)}, unordered_scores, None),
                )
            )
            if len(scores) > 1:
                score_gap = max(scores) - min(scores)
                metrics.append(
                    StageMetric(
                        run_id=event.run_id,
                        stage_id=event.stage_id,
                        metric_name="retrieval.score_gap",
                        score=score_gap,
                        evidence=_with_order_evidence(
                            {"max": max(scores), "min": min(scores)}, unordered_scores, None
                        ),
                    )
                )

        relevant_docs = _get_relevant_docs(event, relevance_map)
        if doc_ids and relevant_docs:
            top_k = _coerce_int(event.attributes.get("top_k"), default=len(doc_ids))
            k = len(doc_ids) if top_k is None or top_k <= 0 else min(top_k, len(doc_ids))
            if unordered_scores and scores:
                score_pairs = list(zip(doc_ids, scores, strict=False))
                score_pairs.sort(key=lambda item: (-item[1], item[0]))
                doc_ids = [doc_id for doc_id, _score in score_pairs]
                scores = [score for _doc_id, score in score_pairs]
                order_reconstructed = "score_desc_then_id"
            retrieved_top_k = doc_ids[:k]
            relevant_found = len(set(retrieved_top_k) & relevant_docs)

            precision = relevant_found / k if k > 0 else 0.0
            recall = relevant_found / len(relevant_docs) if len(relevant_docs) > 0 else 0.0

            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name="retrieval.precision_at_k",
                    score=precision,
                    evidence=_with_order_evidence(
                        {
                            "k": k,
                            "relevant_found": relevant_found,
                            "retrieved_count": k,
                        },
                        unordered_doc_ids or unordered_scores,
                        order_reconstructed,
                    ),
                )
            )
            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name="retrieval.recall_at_k",
                    score=recall,
                    evidence=_with_order_evidence(
                        {
                            "k": k,
                            "relevant_found": relevant_found,
                            "relevant_total": len(relevant_docs),
                        },
                        unordered_doc_ids or unordered_scores,
                        order_reconstructed,
                    ),
                )
            )

        return metrics

    def _rerank_metrics(self, event: StageEvent) -> list[StageMetric]:
        metrics: list[StageMetric] = []
        input_count = _coerce_int(event.attributes.get("input_count"))
        output_count = _coerce_int(event.attributes.get("output_count"))

        if input_count and output_count is not None and input_count > 0:
            keep_rate = output_count / input_count
            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name="rerank.keep_rate",
                    score=keep_rate,
                    evidence={
                        "input_count": input_count,
                        "output_count": output_count,
                    },
                )
            )

        scores = _to_float_list(event.attributes.get("scores"))
        if scores:
            avg_score = _safe_avg(scores)
            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name="rerank.avg_score",
                    score=avg_score,
                    evidence={"count": len(scores)},
                )
            )
            if len(scores) > 1:
                score_gap = max(scores) - min(scores)
                metrics.append(
                    StageMetric(
                        run_id=event.run_id,
                        stage_id=event.stage_id,
                        metric_name="rerank.score_gap",
                        score=score_gap,
                        evidence={"max": max(scores), "min": min(scores)},
                    )
                )

        return metrics

    def _output_metrics(self, event: StageEvent) -> list[StageMetric]:
        metrics: list[StageMetric] = []
        tokens_in = _coerce_int(event.attributes.get("tokens_in"))
        tokens_out = _coerce_int(event.attributes.get("tokens_out"))

        if tokens_in and tokens_out is not None and tokens_in > 0:
            ratio = tokens_out / tokens_in
            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name="output.token_ratio",
                    score=ratio,
                    evidence={"tokens_in": tokens_in, "tokens_out": tokens_out},
                )
            )

        citations = event.attributes.get("citations")
        citation_count = 0 if citations is None else _count_citations(citations)
        if citation_count is None:
            citation_count = 0
            citations = None
        evidence = {"count": citation_count}
        if citations is None:
            evidence["missing"] = True
        metrics.append(
            StageMetric(
                run_id=event.run_id,
                stage_id=event.stage_id,
                metric_name="output.citation_count",
                score=float(citation_count),
                evidence=evidence,
            )
        )

        return metrics

    def _input_metrics(self, event: StageEvent) -> list[StageMetric]:
        metrics: list[StageMetric] = []
        query = event.attributes.get("query")
        if isinstance(query, str):
            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name="input.query_length",
                    score=float(len(query)),
                    evidence={"length": len(query)},
                )
            )
        return metrics

    def _classification_metrics(self, event: StageEvent, *, prefix: str) -> list[StageMetric]:
        metrics: list[StageMetric] = []
        predicted = event.attributes.get("predicted_label")
        label = event.attributes.get("label")
        if isinstance(predicted, str) and isinstance(label, str):
            score = 1.0 if predicted == label else 0.0
            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name=f"{prefix}.accuracy",
                    score=score,
                    evidence={"predicted": predicted, "label": label},
                )
            )

        confidence = _coerce_float(event.attributes.get("confidence"))
        if confidence is not None:
            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name=f"{prefix}.confidence",
                    score=confidence,
                    evidence={"confidence": confidence},
                )
            )

        return metrics

    def _safety_metrics(self, event: StageEvent) -> list[StageMetric]:
        metrics: list[StageMetric] = []
        violation_count = _extract_violation_count(event.attributes)
        if violation_count is not None:
            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name="safety_check.violation_rate",
                    score=1.0 if violation_count > 0 else 0.0,
                    evidence={"violations": violation_count, "comparison": "max"},
                )
            )

        blocked = event.attributes.get("blocked")
        if blocked is not None:
            blocked_flag = bool(blocked)
            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name="safety_check.block_rate",
                    score=1.0 if blocked_flag else 0.0,
                    evidence={"blocked": blocked_flag, "comparison": "max"},
                )
            )

        return metrics

    def _answer_validation_metrics(self, event: StageEvent) -> list[StageMetric]:
        metrics: list[StageMetric] = []
        passed = event.attributes.get("passed")
        if passed is not None:
            passed_flag = bool(passed)
            metrics.append(
                StageMetric(
                    run_id=event.run_id,
                    stage_id=event.stage_id,
                    metric_name="answer_validation.pass_rate",
                    score=1.0 if passed_flag else 0.0,
                    evidence={"passed": passed_flag},
                )
            )
        return metrics


def _get_relevant_docs(event: StageEvent, relevance_map: Mapping[str, set[str]]) -> set[str] | None:
    raw = event.attributes.get("relevant_doc_ids") or event.metadata.get("relevant_doc_ids")
    if raw:
        return _to_str_set(raw)
    test_case_id = event.metadata.get("test_case_id")
    if test_case_id and isinstance(test_case_id, str):
        return relevance_map.get(test_case_id)
    return None


def _normalize_relevance_map(
    relevance_map: Mapping[str, Sequence[str]] | None,
) -> dict[str, set[str]]:
    if not relevance_map:
        return {}
    normalized: dict[str, set[str]] = {}
    for key, value in relevance_map.items():
        normalized[key] = _to_str_set(value)
    return normalized


def _to_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, set | frozenset):
        return [str(item) for item in value if not isinstance(item, bytes | bytearray)]
    if isinstance(value, Sequence):
        return [str(item) for item in value if not isinstance(item, bytes | bytearray)]
    return [str(value)]


def _to_str_set(value: Any) -> set[str]:
    return set(_to_str_list(value))


def _to_float_list(value: Any) -> list[float]:
    if value is None:
        return []
    if isinstance(value, set | frozenset):
        return [float(item) for item in value]
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [float(item) for item in value]
    return [float(value)]


def _coerce_int(value: Any, *, default: int | None = None) -> int | None:
    if value is None:
        return default
    return int(value)


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_avg(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    total = math.fsum(values)
    return total / len(values)


def _with_order_evidence(
    evidence: dict[str, Any], unordered: bool, order_reconstructed: str | None
) -> dict[str, Any]:
    if not unordered:
        return evidence
    enriched = dict(evidence)
    enriched["unordered_input"] = True
    if order_reconstructed:
        enriched["order_reconstructed"] = order_reconstructed
    return enriched


def _extract_violation_count(attributes: Mapping[str, Any]) -> int | None:
    violations = attributes.get("violations")
    if isinstance(violations, list | tuple | set):
        return len(violations)
    count = attributes.get("violation_count")
    if count is None:
        return None
    try:
        return int(count)
    except (TypeError, ValueError):
        return None


def _count_citations(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, list | tuple | set):
        return len(value)
    if isinstance(value, dict):
        for key in ("doc_ids", "ids", "sources", "citations"):
            nested = value.get(key)
            if isinstance(nested, list | tuple | set):
                return len(nested)
        if "count" in value:
            try:
                return int(value["count"])
            except (TypeError, ValueError):
                return None
        return len(value)
    return 1


def _resolve_thresholds(
    thresholds: Mapping[str, float] | None,
) -> dict[str, float]:
    if thresholds is None:
        return dict(DEFAULT_STAGE_THRESHOLDS)
    if not thresholds:
        return {}
    resolved = dict(DEFAULT_STAGE_THRESHOLDS)
    for key, value in thresholds.items():
        resolved[str(key)] = float(value)
    return resolved
