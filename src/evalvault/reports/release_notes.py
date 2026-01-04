"""Utility helpers for building EvalVault release notes."""

from __future__ import annotations

from typing import Any, Literal

from evalvault.config.phoenix_support import format_phoenix_links
from evalvault.domain.services.prompt_status import (
    format_prompt_section,
    format_prompt_summary_label,
)

Style = Literal["markdown", "plain", "slack"]


def _format_percentage(value: Any) -> str:
    if isinstance(value, int | float):
        return f"{value:.1%}"
    return "N/A"


def _format_float(value: Any) -> str:
    if isinstance(value, int | float):
        return f"{value:.3f}"
    return "N/A"


def build_release_notes(
    summary: dict[str, Any],
    *,
    style: Style = "markdown",
    max_failures: int = 5,
    prompt_diff_lines: int = 20,
) -> str:
    """Create Markdown/Slack release notes from an EvalVault summary JSON."""

    dataset = summary.get("dataset_name") or "unknown"
    dataset_version = summary.get("dataset_version") or "N/A"
    model = summary.get("model_name") or "unknown"
    total_cases = summary.get("total_test_cases") or 0
    passed_cases = summary.get("passed_test_cases") or 0
    pass_rate = summary.get("pass_rate")

    bullet = "• " if style == "slack" else "- "
    lines: list[str] = [
        f"# EvalVault Release Summary — {dataset} ({model})",
        "",
        "## Overview",
        f"{bullet}Dataset: `{dataset}` v{dataset_version}",
        f"{bullet}Model: `{model}`",
        f"{bullet}Pass Rate: {_format_percentage(pass_rate)} ({passed_cases}/{total_cases})",
        "",
    ]

    metric_rows = []
    for key, value in sorted(summary.items()):
        if key.startswith("avg_"):
            metric_name = key.replace("avg_", "", 1)
            metric_rows.append(f"{bullet}{metric_name}: {_format_float(value)}")
    if metric_rows:
        lines.extend(["## Metric Averages", *metric_rows, ""])

    results = summary.get("results") or []
    failures = [item for item in results if not item.get("all_passed")]
    if failures:
        lines.append("## Notable Failures")
        limit = max(1, max_failures)
        for test_case in failures[:limit]:
            tc_id = test_case.get("test_case_id", "unknown")
            metric_bits = []
            for metric in test_case.get("metrics", []):
                name = metric.get("name", "metric")
                score = metric.get("score")
                threshold = metric.get("threshold")
                metric_bits.append(
                    f"{name} {score:.2f}/{threshold:.2f}"
                    if isinstance(score, int | float) and isinstance(threshold, int | float)
                    else f"{name}"
                )
            metric_summary = ", ".join(metric_bits) if metric_bits else "metric details unavailable"
            lines.append(f"{bullet}`{tc_id}` — {metric_summary}")
        remaining = len(failures) - limit
        if remaining > 0:
            lines.append(f"{bullet}+{remaining} additional failing cases")
        lines.append("")

    prompt_source = summary.get("tracker_metadata") or summary.get("phoenix_prompts")
    prompt_summary_label = format_prompt_summary_label(prompt_source)
    prompt_section = format_prompt_section(
        prompt_source,
        style=style,
        max_diff_lines=prompt_diff_lines,
    )
    phoenix_section = format_phoenix_links(summary.get("tracker_metadata"), style=style)
    observability_block: list[str] = []
    if phoenix_section:
        observability_block.append(phoenix_section)
    if prompt_summary_label:
        observability_block.append(f"{bullet}Prompt Summary: {prompt_summary_label}")
    if prompt_section:
        if observability_block and not prompt_section.startswith("#"):
            observability_block.append("")
        observability_block.append(prompt_section)
    if observability_block:
        lines.extend(["## Phoenix & Prompt Loop", *observability_block, ""])

    return "\n".join([line.rstrip() for line in lines if line is not None]).strip() + "\n"
