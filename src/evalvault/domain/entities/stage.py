"""Stage-level trace entities for RAG pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, overload
from uuid import uuid4

REQUIRED_STAGE_TYPES: tuple[str, ...] = ("system_prompt", "input", "retrieval", "output")


@dataclass
class StagePayloadRef:
    """Reference to a stored payload (input/output)."""

    store: str
    id: str
    type: str = "json"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> StagePayloadRef:
        if not payload.get("store") or not payload.get("id"):
            raise ValueError("StagePayloadRef requires 'store' and 'id'")
        return cls(
            store=str(payload["store"]),
            id=str(payload["id"]),
            type=str(payload.get("type", "json")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"store": self.store, "id": self.id, "type": self.type}


@dataclass
class StageEvent:
    """Single stage execution event within a RAG pipeline."""

    run_id: str
    stage_type: str
    stage_id: str = field(default_factory=lambda: str(uuid4()))
    stage_name: str | None = None
    parent_stage_id: str | None = None
    status: str = "success"
    attempt: int = 1
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: float | None = None
    input_ref: StagePayloadRef | None = None
    output_ref: StagePayloadRef | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None
    span_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.attributes, dict):
            raise ValueError("StageEvent requires attributes dict")
        if not isinstance(self.metadata, dict):
            raise ValueError("StageEvent requires metadata dict")
        self.stage_type = str(self.stage_type).strip().lower()
        if not self.stage_type:
            raise ValueError("StageEvent requires non-empty 'stage_type'")
        if self.attempt < 1:
            raise ValueError("StageEvent requires attempt >= 1")
        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError("StageEvent requires non-negative duration_ms")
        if self.started_at and self.finished_at and self.finished_at < self.started_at:
            raise ValueError("StageEvent requires finished_at >= started_at")
        if self.duration_ms is None and self.started_at and self.finished_at:
            delta = self.finished_at - self.started_at
            self.duration_ms = delta.total_seconds() * 1000

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> StageEvent:
        run_id = _require_str(payload, "run_id")
        stage_type = _normalize_stage_type(payload)

        trace_payload = payload.get("trace") or {}
        input_ref = _parse_payload_ref(payload.get("input_ref"))
        output_ref = _parse_payload_ref(payload.get("output_ref"))

        return cls(
            run_id=run_id,
            stage_type=stage_type,
            stage_id=str(payload.get("stage_id") or uuid4()),
            stage_name=_optional_str(payload.get("stage_name")),
            parent_stage_id=_optional_str(payload.get("parent_stage_id")),
            status=str(payload.get("status", "success")),
            attempt=int(payload.get("attempt", 1)),
            started_at=_parse_datetime(payload.get("started_at")),
            finished_at=_parse_datetime(payload.get("finished_at")),
            duration_ms=_optional_float(payload.get("duration_ms")),
            input_ref=input_ref,
            output_ref=output_ref,
            attributes=_ensure_dict(payload.get("attributes"), allow_none=False),
            metadata=_ensure_dict(payload.get("metadata"), allow_none=False),
            trace_id=_optional_str(payload.get("trace_id") or trace_payload.get("trace_id")),
            span_id=_optional_str(payload.get("span_id") or trace_payload.get("span_id")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "stage_id": self.stage_id,
            "parent_stage_id": self.parent_stage_id,
            "stage_type": self.stage_type,
            "stage_name": self.stage_name,
            "status": self.status,
            "attempt": self.attempt,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_ms": self.duration_ms,
            "input_ref": self.input_ref.to_dict() if self.input_ref else None,
            "output_ref": self.output_ref.to_dict() if self.output_ref else None,
            "attributes": self.attributes,
            "metadata": self.metadata,
            "trace": {"trace_id": self.trace_id, "span_id": self.span_id},
        }


@dataclass
class StageMetric:
    """Stage-level evaluation metric."""

    run_id: str
    stage_id: str
    metric_name: str
    score: float
    threshold: float | None = None
    evidence: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> StageMetric:
        return cls(
            run_id=str(payload["run_id"]),
            stage_id=str(payload["stage_id"]),
            metric_name=str(payload["metric_name"]),
            score=float(payload["score"]),
            threshold=_optional_float(payload.get("threshold")),
            evidence=_ensure_dict(payload.get("evidence"), allow_none=True),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "stage_id": self.stage_id,
            "metric_name": self.metric_name,
            "score": self.score,
            "threshold": self.threshold,
            "evidence": self.evidence,
        }

    @property
    def passed(self) -> bool | None:
        """Return pass status when threshold is provided."""
        if self.threshold is None:
            return None
        comparison = None
        if isinstance(self.evidence, dict):
            comparison = self.evidence.get("comparison")
        if isinstance(comparison, str) and comparison.lower() in {"max", "<=", "le"}:
            return self.score <= self.threshold
        return self.score >= self.threshold


@dataclass
class StageSummary:
    """Aggregated summary for stage events."""

    run_id: str
    total_events: int
    stage_type_counts: dict[str, int]
    stage_type_avg_durations: dict[str, float]
    missing_required_stage_types: list[str]


def _parse_payload_ref(payload: Any) -> StagePayloadRef | None:
    if payload is None:
        return None
    if isinstance(payload, StagePayloadRef):
        return payload
    if isinstance(payload, dict):
        return StagePayloadRef.from_dict(payload)
    raise ValueError("input_ref/output_ref must be a dict or StagePayloadRef")


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        return datetime.fromisoformat(normalized)
    raise ValueError("Invalid datetime value")


def _require_str(payload: dict[str, Any], key: str) -> str:
    if key not in payload:
        raise ValueError(f"StageEvent requires '{key}'")
    value = str(payload.get(key, "")).strip()
    if not value:
        raise ValueError(f"StageEvent requires non-empty '{key}'")
    return value


def _normalize_stage_type(payload: dict[str, Any]) -> str:
    if "stage_type" not in payload:
        raise ValueError("StageEvent requires 'stage_type'")
    value = str(payload.get("stage_type", "")).strip()
    if not value:
        raise ValueError("StageEvent requires non-empty 'stage_type'")
    return value.lower()


@overload
def _ensure_dict(value: None, *, allow_none: Literal[True]) -> None: ...


@overload
def _ensure_dict(value: Any, *, allow_none: Literal[False] = False) -> dict[str, Any]: ...


def _ensure_dict(value: Any, *, allow_none: bool = False) -> dict[str, Any] | None:
    if value is None:
        return None if allow_none else {}
    if isinstance(value, dict):
        return value
    raise ValueError("Expected a dict for attributes/metadata/evidence")


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
