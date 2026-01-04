"""Render debug reports to Markdown or JSON."""

from __future__ import annotations

import json
from typing import Any

from evalvault.domain.entities.debug import DebugReport
from evalvault.domain.entities.stage import StageMetric, StageSummary


def render_markdown(report: DebugReport) -> str:
    lines: list[str] = []
    lines.append("# Debug Report")
    lines.append("")
    lines.extend(
        _render_run_summary(
            report.run_summary,
            report.phoenix_trace_url,
            report.langfuse_trace_url,
        )
    )
    lines.append("")
    lines.extend(_render_stage_summary(report.stage_summary))
    lines.append("")
    lines.extend(_render_bottlenecks(report.bottlenecks))
    lines.append("")
    lines.extend(_render_recommendations(report.recommendations))
    lines.append("")
    lines.extend(_render_failing_metrics(report.stage_metrics))
    return "\n".join(lines).strip()


def render_json(report: DebugReport) -> str:
    payload = report.to_dict()
    return json.dumps(payload, ensure_ascii=True, indent=2)


def _render_run_summary(
    summary: dict[str, Any],
    phoenix_trace_url: str | None,
    langfuse_trace_url: str | None,
) -> list[str]:
    run_id = summary.get("run_id", "-")
    dataset = summary.get("dataset_name", "-")
    version = summary.get("dataset_version", "-")
    model = summary.get("model_name", "-")
    started = summary.get("started_at", "-")
    finished = summary.get("finished_at", "-")
    duration = summary.get("duration_seconds", "-")
    total_cases = summary.get("total_test_cases", "-")
    pass_rate = summary.get("pass_rate", "-")
    total_tokens = summary.get("total_tokens", "-")
    total_cost = summary.get("total_cost_usd", "-")

    lines = [
        "## Run Summary",
        f"- run_id: {run_id}",
        f"- dataset: {dataset} ({version})",
        f"- model: {model}",
        f"- started_at: {started}",
        f"- finished_at: {finished}",
        f"- duration_seconds: {duration}",
        f"- total_test_cases: {total_cases}",
        f"- pass_rate: {pass_rate}",
        f"- total_tokens: {total_tokens}",
        f"- total_cost_usd: {total_cost}",
    ]
    trace_links: list[str] = []
    if langfuse_trace_url:
        trace_links.append(f"langfuse_trace_url={langfuse_trace_url}")
    if phoenix_trace_url:
        trace_links.append(f"phoenix_trace_url={phoenix_trace_url}")
    if trace_links:
        lines.append(f"- trace_links: {', '.join(trace_links)}")
    return lines


def _render_stage_summary(summary: StageSummary | None) -> list[str]:
    lines = ["## Stage Summary"]
    if summary is None:
        lines.append("- no stage events found")
        return lines
    lines.append(f"- total_events: {summary.total_events}")
    if summary.missing_required_stage_types:
        missing = ", ".join(summary.missing_required_stage_types)
        lines.append(f"- missing_required_stage_types: {missing}")
    if summary.stage_type_counts:
        lines.append("- stage_type_counts:")
        for stage_type, count in summary.stage_type_counts.items():
            lines.append(f"  - {stage_type}: {count}")
    if summary.stage_type_avg_durations:
        lines.append("- stage_type_avg_durations_ms:")
        for stage_type, duration in summary.stage_type_avg_durations.items():
            lines.append(f"  - {stage_type}: {duration:.3f}")
    return lines


def _render_bottlenecks(bottlenecks: list[dict[str, Any]]) -> list[str]:
    lines = ["## Bottlenecks"]
    if not bottlenecks:
        lines.append("- none")
        return lines
    for entry in bottlenecks:
        entry_type = entry.get("type", "unknown")
        if entry_type == "latency":
            stage_type = entry.get("stage_type", "-")
            duration = entry.get("avg_duration_ms", "-")
            lines.append(f"- latency: {stage_type} avg_duration_ms={duration}")
        elif entry_type == "missing_stage":
            stage_type = entry.get("stage_type", "-")
            lines.append(f"- missing_stage: {stage_type}")
        else:
            lines.append(f"- {entry_type}: {entry}")
    return lines


def _render_recommendations(recommendations: list[str]) -> list[str]:
    lines = ["## Recommendations"]
    if not recommendations:
        lines.append("- none")
        return lines
    for item in recommendations:
        lines.append(f"- {item}")
    return lines


def _render_failing_metrics(metrics: list[StageMetric]) -> list[str]:
    lines = ["## Failing Stage Metrics"]
    failing = [metric for metric in metrics if metric.passed is False]
    if not failing:
        lines.append("- none")
        return lines

    failing_sorted = sorted(failing, key=_metric_severity, reverse=True)[:20]
    for metric in failing_sorted:
        threshold = metric.threshold if metric.threshold is not None else "-"
        lines.append(
            f"- {metric.metric_name}: score={metric.score} threshold={threshold} "
            f"stage_id={metric.stage_id}"
        )
    return lines


def _metric_severity(metric: StageMetric) -> float:
    if metric.threshold is None:
        return 0.0
    comparison = None
    if isinstance(metric.evidence, dict):
        comparison = metric.evidence.get("comparison")
    if isinstance(comparison, str) and comparison.lower() in {"max", "<=", "le"}:
        return max(metric.score - metric.threshold, 0.0)
    return max(metric.threshold - metric.score, 0.0)
