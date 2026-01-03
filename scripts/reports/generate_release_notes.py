#!/usr/bin/env python3
"""Generate release notes from EvalVault summary outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evalvault.reports import build_release_notes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build EvalVault release notes.")
    parser.add_argument(
        "--summary",
        required=True,
        type=Path,
        help="Path to EvalVault summary JSON (from evalvault run/gate/analyze --output).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional path to write the rendered notes (stdout when omitted).",
    )
    parser.add_argument(
        "--style",
        choices=("markdown", "plain", "slack"),
        default="markdown",
        help="Output style.",
    )
    parser.add_argument(
        "--max-failures",
        type=int,
        default=5,
        help="Maximum number of failed cases to list explicitly.",
    )
    parser.add_argument(
        "--prompt-diff-lines",
        type=int,
        default=20,
        help="Maximum diff lines to include per prompt (0 disables diffs).",
    )
    return parser.parse_args()


def load_summary(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("summary JSON must be an object")
    return data


def main() -> None:
    args = parse_args()
    summary = load_summary(args.summary)
    notes = build_release_notes(
        summary,
        style=args.style,
        max_failures=args.max_failures,
        prompt_diff_lines=args.prompt_diff_lines,
    )

    if args.out:
        args.out.write_text(notes, encoding="utf-8")
    else:
        print(notes)


if __name__ == "__main__":
    main()
