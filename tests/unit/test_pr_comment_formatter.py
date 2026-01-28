from __future__ import annotations

from evalvault.adapters.outbound.report.ci_report_formatter import CIGateMetricRow
from evalvault.adapters.outbound.report.pr_comment_formatter import format_ci_gate_pr_comment


def _row(
    metric: str, baseline: float, current: float, change: float, status: str
) -> CIGateMetricRow:
    return CIGateMetricRow(
        metric=metric,
        baseline_score=baseline,
        current_score=current,
        change_percent=change,
        status=status,
    )


def test_pr_comment_includes_header_and_run_ids() -> None:
    content = format_ci_gate_pr_comment(
        [_row("faithfulness", 0.8, 0.82, 2.5, "✅")],
        baseline_run_id="baseline",
        current_run_id="current",
        regression_rate=0.0,
        regression_threshold=0.05,
        gate_passed=True,
        threshold_failures=[],
        regressed_metrics=[],
    )

    assert "## EvalVault CI Gate" in content
    assert "`baseline`" in content
    assert "`current`" in content


def test_pr_comment_renders_table_rows() -> None:
    content = format_ci_gate_pr_comment(
        [_row("faithfulness", 0.8, 0.82, 2.5, "✅")],
        baseline_run_id="base",
        current_run_id="cur",
        regression_rate=0.0,
        regression_threshold=0.05,
        gate_passed=True,
        threshold_failures=[],
        regressed_metrics=[],
    )

    assert "| Metric | Baseline | Current | Change | Status |" in content
    assert "| faithfulness | 0.800 | 0.820 | +2.5% | ✅ |" in content


def test_pr_comment_passed_status_line() -> None:
    content = format_ci_gate_pr_comment(
        [],
        baseline_run_id="base",
        current_run_id="cur",
        regression_rate=0.0,
        regression_threshold=0.05,
        gate_passed=True,
        threshold_failures=[],
        regressed_metrics=[],
    )

    assert "✅ PASSED" in content
    assert "regression: 0.0% < 5.0%" in content


def test_pr_comment_failed_status_line() -> None:
    content = format_ci_gate_pr_comment(
        [],
        baseline_run_id="base",
        current_run_id="cur",
        regression_rate=0.2,
        regression_threshold=0.05,
        gate_passed=False,
        threshold_failures=[],
        regressed_metrics=[],
    )

    assert "❌ FAILED" in content
    assert "regression: 20.0% >= 5.0%" in content


def test_pr_comment_includes_threshold_failures() -> None:
    content = format_ci_gate_pr_comment(
        [_row("faithfulness", 0.8, 0.6, -25.0, "❌")],
        baseline_run_id="base",
        current_run_id="cur",
        regression_rate=0.0,
        regression_threshold=0.05,
        gate_passed=False,
        threshold_failures=["faithfulness"],
        regressed_metrics=[],
    )

    assert "**Threshold Failures**: faithfulness" in content


def test_pr_comment_includes_regressed_metrics() -> None:
    content = format_ci_gate_pr_comment(
        [_row("faithfulness", 0.8, 0.6, -25.0, "⚠️")],
        baseline_run_id="base",
        current_run_id="cur",
        regression_rate=0.5,
        regression_threshold=0.05,
        gate_passed=False,
        threshold_failures=[],
        regressed_metrics=["faithfulness"],
    )

    assert "**Regressions**: faithfulness" in content


def test_pr_comment_sorts_and_dedupes_failure_lists() -> None:
    content = format_ci_gate_pr_comment(
        [_row("answer_relevancy", 0.8, 0.7, -12.5, "⚠️")],
        baseline_run_id="base",
        current_run_id="cur",
        regression_rate=0.5,
        regression_threshold=0.05,
        gate_passed=False,
        threshold_failures=["faithfulness", "answer_relevancy", "faithfulness"],
        regressed_metrics=["answer_relevancy", "faithfulness", "answer_relevancy"],
    )

    assert "**Threshold Failures**: answer_relevancy, faithfulness" in content
    assert "**Regressions**: answer_relevancy, faithfulness" in content


def test_pr_comment_omits_failure_sections_when_empty() -> None:
    content = format_ci_gate_pr_comment(
        [_row("faithfulness", 0.8, 0.82, 2.5, "✅")],
        baseline_run_id="base",
        current_run_id="cur",
        regression_rate=0.0,
        regression_threshold=0.05,
        gate_passed=True,
        threshold_failures=[],
        regressed_metrics=[],
    )

    assert "Threshold Failures" not in content
    assert "Regressions" not in content


def test_pr_comment_formats_negative_change() -> None:
    content = format_ci_gate_pr_comment(
        [_row("faithfulness", 0.8, 0.6, -25.0, "❌")],
        baseline_run_id="base",
        current_run_id="cur",
        regression_rate=0.0,
        regression_threshold=0.05,
        gate_passed=False,
        threshold_failures=["faithfulness"],
        regressed_metrics=[],
    )

    assert "-25.0%" in content


def test_pr_comment_uses_status_symbol() -> None:
    content = format_ci_gate_pr_comment(
        [_row("faithfulness", 0.8, 0.82, 2.5, "✅")],
        baseline_run_id="base",
        current_run_id="cur",
        regression_rate=0.0,
        regression_threshold=0.05,
        gate_passed=True,
        threshold_failures=[],
        regressed_metrics=[],
    )

    assert "| faithfulness | 0.800 | 0.820 | +2.5% | ✅ |" in content
