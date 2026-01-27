"""Run regression suites for CI quality gate."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from evalvault.scripts.regression_runner import (
    append_issue_log,
    format_summary,
    load_regression_config,
    run_regression_suites,
    select_suites,
    write_json_summary,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EvalVault regression gate runner")
    parser.add_argument("--config", type=Path, default=None, help="Regression config path")
    parser.add_argument(
        "--suites",
        type=str,
        default=None,
        help="Comma-separated suite names to run",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=None,
        help="Write JSON summary to a file",
    )
    parser.add_argument(
        "--issue-log",
        type=Path,
        default=None,
        help="Append summary to a markdown log",
    )
    parser.add_argument("--tag", type=str, default=None, help="Label for the run")
    parser.add_argument(
        "--format",
        type=str,
        default="text",
        choices=["text", "github-actions"],
        help="Output format",
    )
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="Stop on first suite failure",
    )
    return parser.parse_args()


def _split_names(raw: str | None) -> Sequence[str] | None:
    if not raw:
        return None
    return [name.strip() for name in raw.split(",") if name.strip()]


def _emit_github_actions(results) -> None:
    for result in results:
        status = "✅" if result.succeeded else "❌"
        print(f"{status} {result.name} — {result.status.upper()} ({result.duration:.1f}s)")
        if not result.succeeded:
            message = result.stderr.splitlines()[-1] if result.stderr else "Suite failed"
            print(f"::error::Regression suite failed: {result.name} ({message})")
    passed = all(result.succeeded for result in results)
    print(f"::set-output name=passed::{str(passed).lower()}")


def main() -> int:
    args = _parse_args()

    suites = load_regression_config(args.config)
    selected = select_suites(suites, _split_names(args.suites))
    results = run_regression_suites(selected, stop_on_failure=args.stop_on_failure)

    summary = format_summary(results, tag=args.tag)
    if args.summary:
        write_json_summary(args.summary, results, tag=args.tag)
    if args.issue_log:
        append_issue_log(args.issue_log, summary)

    if args.format == "github-actions":
        _emit_github_actions(results)
    else:
        print(summary)

    if any(not result.succeeded for result in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
