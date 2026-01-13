"""Prompt set helpers for storing system/Ragas prompt snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Any

from evalvault.domain.entities.prompt import (
    Prompt,
    PromptKind,
    PromptSet,
    PromptSetBundle,
    PromptSetItem,
)


@dataclass(frozen=True)
class PromptInput:
    """Normalized prompt input for building prompt sets."""

    content: str
    name: str
    kind: PromptKind
    role: str
    source: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None


def compute_prompt_checksum(content: str) -> str:
    """Compute a stable checksum for prompt content."""

    return sha256(content.encode("utf-8")).hexdigest()


def build_prompt_bundle(
    *,
    run_id: str,
    prompt_set_name: str | None,
    prompt_set_description: str | None,
    prompt_inputs: list[PromptInput],
    metadata: dict[str, Any] | None = None,
) -> PromptSetBundle | None:
    """Create a PromptSetBundle from normalized inputs."""

    if not prompt_inputs:
        return None

    prompt_set = PromptSet(
        name=prompt_set_name or f"run-{run_id[:8]}",
        description=prompt_set_description or "",
        metadata=metadata or {},
        created_at=datetime.now(),
    )

    prompts: list[Prompt] = []
    items: list[PromptSetItem] = []
    for index, entry in enumerate(prompt_inputs):
        checksum = compute_prompt_checksum(entry.content)
        prompt = Prompt(
            name=entry.name,
            kind=entry.kind,
            content=entry.content,
            checksum=checksum,
            source=entry.source,
            notes=entry.notes,
            metadata=entry.metadata or {},
        )
        prompts.append(prompt)
        items.append(
            PromptSetItem(
                prompt_set_id=prompt_set.prompt_set_id,
                prompt_id=prompt.prompt_id,
                role=entry.role,
                item_order=index,
                metadata={},
            )
        )

    return PromptSetBundle(prompt_set=prompt_set, prompts=prompts, items=items)


def build_prompt_summary(bundle: PromptSetBundle) -> dict[str, Any]:
    """Build a compact summary for tracker metadata."""

    summary: dict[str, Any] = {
        "prompt_set_id": bundle.prompt_set.prompt_set_id,
        "prompt_set_name": bundle.prompt_set.name,
    }
    system_checksum: str | None = None
    ragas_checksums: dict[str, str] = {}
    prompt_map = {prompt.prompt_id: prompt for prompt in bundle.prompts}
    for item in bundle.items:
        prompt = prompt_map.get(item.prompt_id)
        if not prompt:
            continue
        if prompt.kind == "system":
            system_checksum = prompt.checksum
        elif prompt.kind == "ragas":
            ragas_checksums[item.role] = prompt.checksum
    if system_checksum:
        summary["system_prompt_checksum"] = system_checksum
    if ragas_checksums:
        summary["ragas_prompt_checksums"] = ragas_checksums
    return summary


def build_prompt_inputs_from_snapshots(
    snapshots: dict[str, dict[str, Any]] | None,
) -> list[PromptInput]:
    if not snapshots:
        return []
    prompt_inputs: list[PromptInput] = []
    for metric_name, entry in snapshots.items():
        prompt_text = entry.get("prompt") if isinstance(entry, dict) else None
        if not isinstance(prompt_text, str):
            continue
        prompt_text = prompt_text.strip()
        if not prompt_text:
            continue
        source = entry.get("source") if isinstance(entry, dict) else None
        metadata = {
            key: value
            for key, value in entry.items()
            if key != "prompt" and isinstance(entry, dict)
        }
        prompt_inputs.append(
            PromptInput(
                content=prompt_text,
                name=f"ragas.{metric_name}",
                kind="ragas",
                role=str(metric_name),
                source=source if isinstance(source, str) and source else "ragas",
                metadata=metadata or None,
            )
        )
    return prompt_inputs
