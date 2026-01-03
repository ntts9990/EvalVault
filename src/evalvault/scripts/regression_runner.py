"""Regression runner utilities used by automation scripts."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:  # pragma: no cover - httpx is provided via extras
    httpx = None


def _detect_repo_root(start: Path) -> Path:
    """Walk upwards from the given path to find pyproject.toml."""

    current = start
    for _ in range(6):  # limit traversal depth to avoid runaway loops
        if (current / "pyproject.toml").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return start


REPO_ROOT = _detect_repo_root(Path(__file__).resolve())
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "regressions" / "default.json"


@dataclass
class RegressionSuite:
    """Definition of a single regression suite command."""

    name: str
    command: list[str]
    description: str | None = None
    timeout: int | None = None
    halt_on_failure: bool = False
    cwd: Path | None = None
    env: dict[str, str] | None = None


@dataclass
class RegressionResult:
    """Execution result for a regression suite."""

    name: str
    status: str
    exit_code: int | None
    duration: float
    command: list[str]
    description: str | None
    stdout: str
    stderr: str

    @property
    def succeeded(self) -> bool:
        return self.status == "passed"


def _normalize_command(command: Any) -> list[str]:
    if isinstance(command, list):
        return [str(part) for part in command]
    if isinstance(command, str):
        return shlex.split(command)
    raise TypeError("command must be a string or list")


def load_regression_config(path: Path | None) -> list[RegressionSuite]:
    """Load regression suites from a JSON config file."""

    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"Regression config not found: {config_path}")

    data = json.loads(config_path.read_text(encoding="utf-8"))
    suites_data = data.get("suites")
    if not isinstance(suites_data, list) or not suites_data:
        raise ValueError("Regression config must contain a non-empty 'suites' array")

    suites: list[RegressionSuite] = []
    for entry in suites_data:
        if not isinstance(entry, dict):
            raise ValueError("Each suite entry must be a JSON object")
        name = entry.get("name")
        command = entry.get("command")
        if not name or not command:
            raise ValueError("Suite entries require 'name' and 'command'")
        suite = RegressionSuite(
            name=str(name),
            command=_normalize_command(command),
            description=entry.get("description"),
            timeout=entry.get("timeout"),
            halt_on_failure=bool(entry.get("halt_on_failure", False)),
            cwd=Path(entry["cwd"]).expanduser() if isinstance(entry.get("cwd"), str) else None,
            env={str(k): str(v) for k, v in (entry.get("env") or {}).items()},
        )
        suites.append(suite)
    return suites


def select_suites(
    suites: list[RegressionSuite],
    names: Sequence[str] | None,
) -> list[RegressionSuite]:
    """Filter suites by name when requested."""

    if not names:
        return suites
    lookup = {suite.name: suite for suite in suites}
    selected: list[RegressionSuite] = []
    missing: list[str] = []
    for name in names:
        suite = lookup.get(name)
        if suite:
            selected.append(suite)
        else:
            missing.append(name)
    if missing:
        raise KeyError(f"Unknown regression suite(s): {', '.join(missing)}")
    return selected


def execute_suite(suite: RegressionSuite) -> RegressionResult:
    """Execute a single regression suite and capture stdout/stderr."""

    env = os.environ.copy()
    if suite.env:
        env.update(suite.env)

    start = time.monotonic()
    status = "passed"
    stdout = ""
    stderr = ""
    exit_code: int | None

    try:
        completed = subprocess.run(
            suite.command,
            cwd=str(suite.cwd) if suite.cwd else None,
            env=env,
            capture_output=True,
            text=True,
            timeout=suite.timeout,
            check=False,
        )
        exit_code = completed.returncode
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        if exit_code != 0:
            status = "failed"
    except subprocess.TimeoutExpired as exc:
        status = "timeout"
        exit_code = None
        stdout = (exc.stdout or "").strip()
        stderr = ((exc.stderr or "") + f"\nTimeout after {suite.timeout}s").strip()
    except Exception as exc:  # pragma: no cover - defensive path
        status = "error"
        exit_code = None
        stderr = str(exc)

    duration = time.monotonic() - start

    return RegressionResult(
        name=suite.name,
        status=status,
        exit_code=exit_code,
        duration=duration,
        command=suite.command,
        description=suite.description,
        stdout=stdout,
        stderr=stderr,
    )


def run_regression_suites(
    suites: Iterable[RegressionSuite],
    *,
    stop_on_failure: bool = False,
) -> list[RegressionResult]:
    """Execute suites sequentially and collect results."""

    results: list[RegressionResult] = []
    for suite in suites:
        result = execute_suite(suite)
        results.append(result)
        if not result.succeeded and (stop_on_failure or suite.halt_on_failure):
            break
    return results


def format_summary(results: Sequence[RegressionResult], tag: str | None = None) -> str:
    """Return a human-friendly summary string."""

    lines: list[str] = []
    header = "Regression Suites"
    if tag:
        header += f" ({tag})"
    lines.append(header)
    lines.append("-" * len(header))
    for result in results:
        symbol = "✅" if result.succeeded else "❌"
        lines.append(
            f"{symbol} {result.name} — {result.status.upper()} "
            f"({result.duration:.1f}s, cmd: {' '.join(result.command)})"
        )
        if result.stderr and not result.succeeded:
            lines.append(f"    stderr: {result.stderr.splitlines()[-1]}")
    return "\n".join(lines).strip()


def write_json_summary(
    path: Path,
    results: Sequence[RegressionResult],
    *,
    tag: str | None = None,
) -> None:
    """Persist structured results for later ingestion."""

    payload = {
        "tag": tag,
        "suites": [
            {
                "name": result.name,
                "status": result.status,
                "exit_code": result.exit_code,
                "duration": result.duration,
                "command": result.command,
                "description": result.description,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
            for result in results
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def send_slack_summary(
    webhook: str | None,
    summary: str,
) -> None:
    """Send the summary text to Slack when configured."""

    if not webhook:
        return
    if httpx is None:  # pragma: no cover - httpx missing
        raise RuntimeError("httpx is required for Slack notifications")
    try:
        response = httpx.post(webhook, json={"text": summary}, timeout=10)
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - best effort
        print(f"[regression-runner] Failed to send Slack message: {exc}", file=sys.stderr)


def append_issue_log(path: Path | None, summary: str) -> None:
    """Append run summary to an issue/markdown log."""

    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"- [{time.strftime('%Y-%m-%d %H:%M:%S')}] {summary}\n")


__all__ = [
    "DEFAULT_CONFIG_PATH",
    "RegressionResult",
    "RegressionSuite",
    "append_issue_log",
    "execute_suite",
    "format_summary",
    "load_regression_config",
    "run_regression_suites",
    "select_suites",
    "send_slack_summary",
    "write_json_summary",
]
