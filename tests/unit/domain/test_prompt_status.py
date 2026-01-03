"""Tests for prompt status formatting helpers."""

from evalvault.domain.services.prompt_status import (
    extract_prompt_entries,
    format_prompt_section,
    format_prompt_summary_label,
)

SAMPLE_PROMPTS = [
    {
        "path": "/tmp/baseline.txt",
        "status": "modified",
        "phoenix_prompt_id": "pr-1",
        "phoenix_experiment_id": "exp-9",
        "current_checksum": "abcdef123456",
        "previous_checksum": "fff000999888",
        "notes": "Refined instructions",
        "diff": "- hi\n+ hello",
        "content_preview": "line1\nline2\nline3\nline4\nline5\nline6\nline7",
    }
]


def test_format_prompt_summary_label_counts() -> None:
    summary = format_prompt_summary_label(SAMPLE_PROMPTS)

    assert summary is not None
    assert "1 files" in summary
    assert "1 drift" in summary


def test_extract_prompt_entries_from_metadata() -> None:
    metadata = {"phoenix": {"prompts": SAMPLE_PROMPTS}}
    entries = extract_prompt_entries(metadata)

    assert len(entries) == 1
    assert entries[0]["path"].endswith("baseline.txt")


def test_format_prompt_section_includes_details() -> None:
    section = format_prompt_section(
        SAMPLE_PROMPTS,
        style="markdown",
        max_diff_lines=1,
        preview_lines=3,
    )

    assert "Prompt status" in section
    assert "**baseline.txt**" in section
    assert "checksum" in section
    assert "... (+1 lines)" in section
    assert "```text" in section
    assert "... (+4 lines)" in section


def test_format_prompt_section_empty() -> None:
    assert format_prompt_section([], style="markdown") == ""
