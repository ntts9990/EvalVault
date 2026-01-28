from __future__ import annotations

from evalvault.adapters.outbound.report.ci_report_formatter import CIGateMetricRow


def format_ci_gate_pr_comment(
    rows: list[CIGateMetricRow],
    *,
    baseline_run_id: str,
    current_run_id: str,
    regression_rate: float,
    regression_threshold: float,
    gate_passed: bool,
    threshold_failures: list[str],
    regressed_metrics: list[str],
) -> str:
    lines: list[str] = ["## EvalVault CI Gate", ""]
    lines.append(f"- Baseline: `{baseline_run_id}`")
    lines.append(f"- Current: `{current_run_id}`")
    lines.append("")
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

    if threshold_failures or regressed_metrics:
        lines.append("")
        if threshold_failures:
            lines.append("**Threshold Failures**: " + ", ".join(sorted(set(threshold_failures))))
        if regressed_metrics:
            lines.append("**Regressions**: " + ", ".join(sorted(set(regressed_metrics))))

    return "\n".join(lines).strip()


__all__ = ["format_ci_gate_pr_comment"]
