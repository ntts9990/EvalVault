from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evalvault.domain.entities.multiturn import ConversationTurn, MultiTurnTestCase


@dataclass(frozen=True)
class MultiTurnDataset:
    name: str
    version: str
    test_cases: list[MultiTurnTestCase]
    metadata: dict[str, Any]
    source_file: str | None = None


def load_multiturn_dataset(file_path: str | Path) -> MultiTurnDataset:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    name = path.stem
    version = "1.0.0"
    metadata: dict[str, Any] = {}
    raw_cases: list[dict[str, Any]]

    if isinstance(payload, list):
        raw_cases = payload
    elif isinstance(payload, dict):
        name = str(payload.get("name") or name)
        version = str(payload.get("version") or version)
        metadata = payload.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a JSON object")
        raw_cases = payload.get("test_cases") or payload.get("conversations") or []
    else:
        raise ValueError("JSON must be an array or object with 'test_cases' key")

    if not isinstance(raw_cases, list):
        raise ValueError("test_cases must be a list")

    test_cases: list[MultiTurnTestCase] = []
    for idx, raw_case in enumerate(raw_cases, start=1):
        if not isinstance(raw_case, dict):
            raise ValueError(f"test_cases[{idx}] must be an object")
        conversation_id = raw_case.get("conversation_id") or raw_case.get("id")
        if not conversation_id:
            raise ValueError(f"test_cases[{idx}] missing conversation_id")
        raw_turns = raw_case.get("turns")
        if not isinstance(raw_turns, list) or not raw_turns:
            raise ValueError(f"test_cases[{idx}] missing turns list")

        turns: list[ConversationTurn] = []
        for t_idx, raw_turn in enumerate(raw_turns, start=1):
            if not isinstance(raw_turn, dict):
                raise ValueError(f"turns[{t_idx}] must be an object")
            role = raw_turn.get("role")
            if role not in {"user", "assistant"}:
                raise ValueError(f"turns[{t_idx}] role must be 'user' or 'assistant'")
            content = raw_turn.get("content")
            if content is None:
                raise ValueError(f"turns[{t_idx}] missing content")
            turn_id = raw_turn.get("turn_id") or f"t{t_idx:02d}"
            contexts = raw_turn.get("contexts")
            if contexts is None:
                contexts = []
            if isinstance(contexts, str):
                contexts = [contexts]
            if not isinstance(contexts, list):
                raise ValueError(f"turns[{t_idx}] contexts must be a list")
            ground_truth = raw_turn.get("ground_truth")
            metadata_value = raw_turn.get("metadata") or {}
            if not isinstance(metadata_value, dict):
                raise ValueError(f"turns[{t_idx}] metadata must be an object")
            turns.append(
                ConversationTurn(
                    turn_id=str(turn_id),
                    role=role,
                    content=str(content),
                    contexts=[str(ctx) for ctx in contexts],
                    ground_truth=ground_truth,
                    metadata=metadata_value,
                )
            )

        test_cases.append(
            MultiTurnTestCase(
                conversation_id=str(conversation_id),
                turns=turns,
                expected_final_answer=raw_case.get("expected_final_answer"),
                drift_tolerance=float(raw_case.get("drift_tolerance", 0.1)),
            )
        )

    return MultiTurnDataset(
        name=name,
        version=version,
        test_cases=test_cases,
        metadata=metadata,
        source_file=str(path),
    )
