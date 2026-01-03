"""Tests for prompt manifest helpers."""

from __future__ import annotations

from evalvault.domain.services.prompt_manifest import (
    PromptManifestDict,
    load_prompt_manifest,
    record_prompt_entry,
    save_prompt_manifest,
    summarize_prompt_entry,
    summarize_prompts,
)


def test_load_prompt_manifest_returns_empty_structure(tmp_path):
    manifest_path = tmp_path / "prompt_manifest.json"

    manifest = load_prompt_manifest(manifest_path)

    assert manifest["version"] == 1
    assert manifest["prompts"] == {}


def test_record_and_summarize_prompt(tmp_path):
    manifest_path = tmp_path / "prompt_manifest.json"
    manifest = PromptManifestDict(version=1, prompts={})
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("Hello Phoenix", encoding="utf-8")

    record_prompt_entry(
        manifest,
        prompt_path=prompt_file,
        content=prompt_file.read_text(encoding="utf-8"),
        phoenix_prompt_id="prompt-1",
        phoenix_experiment_id="exp-1",
        notes="baseline",
    )
    save_prompt_manifest(manifest_path, manifest)

    loaded = load_prompt_manifest(manifest_path)
    summary = summarize_prompt_entry(
        loaded,
        prompt_path=prompt_file,
        content=prompt_file.read_text(encoding="utf-8"),
    )

    assert summary.status == "synced"
    assert summary.phoenix_prompt_id == "prompt-1"
    assert summary.notes == "baseline"


def test_summarize_prompts_detects_changes_and_missing(tmp_path):
    manifest = PromptManifestDict(version=1, prompts={})
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("Initial prompt", encoding="utf-8")

    record_prompt_entry(
        manifest,
        prompt_path=prompt_file,
        content=prompt_file.read_text(encoding="utf-8"),
        phoenix_prompt_id="prompt-123",
    )

    # Modify the prompt to force a diff
    prompt_file.write_text("Changed prompt", encoding="utf-8")
    missing_prompt = tmp_path / "missing_prompt.txt"

    summaries = summarize_prompts(manifest, prompt_paths=[prompt_file, missing_prompt])

    assert summaries[0].status == "modified"
    assert summaries[0].diff
    assert summaries[1].status == "missing_file"
