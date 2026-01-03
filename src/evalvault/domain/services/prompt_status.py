"""Formatting helpers for Phoenix prompt metadata surfaces."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal

PromptEntry = dict[str, Any]


def extract_prompt_entries(source: Any) -> list[PromptEntry]:
    """Normalize prompt metadata from tracker outputs or raw lists."""

    if source is None:
        return []

    prompts: Any = None
    if isinstance(source, list):
        prompts = source
    elif isinstance(source, dict):
        phoenix_meta = source.get("phoenix")
        if isinstance(phoenix_meta, dict):
            prompts = phoenix_meta.get("prompts")
        elif "prompts" in source:
            prompts = source.get("prompts")
        elif "path" in source and "status" in source:
            prompts = [source]

    if not isinstance(prompts, list):
        return []

    entries: list[PromptEntry] = []
    for entry in prompts:
        if isinstance(entry, dict):
            entries.append(entry)
    return entries


def summarize_prompt_counts(entries: Iterable[PromptEntry]) -> dict[str, int]:
    """Return aggregated counters for prompt statuses."""

    counts = Counter()
    total = 0
    for entry in entries:
        total += 1
        status = str(entry.get("status") or "unknown").lower()
        counts[status] += 1

    drift = counts.get("modified", 0) + counts.get("missing_file", 0)
    summary = {
        "total": total,
        "synced": counts.get("synced", 0),
        "drift": drift,
        "untracked": counts.get("untracked", 0),
        "missing": counts.get("missing_file", 0),
        "other": total
        - (
            counts.get("synced", 0)
            + counts.get("modified", 0)
            + counts.get("missing_file", 0)
            + counts.get("untracked", 0)
        ),
    }
    return summary


def format_prompt_summary_label(source: Any) -> str | None:
    """Short summary label (e.g., '3 files · 1 drift')."""

    entries = extract_prompt_entries(source)
    if not entries:
        return None

    summary = summarize_prompt_counts(entries)
    bits = [f"{summary['total']} files"]
    if summary["drift"]:
        bits.append(f"{summary['drift']} drift")
    if summary["untracked"]:
        bits.append(f"{summary['untracked']} untracked")
    return " · ".join(bits)


def format_prompt_section(
    source: Any,
    *,
    style: Literal["markdown", "plain", "slack"] = "markdown",
    max_diff_lines: int | None = 20,
    preview_lines: int | None = 6,
) -> str:
    """Human readable prompt status block for Markdown/Slack/plain text."""

    entries = extract_prompt_entries(source)
    if not entries:
        return ""

    lines: list[str] = []
    summary_label = format_prompt_summary_label(entries)
    if summary_label:
        prefix = _bullet(style)
        lines.append(f"{prefix}Prompt status: {summary_label}")

    for entry in entries:
        lines.extend(_format_entry(entry, style, max_diff_lines, preview_lines))

    return "\n".join(line for line in lines if line).strip()


def _format_entry(
    entry: PromptEntry,
    style: Literal["markdown", "plain", "slack"],
    max_diff_lines: int | None,
    preview_lines: int | None,
) -> list[str]:
    path = str(entry.get("path") or "prompt")
    short_path = Path(path).name or path
    status = str(entry.get("status") or "unknown")
    status_lower = status.lower()

    prompt_id = entry.get("phoenix_prompt_id")
    experiment_id = entry.get("phoenix_experiment_id")
    notes = entry.get("notes")
    checksum = entry.get("current_checksum")
    previous = entry.get("previous_checksum")
    diff = entry.get("diff")

    label_prefix = _bullet(style)
    path_label = _emphasize(style, short_path)
    detail_bits: list[str] = []
    if prompt_id:
        detail_bits.append(f"Prompt {prompt_id}")
    if experiment_id:
        detail_bits.append(f"Exp {experiment_id}")
    if checksum:
        detail_bits.append(f"checksum {checksum[:8]}")
    if previous and previous != checksum:
        detail_bits.append(f"prev {previous[:8]}")

    detail_suffix = f" ({', '.join(detail_bits)})" if detail_bits else ""
    lines = [f"{label_prefix}{path_label} — {status}{detail_suffix}"]

    if notes:
        lines.append(_indent(style, f"Notes: {notes}"))

    if diff:
        trimmed = _trim_diff(diff, max_diff_lines)
        if trimmed:
            lines.append(_code_block(style, trimmed, language="diff"))

    preview = entry.get("content_preview")
    if (
        preview
        and preview_lines
        and preview_lines > 0
        and status_lower not in {"synced", "unknown"}
    ):
        trimmed_preview = _trim_preview(str(preview), preview_lines)
        if trimmed_preview:
            lines.append(_code_block(style, trimmed_preview, language="text"))

    return lines


def _bullet(style: Literal["markdown", "plain", "slack"]) -> str:
    if style == "slack":
        return "• "
    if style == "plain":
        return "- "
    return "- "


def _emphasize(style: Literal["markdown", "plain", "slack"], text: str) -> str:
    if style == "markdown":
        return f"**{text}**"
    if style == "slack":
        return f"*{text}*"
    return text


def _indent(style: Literal["markdown", "plain", "slack"], text: str) -> str:
    if style == "slack":
        return f"    • {text}"
    if style == "markdown":
        return f"    - {text}"
    return f"    {text}"


def _code_block(
    style: Literal["markdown", "plain", "slack"], content: str, *, language: str = ""
) -> str:
    if style in {"markdown", "slack"}:
        fence = "```"
        lang = language or ""
        header = f"{fence}{lang}" if lang else fence
        return "\n".join([header, content, fence])
    # plain text fallback
    indented = "\n".join(f"    {line}" for line in content.splitlines())
    return indented


def _trim_diff(diff: str, max_lines: int | None) -> str:
    if not diff:
        return ""
    if max_lines is None or max_lines <= 0:
        return diff
    lines = diff.splitlines()
    if len(lines) <= max_lines:
        return diff
    remaining = len(lines) - max_lines
    trimmed = lines[:max_lines]
    trimmed.append(f"... (+{remaining} lines)")
    return "\n".join(trimmed)


def _trim_preview(content: str, max_lines: int) -> str:
    lines = content.splitlines()
    if len(lines) <= max_lines:
        return content
    remaining = len(lines) - max_lines
    trimmed = lines[:max_lines]
    trimmed.append(f"... (+{remaining} lines)")
    return "\n".join(trimmed)


__all__ = [
    "extract_prompt_entries",
    "format_prompt_section",
    "format_prompt_summary_label",
    "summarize_prompt_counts",
]
