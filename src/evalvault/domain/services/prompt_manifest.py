"""Helper utilities for tracking Phoenix prompt versions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import unified_diff
from hashlib import sha256
from pathlib import Path
from typing import TypedDict


class PromptRecord(TypedDict, total=False):
    phoenix_prompt_id: str
    phoenix_experiment_id: str | None
    checksum: str
    last_synced_at: str
    notes: str | None
    content: str


class PromptManifestDict(TypedDict, total=False):
    version: int
    updated_at: str
    prompts: dict[str, PromptRecord]


@dataclass
class PromptDiffSummary:
    """Summary of how the current prompt differs from the manifest."""

    path: str
    status: str
    phoenix_prompt_id: str | None = None
    phoenix_experiment_id: str | None = None
    previous_checksum: str | None = None
    current_checksum: str | None = None
    diff: str | None = None
    notes: str | None = None
    content_preview: str | None = None


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def normalize_prompt_path(path: Path) -> str:
    """Normalize a prompt path so manifest keys stay consistent."""

    try:
        return path.resolve().as_posix()
    except FileNotFoundError:
        return path.as_posix()


def load_prompt_manifest(path: Path) -> PromptManifestDict:
    """Load an existing manifest or return an empty structure."""

    if not path.exists():
        return PromptManifestDict(version=1, prompts={})

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Prompt manifest must be a JSON object")
    data.setdefault("version", 1)
    data.setdefault("prompts", {})
    return PromptManifestDict(
        version=int(data.get("version", 1)),
        updated_at=data.get("updated_at"),
        prompts=data.get("prompts", {}),
    )


def save_prompt_manifest(path: Path, manifest: PromptManifestDict) -> None:
    """Persist the manifest to disk."""

    manifest["version"] = int(manifest.get("version", 1))
    manifest["updated_at"] = _now_iso()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def _checksum(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def record_prompt_entry(
    manifest: PromptManifestDict,
    *,
    prompt_path: Path,
    content: str,
    phoenix_prompt_id: str,
    phoenix_experiment_id: str | None = None,
    notes: str | None = None,
) -> PromptRecord:
    """Store a prompt entry (content snapshot + Phoenix metadata)."""

    prompts = manifest.setdefault("prompts", {})
    key = normalize_prompt_path(prompt_path)
    record: PromptRecord = {
        "phoenix_prompt_id": phoenix_prompt_id,
        "phoenix_experiment_id": phoenix_experiment_id,
        "checksum": _checksum(content),
        "last_synced_at": _now_iso(),
        "notes": notes,
        "content": content,
    }
    prompts[key] = record
    manifest["updated_at"] = _now_iso()
    return record


def summarize_prompt_entry(
    manifest: PromptManifestDict | None,
    *,
    prompt_path: Path,
    content: str,
) -> PromptDiffSummary:
    """Summarize differences between manifest snapshot and the provided prompt."""

    normalized_path = normalize_prompt_path(prompt_path)
    record = (manifest or {}).get("prompts", {}).get(normalized_path) if manifest else None

    current_checksum = _checksum(content)
    if record is None:
        return PromptDiffSummary(
            path=normalized_path,
            status="untracked",
            current_checksum=current_checksum,
        )

    previous_checksum = record.get("checksum")
    notes = record.get("notes")
    diff_str = None
    status = "synced"
    if previous_checksum != current_checksum:
        status = "modified"
        previous_content = record.get("content", "")
        diff_lines = unified_diff(
            previous_content.splitlines(),
            content.splitlines(),
            fromfile="manifest",
            tofile="current",
            lineterm="",
        )
        diff_str = "\n".join(diff_lines)

    return PromptDiffSummary(
        path=normalized_path,
        status=status,
        phoenix_prompt_id=record.get("phoenix_prompt_id"),
        phoenix_experiment_id=record.get("phoenix_experiment_id"),
        previous_checksum=previous_checksum,
        current_checksum=current_checksum,
        diff=diff_str,
        notes=notes,
    )


def summarize_prompts(
    manifest: PromptManifestDict | None,
    *,
    prompt_paths: list[Path],
) -> list[PromptDiffSummary]:
    """Convenience wrapper that reads files and returns summaries."""

    summaries: list[PromptDiffSummary] = []
    for prompt_path in prompt_paths:
        try:
            content = prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            summaries.append(
                PromptDiffSummary(
                    path=normalize_prompt_path(prompt_path),
                    status="missing_file",
                )
            )
            continue
        summaries.append(
            summarize_prompt_entry(
                manifest,
                prompt_path=prompt_path,
                content=content,
            )
        )
    return summaries


__all__ = [
    "PromptDiffSummary",
    "PromptManifestDict",
    "record_prompt_entry",
    "normalize_prompt_path",
    "load_prompt_manifest",
    "save_prompt_manifest",
    "summarize_prompt_entry",
    "summarize_prompts",
]
