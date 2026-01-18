"""Stage event builder for evaluation runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from evalvault.domain.entities.result import EvaluationRun, TestCaseResult
from evalvault.domain.entities.stage import StageEvent


@dataclass(frozen=True)
class StageEventBuilder:
    """Build StageEvent lists from EvaluationRun data."""

    max_text_length: int = 2000

    def build_for_run(
        self,
        run: EvaluationRun,
        *,
        prompt_metadata: list[dict[str, Any]] | None = None,
        retrieval_metadata: dict[str, dict[str, Any]] | None = None,
    ) -> list[StageEvent]:
        events: list[StageEvent] = []

        system_prompt_id = None
        if prompt_metadata:
            system_prompt_id = str(uuid4())
            events.append(
                StageEvent(
                    run_id=run.run_id,
                    stage_id=system_prompt_id,
                    stage_type="system_prompt",
                    stage_name="prompt_manifest",
                    attributes={
                        "prompts": _trim_prompt_metadata(prompt_metadata, self.max_text_length)
                    },
                    metadata=_run_metadata(run),
                )
            )

        for result in run.results:
            events.extend(
                self._build_for_result(
                    run,
                    result,
                    parent_stage_id=system_prompt_id,
                    retrieval_metadata=retrieval_metadata,
                )
            )

        return events

    def _build_for_result(
        self,
        run: EvaluationRun,
        result: TestCaseResult,
        *,
        parent_stage_id: str | None,
        retrieval_metadata: dict[str, dict[str, Any]] | None,
    ) -> list[StageEvent]:
        events: list[StageEvent] = []
        base_metadata = _result_metadata(run, result)

        input_id = str(uuid4())
        input_attrs = {}
        if result.question is not None:
            input_attrs["query"] = _trim_text(result.question, self.max_text_length)
        events.append(
            StageEvent(
                run_id=run.run_id,
                stage_id=input_id,
                parent_stage_id=parent_stage_id,
                stage_type="input",
                stage_name="user_query",
                attributes=input_attrs,
                metadata=base_metadata,
                trace_id=result.trace_id,
            )
        )

        retrieval_id = str(uuid4())
        retrieval_attrs, retrieval_duration = _build_retrieval_attributes(
            result,
            retrieval_metadata=retrieval_metadata,
        )
        doc_ids = retrieval_attrs.get("doc_ids", [])
        events.append(
            StageEvent(
                run_id=run.run_id,
                stage_id=retrieval_id,
                parent_stage_id=input_id,
                stage_type="retrieval",
                stage_name="context_lookup",
                attributes=retrieval_attrs,
                metadata=base_metadata,
                trace_id=result.trace_id,
                duration_ms=retrieval_duration,
            )
        )

        output_attrs = {"citations": doc_ids}
        if result.answer is not None:
            output_attrs["answer"] = _trim_text(result.answer, self.max_text_length)
        if result.tokens_used:
            output_attrs["tokens_used"] = result.tokens_used
        events.append(
            StageEvent(
                run_id=run.run_id,
                stage_id=str(uuid4()),
                parent_stage_id=retrieval_id,
                stage_type="output",
                stage_name="final_answer",
                attributes=output_attrs,
                metadata=base_metadata,
                trace_id=result.trace_id,
                started_at=result.started_at,
                finished_at=result.finished_at,
                duration_ms=float(result.latency_ms) if result.latency_ms else None,
            )
        )

        return events


def _run_metadata(run: EvaluationRun) -> dict[str, Any]:
    return {
        "dataset_name": run.dataset_name,
        "dataset_version": run.dataset_version,
        "model_name": run.model_name,
    }


def _result_metadata(run: EvaluationRun, result: TestCaseResult) -> dict[str, Any]:
    metadata = _run_metadata(run)
    metadata["test_case_id"] = result.test_case_id
    return metadata


def _trim_text(text: str, max_length: int) -> str:
    normalized = text.strip()
    if len(normalized) <= max_length:
        return normalized
    return normalized[:max_length].rstrip() + f"... (+{len(normalized) - max_length} chars)"


def _build_doc_ids(contexts: list[str] | None) -> list[str]:
    if not contexts:
        return []
    return [f"context_{idx}" for idx, _ in enumerate(contexts, start=1)]


def _build_retrieval_attributes(
    result: TestCaseResult,
    *,
    retrieval_metadata: dict[str, dict[str, Any]] | None,
) -> tuple[dict[str, Any], float | None]:
    fallback_doc_ids = _build_doc_ids(result.contexts)
    if not retrieval_metadata:
        return {
            "doc_ids": fallback_doc_ids,
            "top_k": len(fallback_doc_ids),
            "retrieval_time_ms": 0.0,
        }, None

    metadata = retrieval_metadata.get(result.test_case_id)
    if not isinstance(metadata, dict):
        return {
            "doc_ids": fallback_doc_ids,
            "top_k": len(fallback_doc_ids),
            "retrieval_time_ms": 0.0,
        }, None

    doc_ids = _normalize_doc_ids(metadata.get("doc_ids"), fallback=fallback_doc_ids)
    top_k = _coerce_int(metadata.get("top_k"), default=len(doc_ids))
    scores = _normalize_scores(metadata.get("scores"))

    attributes = {"doc_ids": doc_ids, "top_k": top_k}
    if scores:
        attributes["scores"] = scores
    retrieval_duration = _apply_retrieval_perf_attributes(attributes, metadata)
    return attributes, retrieval_duration


def _apply_retrieval_perf_attributes(
    attributes: dict[str, Any],
    metadata: dict[str, Any],
) -> float | None:
    retrieval_time = _coerce_float(metadata.get("retrieval_time_ms"))
    if retrieval_time is None:
        retrieval_time = _coerce_float(metadata.get("duration_ms"))
    if retrieval_time is not None:
        attributes["retrieval_time_ms"] = retrieval_time
    else:
        attributes.setdefault("retrieval_time_ms", 0.0)

    perf_keys: dict[str, str] = {
        "index_build_time_ms": "float",
        "cache_hit": "bool",
        "batch_size": "int",
        "total_docs_searched": "int",
        "index_size": "int",
        "faiss_gpu_active": "bool",
        "graph_nodes": "int",
        "graph_edges": "int",
        "subgraph_size": "int",
    }

    for key, kind in perf_keys.items():
        if key not in metadata:
            continue
        value = metadata.get(key)
        if kind == "float":
            coerced = _coerce_float(value)
        elif kind == "int":
            coerced = _coerce_int_optional(value)
        else:
            coerced = _coerce_bool(value)
        if coerced is not None:
            attributes[key] = coerced

    if "community_id" in metadata:
        attributes["community_id"] = _coerce_text_or_list(metadata.get("community_id"))

    return retrieval_time


def _trim_prompt_metadata(
    prompt_metadata: list[dict[str, Any]],
    max_length: int,
) -> list[dict[str, Any]]:
    trimmed: list[dict[str, Any]] = []
    for entry in prompt_metadata:
        if not isinstance(entry, dict):
            continue
        copy = dict(entry)
        preview = copy.get("content_preview")
        if isinstance(preview, str):
            copy["content_preview"] = _trim_text(preview, max_length)
        trimmed.append(copy)
    return trimmed


def _normalize_doc_ids(value: Any, *, fallback: list[str]) -> list[str]:
    if value is None:
        return fallback
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value]
    return [str(value)]


def _normalize_scores(value: Any) -> list[float]:
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        scores: list[float] = []
        for item in value:
            score = _coerce_float(item)
            if score is not None:
                scores.append(score)
        return scores
    coerced = _coerce_float(value)
    return [coerced] if coerced is not None else []


def _coerce_int(value: Any, *, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int_optional(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, float):
        return bool(int(value))
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    return None


def _coerce_text_or_list(value: Any) -> str | list[str] | None:
    if value is None:
        return None
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value]
    return str(value)
