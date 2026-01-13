"""Prompt suggestion entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PromptCandidate:
    """Single prompt candidate for suggestion workflow."""

    candidate_id: str
    source: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PromptCandidateSampleScore:
    sample_index: int
    scores: dict[str, float]
    weighted_score: float
    responses: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class PromptCandidateScore:
    """Evaluation score for a prompt candidate."""

    candidate_id: str
    scores: dict[str, float]
    weighted_score: float
    sample_scores: list[PromptCandidateSampleScore] = field(default_factory=list)
    selected_sample_index: int | None = None


@dataclass(frozen=True)
class PromptSuggestionResult:
    """Aggregated prompt suggestion results."""

    run_id: str
    role: str
    metrics: list[str]
    weights: dict[str, float]
    candidates: list[PromptCandidate]
    scores: list[PromptCandidateScore]
    ranking: list[str]
    holdout_ratio: float
    metadata: dict[str, Any] = field(default_factory=dict)
