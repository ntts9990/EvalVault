from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass
class ConversationTurn:
    turn_id: str
    role: Literal["user", "assistant"]
    content: str
    contexts: list[str] | None = None
    ground_truth: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiTurnTestCase:
    conversation_id: str
    turns: list[ConversationTurn]
    expected_final_answer: str | None = None
    drift_tolerance: float = 0.1


@dataclass
class MultiTurnTurnResult:
    conversation_id: str
    turn_id: str
    turn_index: int | None
    role: Literal["user", "assistant"]
    metrics: dict[str, float] = field(default_factory=dict)
    passed: bool = False
    latency_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiTurnEvaluationResult:
    conversation_id: str
    turn_results: list[MultiTurnTurnResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass
class DriftAnalysis:
    conversation_id: str
    drift_score: float
    drift_threshold: float
    drift_detected: bool
    notes: list[str] = field(default_factory=list)


@dataclass
class MultiTurnRunRecord:
    run_id: str
    dataset_name: str
    dataset_version: str | None
    model_name: str | None
    started_at: datetime
    finished_at: datetime | None
    conversation_count: int
    turn_count: int
    metrics_evaluated: list[str] = field(default_factory=list)
    drift_threshold: float | None = None
    summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiTurnConversationRecord:
    run_id: str
    conversation_id: str
    turn_count: int
    drift_score: float | None = None
    drift_threshold: float | None = None
    drift_detected: bool = False
    summary: dict[str, Any] = field(default_factory=dict)
