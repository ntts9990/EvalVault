#!/usr/bin/env python3
"""Execute EvalVault regression suites with optional Slack/issue outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

from evalvault.scripts.regression_runner import (
    DEFAULT_CONFIG_PATH,
    append_issue_log,
    format_summary,
    load_regression_config,
    run_regression_suites,
    select_suites,
    send_slack_summary,
    write_json_summary,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run EvalVault regression suites.")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=f"Regression config path (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Use a regression profile from config/regressions/<profile>.json",
    )
    parser.add_argument(
        "--suite",
        dest="suites",
        action="append",
        help="Suite name to run (can be provided multiple times).",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional JSON output path for structured results.",
    )
    parser.add_argument(
        "--slack-webhook",
        default=None,
        help="Optional Slack webhook to receive summary updates.",
    )
    parser.add_argument(
        "--issue-file",
        type=Path,
        default=None,
        help="Append a single-line summary to this markdown file.",
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="Label for this regression run (e.g., 'phoenix-alert').",
    )
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="Stop executing additional suites once a failure occurs.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available suites and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path = args.config
    if args.profile:
        if config_path is not None:
            parser.error("--profile and --config cannot be used together.")
        config_path = DEFAULT_CONFIG_PATH.parent / f"{args.profile}.json"
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    suites = load_regression_config(config_path)

    if args.list:
        parser.exit(
            0,
            "\n".join(f"- {suite.name}: {suite.description or ''}" for suite in suites) + "\n",
        )

    try:
        selected = select_suites(suites, args.suites)
    except KeyError as exc:  # pragma: no cover - user input validation
        parser.error(str(exc))

    if not selected:
        parser.error("No regression suites selected.")

    results = run_regression_suites(selected, stop_on_failure=args.stop_on_failure)
    summary = format_summary(results, tag=args.tag)
    print(summary)

    if args.json_out:
        write_json_summary(args.json_out, results, tag=args.tag)

    send_slack_summary(args.slack_webhook, summary)
    append_issue_log(args.issue_file, summary)

    return 0 if all(result.succeeded for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
