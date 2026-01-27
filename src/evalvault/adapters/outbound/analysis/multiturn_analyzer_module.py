"""
멀티턴 평가 요약 모듈입니다.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output, safe_mean
from evalvault.domain.entities import EvaluationRun


class MultiTurnAnalyzerModule(BaseAnalysisModule):
    """멀티턴(대화) 단위로 결과를 집계합니다."""

    module_id = "multiturn_analyzer"
    name = "멀티턴 분석"
    description = "대화/턴 메타데이터를 기준으로 멀티턴 성능을 요약합니다."
    input_types = ["run"]
    output_types = ["multiturn_summary", "multiturn_conversations", "multiturn_turns"]
    requires = ["data_loader"]
    tags = ["analysis", "multiturn"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")
        if not isinstance(run, EvaluationRun):
            return {
                "available": False,
                "summary": {},
                "conversations": [],
                "turns": [],
                "coverage": {},
            }

        retrieval_meta = run.retrieval_metadata or {}
        cases = run.results
        total_cases = len(cases)

        coverage = {
            "total_cases": total_cases,
            "has_conversation_id": 0,
            "has_turn_index": 0,
        }

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        turns: list[dict[str, Any]] = []

        for result in cases:
            case_meta = _resolve_case_metadata(retrieval_meta, result.test_case_id)
            conversation_id = _coerce_text(case_meta.get("conversation_id"))
            turn_index = _coerce_turn_index(case_meta.get("turn_index"))
            turn_id = _coerce_text(case_meta.get("turn_id"))

            if conversation_id:
                coverage["has_conversation_id"] += 1
            if turn_index is not None:
                coverage["has_turn_index"] += 1

            metrics = {
                metric.name: metric.score for metric in result.metrics if metric.score is not None
            }
            avg_score = safe_mean(metrics.values()) if metrics else 0.0
            failed_metrics = [metric.name for metric in result.metrics if not metric.passed]
            entry = {
                "test_case_id": result.test_case_id,
                "conversation_id": conversation_id,
                "turn_index": turn_index,
                "turn_id": turn_id,
                "avg_score": round(avg_score, 4),
                "metrics": metrics,
                "failed_metrics": failed_metrics,
                "passed_all": result.all_passed,
            }
            turns.append(entry)
            if conversation_id:
                grouped[conversation_id].append(entry)

        conversations: list[dict[str, Any]] = []
        first_failure_hist: dict[str, int] = defaultdict(int)

        for conversation_id, entries in grouped.items():
            entries_sorted = _sort_turns(entries)
            avg_scores = [item["avg_score"] for item in entries_sorted]
            metric_scores: dict[str, list[float]] = defaultdict(list)
            for item in entries_sorted:
                for name, score in (item.get("metrics") or {}).items():
                    metric_scores[name].append(float(score))

            metric_means = {
                name: round(safe_mean(values), 4) for name, values in metric_scores.items()
            }
            passed_all = all(item.get("passed_all") for item in entries_sorted)
            failure_turn = _first_failure_turn(entries_sorted)
            if failure_turn is not None:
                first_failure_hist[str(failure_turn)] += 1

            worst_turn = _select_worst_turn(entries_sorted)

            conversations.append(
                {
                    "conversation_id": conversation_id,
                    "turn_count": len(entries_sorted),
                    "avg_score": round(safe_mean(avg_scores), 4),
                    "passed_all_turns": passed_all,
                    "first_failure_turn_index": failure_turn,
                    "worst_turn": worst_turn,
                    "metric_means": metric_means,
                }
            )

        conversation_count = len(grouped)
        turn_count = sum(len(items) for items in grouped.values())
        summary = {
            "conversation_count": conversation_count,
            "turn_count": turn_count,
            "avg_turns_per_conversation": round(
                (turn_count / conversation_count) if conversation_count else 0.0, 3
            ),
            "conversation_pass_rate": round(
                (
                    sum(1 for item in conversations if item.get("passed_all_turns"))
                    / conversation_count
                )
                if conversation_count
                else 0.0,
                4,
            ),
            "first_failure_turn_histogram": dict(first_failure_hist),
        }

        if total_cases:
            coverage["has_conversation_id"] = round(
                coverage["has_conversation_id"] / total_cases, 4
            )
            coverage["has_turn_index"] = round(coverage["has_turn_index"] / total_cases, 4)

        return {
            "available": True,
            "summary": summary,
            "conversations": conversations,
            "turns": turns,
            "coverage": coverage,
        }


def _resolve_case_metadata(
    retrieval_metadata: dict[str, dict[str, Any]],
    test_case_id: str,
) -> dict[str, Any]:
    meta = retrieval_metadata.get(test_case_id)
    if isinstance(meta, dict):
        nested = meta.get("test_case_metadata")
        if isinstance(nested, dict):
            merged = dict(nested)
            merged.update({k: v for k, v in meta.items() if k != "test_case_metadata"})
            return merged
        return dict(meta)
    return {}


def _coerce_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed or None
    return str(value)


def _coerce_turn_index(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _sort_turns(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if all(item.get("turn_index") is None for item in entries):
        return list(entries)
    return sorted(
        entries, key=lambda item: (item.get("turn_index") is None, item.get("turn_index") or 0)
    )


def _first_failure_turn(entries: list[dict[str, Any]]) -> int | None:
    for item in entries:
        if not item.get("passed_all"):
            return item.get("turn_index")
    return None


def _select_worst_turn(entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not entries:
        return None
    worst = min(entries, key=lambda item: item.get("avg_score", 0.0))
    return {
        "test_case_id": worst.get("test_case_id"),
        "avg_score": worst.get("avg_score"),
        "failed_metrics": worst.get("failed_metrics", []),
    }
