"""Prompt entities for tracking system and Ragas prompts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

PromptKind = Literal["system", "ragas", "custom"]


@dataclass
class Prompt:
    """Stored prompt content with metadata."""

    prompt_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    kind: PromptKind = "system"
    content: str = ""
    checksum: str = ""
    source: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PromptSet:
    """A named collection of prompts used for an evaluation."""

    prompt_set_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PromptSetItem:
    """Join between prompt sets and prompts."""

    prompt_set_id: str
    prompt_id: str
    role: str
    item_order: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptSetBundle:
    """Convenience container for prompt set storage."""

    prompt_set: PromptSet
    prompts: list[Prompt] = field(default_factory=list)
    items: list[PromptSetItem] = field(default_factory=list)

    def to_dict(self, *, include_content: bool = True) -> dict[str, Any]:
        """Serialize prompt set details for API/UI usage."""

        prompt_map = {prompt.prompt_id: prompt for prompt in self.prompts}
        items = []
        for item in self.items:
            prompt = prompt_map.get(item.prompt_id)
            if not prompt:
                continue
            prompt_payload = {
                "prompt_id": prompt.prompt_id,
                "name": prompt.name,
                "kind": prompt.kind,
                "checksum": prompt.checksum,
                "source": prompt.source,
                "notes": prompt.notes,
                "metadata": prompt.metadata,
                "created_at": prompt.created_at.isoformat(),
            }
            if include_content:
                prompt_payload["content"] = prompt.content
            items.append(
                {
                    "role": item.role,
                    "order": item.item_order,
                    "metadata": item.metadata,
                    "prompt": prompt_payload,
                }
            )

        return {
            "prompt_set_id": self.prompt_set.prompt_set_id,
            "name": self.prompt_set.name,
            "description": self.prompt_set.description,
            "metadata": self.prompt_set.metadata,
            "created_at": self.prompt_set.created_at.isoformat(),
            "items": items,
        }
