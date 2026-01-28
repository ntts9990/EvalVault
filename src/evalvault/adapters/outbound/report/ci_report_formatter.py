from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CIGateMetricRow:
    metric: str
    baseline_score: float
    current_score: float
    change_percent: float
    status: str


def format_ci_regression_report(
    rows: list[CIGateMetricRow],
    *,
    regression_rate: float,
    regression_threshold: float,
    gate_passed: bool,
) -> str:
    lines: list[str] = ["## RAG Regression Gate Results", ""]
    lines.append("| Metric | Baseline | Current | Change | Status |")
    lines.append("|--------|----------|---------|--------|--------|")
    for row in rows:
        change = f"{row.change_percent:+.1f}%"
        lines.append(
            f"| {row.metric} | {row.baseline_score:.3f} | {row.current_score:.3f} | {change} | {row.status} |"
        )
    lines.append("")
    if gate_passed:
        status_line = "✅ PASSED"
        comparison = "<"
    else:
        status_line = "❌ FAILED"
        comparison = ">="
    lines.append(
        f"**Gate Status**: {status_line} (regression: {regression_rate:.1%} {comparison} {regression_threshold:.1%} threshold)"
    )
    return "\n".join(lines).strip()


__all__ = ["CIGateMetricRow", "format_ci_regression_report"]
