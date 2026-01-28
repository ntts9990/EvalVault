"""
Utilities for multi-turn evaluation metrics.

Metrics:
- turn_faithfulness: average per-turn faithfulness
- context_coherence: coherence across turn contexts
- drift_rate: distance between initial intent and final response
- turn_latency: p95 latency across turns
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Iterable

from evalvault.domain.entities.multiturn import ConversationTurn, MultiTurnTurnResult


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokenize(text: str) -> set[str]:
    if not text:
        return set()
    text = _normalize_text(text)
    tokens = re.findall(r"[\w가-힣]+", text)
    return set(tokens)


def _jaccard_similarity(left: str, right: str) -> float:
    left_tokens = _tokenize(left)
    right_tokens = _tokenize(right)
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    intersection = left_tokens.intersection(right_tokens)
    union = left_tokens.union(right_tokens)
    if not union:
        return 0.0
    return len(intersection) / len(union)


def _turn_context_text(turn: ConversationTurn) -> str:
    if turn.contexts:
        return " ".join([ctx for ctx in turn.contexts if ctx])
    return turn.content or ""


def calculate_turn_faithfulness(turn_results: Iterable[MultiTurnTurnResult]) -> float:
    scores: list[float] = []
    for result in turn_results:
        score = result.metrics.get("faithfulness") if result.metrics else None
        if score is not None:
            scores.append(score)
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def calculate_context_coherence(turns: Iterable[ConversationTurn]) -> float:
    turn_list = list(turns)
    if len(turn_list) < 2:
        return 1.0
    scores: list[float] = []
    for prev, curr in zip(turn_list, turn_list[1:], strict=False):
        left = _turn_context_text(prev)
        right = _turn_context_text(curr)
        scores.append(_jaccard_similarity(left, right))
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def calculate_drift_rate(turns: Iterable[ConversationTurn]) -> float:
    turn_list = list(turns)
    if not turn_list:
        return 0.0
    first_user = next((t for t in turn_list if t.role == "user"), None)
    last_assistant = next((t for t in reversed(turn_list) if t.role == "assistant"), None)
    if not first_user or not last_assistant:
        return 0.0
    similarity = _jaccard_similarity(first_user.content, last_assistant.content)
    drift = 1.0 - similarity
    if drift < 0.0:
        return 0.0
    if drift > 1.0:
        return 1.0
    return drift


def calculate_turn_latency_p95(latencies_ms: Iterable[int | None]) -> float:
    values = [float(value) for value in latencies_ms if value is not None]
    if not values:
        return 0.0
    values.sort()
    if len(values) == 1:
        return values[0]
    rank = 0.95 * (len(values) - 1)
    lower = int(math.floor(rank))
    upper = int(math.ceil(rank))
    if lower == upper:
        return values[lower]
    fraction = rank - lower
    return values[lower] + (values[upper] - values[lower]) * fraction
