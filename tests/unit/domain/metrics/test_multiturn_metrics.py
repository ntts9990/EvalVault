from __future__ import annotations

from typing import Literal

from evalvault.domain.entities.multiturn import ConversationTurn, MultiTurnTurnResult
from evalvault.domain.metrics.multiturn_metrics import (
    calculate_context_coherence,
    calculate_drift_rate,
    calculate_turn_faithfulness,
    calculate_turn_latency_p95,
)


def _turn(
    role: Literal["user", "assistant"],
    content: str,
    *,
    turn_id: str = "t01",
    contexts: list[str] | None = None,
) -> ConversationTurn:
    return ConversationTurn(
        turn_id=turn_id,
        role=role,
        content=content,
        contexts=contexts,
    )


def test_turn_faithfulness_empty_results():
    assert calculate_turn_faithfulness([]) == 0.0


def test_turn_faithfulness_single_value():
    result = MultiTurnTurnResult(
        conversation_id="c1",
        turn_id="t1",
        turn_index=1,
        role="assistant",
        metrics={"faithfulness": 0.8},
    )
    assert calculate_turn_faithfulness([result]) == 0.8


def test_turn_faithfulness_ignores_missing_metric():
    result = MultiTurnTurnResult(
        conversation_id="c1",
        turn_id="t1",
        turn_index=1,
        role="assistant",
        metrics={},
    )
    assert calculate_turn_faithfulness([result]) == 0.0


def test_turn_faithfulness_multiple_values_average():
    results = [
        MultiTurnTurnResult(
            conversation_id="c1",
            turn_id="t1",
            turn_index=1,
            role="assistant",
            metrics={"faithfulness": 0.6},
        ),
        MultiTurnTurnResult(
            conversation_id="c1",
            turn_id="t2",
            turn_index=2,
            role="assistant",
            metrics={"faithfulness": 0.8},
        ),
    ]
    assert calculate_turn_faithfulness(results) == 0.7


def test_context_coherence_single_turn_defaults_to_one():
    turn = _turn("assistant", "A", turn_id="t1", contexts=["alpha"])
    assert calculate_context_coherence([turn]) == 1.0


def test_context_coherence_identical_contexts():
    turns = [
        _turn("assistant", "A", turn_id="t1", contexts=["same context"]),
        _turn("assistant", "B", turn_id="t2", contexts=["same context"]),
    ]
    assert calculate_context_coherence(turns) == 1.0


def test_context_coherence_disjoint_contexts():
    turns = [
        _turn("assistant", "A", turn_id="t1", contexts=["alpha"]),
        _turn("assistant", "B", turn_id="t2", contexts=["beta"]),
    ]
    assert calculate_context_coherence(turns) == 0.0


def test_context_coherence_uses_content_when_contexts_missing():
    turns = [
        _turn("assistant", "hello world", turn_id="t1", contexts=None),
        _turn("assistant", "hello there", turn_id="t2", contexts=None),
    ]
    score = calculate_context_coherence(turns)
    assert score > 0.0


def test_context_coherence_uses_content_when_contexts_empty_list():
    turns = [
        _turn("assistant", "plan a coverage", turn_id="t1", contexts=[]),
        _turn("assistant", "plan a coverage", turn_id="t2", contexts=[]),
    ]
    assert calculate_context_coherence(turns) == 1.0


def test_context_coherence_partial_overlap():
    turns = [
        _turn("assistant", "A", turn_id="t1", contexts=["plan a coverage"]),
        _turn("assistant", "B", turn_id="t2", contexts=["plan a premium"]),
    ]
    assert calculate_context_coherence(turns) == 0.5


def test_context_coherence_filters_empty_contexts():
    turns = [
        _turn("assistant", "A", turn_id="t1", contexts=["", "plan a coverage"]),
        _turn("assistant", "B", turn_id="t2", contexts=["plan a coverage"]),
    ]
    assert calculate_context_coherence(turns) == 1.0


def test_context_coherence_mixed_context_and_content():
    turns = [
        _turn("assistant", "A", turn_id="t1", contexts=["plan a coverage"]),
        _turn("assistant", "plan a coverage", turn_id="t2", contexts=None),
    ]
    assert calculate_context_coherence(turns) == 1.0


def test_context_coherence_empty_turns_defaults_to_one():
    assert calculate_context_coherence([]) == 1.0


def test_drift_rate_empty_turns():
    assert calculate_drift_rate([]) == 0.0


def test_drift_rate_missing_assistant_turn():
    turns = [_turn("user", "question", turn_id="t1")]
    assert calculate_drift_rate(turns) == 0.0


def test_drift_rate_missing_user_turn():
    turns = [_turn("assistant", "answer", turn_id="t1")]
    assert calculate_drift_rate(turns) == 0.0


def test_drift_rate_identical_intent_response():
    turns = [
        _turn("user", "coverage limit", turn_id="t1"),
        _turn("assistant", "coverage limit", turn_id="t2"),
    ]
    assert calculate_drift_rate(turns) == 0.0


def test_drift_rate_full_drift():
    turns = [
        _turn("user", "coverage limit", turn_id="t1"),
        _turn("assistant", "weather today", turn_id="t2"),
    ]
    assert calculate_drift_rate(turns) == 1.0


def test_drift_rate_partial_overlap():
    turns = [
        _turn("user", "coverage limit plan a", turn_id="t1"),
        _turn("assistant", "coverage limit plan b", turn_id="t2"),
    ]
    assert calculate_drift_rate(turns) == 0.4


def test_drift_rate_uses_last_assistant():
    turns = [
        _turn("user", "coverage limit", turn_id="t1"),
        _turn("assistant", "coverage limit", turn_id="t2"),
        _turn("user", "still about coverage", turn_id="t3"),
        _turn("assistant", "weather today", turn_id="t4"),
    ]
    assert calculate_drift_rate(turns) == 1.0


def test_turn_latency_p95_empty():
    assert calculate_turn_latency_p95([]) == 0.0


def test_turn_latency_p95_single_value():
    assert calculate_turn_latency_p95([120]) == 120.0


def test_turn_latency_p95_two_values():
    assert calculate_turn_latency_p95([100, 200]) == 195.0


def test_turn_latency_p95_ignores_none():
    assert calculate_turn_latency_p95([None, 300, None]) == 300.0


def test_turn_latency_p95_multiple_values():
    assert calculate_turn_latency_p95([100, 200, 300, 400, 500]) == 480.0


def test_turn_latency_p95_unsorted_values():
    assert calculate_turn_latency_p95([300, 100, 200]) == 290.0


def test_turn_latency_p95_with_none_values():
    assert calculate_turn_latency_p95([None, 100, None, 200, 300]) == 290.0
