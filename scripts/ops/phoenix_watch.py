#!/usr/bin/env python3
"""Poll Phoenix experiments for updates and emit Slack/issue notifications.

Usage:
    uv run python scripts/ops/phoenix_watch.py \\
        --endpoint http://localhost:6006 \\
        --dataset-id ds_123 \\
        --interval 60 \\
        --state-file .phoenix_watch \\
        --drift-threshold 0.2 \\
        --gate-command "uv run evalvault gate tests/gates/dev.json"

Optional:
    --api-key <token>           Phoenix Cloud API 토큰
    --slack-webhook <url>       Slack Incoming Webhook URL
    --issue-file path.md        새 이벤트를 마크다운 파일에 append
    --drift-key metric_name     Drift 지표 키 (기본 embedding_drift_score)
    --drift-threshold value     해당 지표가 value 이상이면 Alert + Gate 실행
    --gate-command "...gate"    Drift 초과 시 실행할 EvalVault Gate 명령
    --gate-shell                Gate 명령을 shell=True 로 실행 (신뢰된 명령만, 단일 라인)
    --prompt-manifest path      Prompt manifest JSON (diff baseline)
    --prompt-files file [...]   Prompt 파일 리스트 (space separated)
    --prompt-diff-lines 20      Prompt diff 표시 라인 수 (0이면 비활성화)
    --once                      한 번만 조회하고 종료
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
import warnings
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from evalvault.domain.services.prompt_manifest import (
    load_prompt_manifest,
    summarize_prompt_entry,
)
from evalvault.domain.services.prompt_status import (
    format_prompt_section,
    format_prompt_summary_label,
)

try:
    from phoenix.client import Client
except ImportError as exc:  # pragma: no cover - runtime guard
    raise SystemExit(
        "arize-phoenix가 설치되어야 합니다. 'uv sync --extra phoenix' 후 다시 실행하세요."
    ) from exc


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    formats = ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ")
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def load_last_seen(path: Path | None) -> datetime | None:
    if not path or not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        value = data.get("last_seen")
        return _parse_timestamp(value)
    except Exception:
        return None


def save_last_seen(path: Path | None, timestamp: datetime | None) -> None:
    if not path or timestamp is None:
        return
    path.write_text(json.dumps({"last_seen": timestamp.isoformat()}))


def notify_slack(webhook: str, message: str) -> None:
    try:
        response = httpx.post(webhook, json={"text": message}, timeout=10)
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - best-effort alert
        print(f"[phoenix-watch] Slack 알림 실패: {exc}", file=sys.stderr)


def append_issue(path: Path | None, message: str) -> None:
    if not path:
        return
    timestamp = datetime.now(UTC).isoformat()
    payload = f"- [{timestamp}] {message}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(payload)


def format_event(exp: dict[str, Any]) -> str:
    return (
        f"Experiment {exp.get('id')} ({exp.get('project_name') or 'default'}) "
        f"updated at {exp.get('updated_at')} "
        f"[runs: success={exp.get('successful_run_count')}, "
        f"failed={exp.get('failed_run_count')}]"
    )


def format_event_with_drift(
    exp: dict[str, Any],
    *,
    drift_key: str | None,
    drift_value: float | None,
) -> str:
    base = format_event(exp)
    if drift_key and drift_value is not None:
        return f"{base} | {drift_key}={drift_value:.3f}"
    return base


def poll_experiments(
    client: Client,
    dataset_id: str,
    last_seen: datetime | None,
) -> tuple[list[tuple[datetime, dict[str, Any]]], datetime | None]:
    experiments = client.experiments.list(dataset_id=dataset_id)
    new_events: list[tuple[datetime, dict[str, Any]]] = []
    newest = last_seen
    for exp in experiments:
        updated_at = _parse_timestamp(exp.get("updated_at"))
        if updated_at is None:
            continue
        if last_seen is None or updated_at > last_seen:
            new_events.append((updated_at, exp))
        if newest is None or updated_at > newest:
            newest = updated_at
    new_events.sort(key=lambda item: item[0])
    return new_events, newest


def _coerce_metric_value(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for candidate_key in ("value", "score", "drift", "metric"):
            if candidate_key in value:
                candidate = _coerce_metric_value(value[candidate_key])
                if candidate is not None:
                    return candidate
    return None


def collect_prompt_diffs(
    manifest_path: Path | None,
    prompt_paths: list[Path],
) -> list[dict[str, Any]]:
    """Return prompt summaries for the configured prompt files."""

    if not prompt_paths:
        return []

    manifest_data = None
    if manifest_path:
        try:
            manifest_data = load_prompt_manifest(manifest_path)
        except Exception as exc:  # pragma: no cover - protective logging
            print(f"[phoenix-watch] Failed to load prompt manifest: {exc}", file=sys.stderr)
            manifest_data = None

    entries: list[dict[str, Any]] = []
    for prompt_path in prompt_paths:
        target = prompt_path.expanduser()
        try:
            content = target.read_text(encoding="utf-8")
        except FileNotFoundError:
            entries.append(
                {
                    "path": target.as_posix(),
                    "status": "missing_file",
                }
            )
            continue

        summary = summarize_prompt_entry(
            manifest_data,
            prompt_path=target,
            content=content,
        )
        entries.append(asdict(summary))

    return entries


def extract_drift_score(exp: dict[str, Any], drift_key: str | None) -> float | None:
    if not drift_key:
        return None

    containers = [exp]
    metrics = exp.get("metrics")
    if isinstance(metrics, dict):
        containers.append(metrics)
    metadata = exp.get("metadata")
    if isinstance(metadata, dict):
        containers.append(metadata)

    for container in containers:
        if drift_key not in container:
            continue
        candidate = _coerce_metric_value(container[drift_key])
        if candidate is not None:
            return candidate
    return None


def _validate_gate_command(command: str, *, shell: bool) -> str | None:
    if not command.strip():
        return "Gate command is empty."
    if shell and ("\n" in command or "\r" in command):
        return "Gate command must be single-line when --gate-shell is enabled."
    return None


def run_gate_command(command: str, *, shell: bool = False) -> tuple[int, str]:
    validation_error = _validate_gate_command(command, shell=shell)
    if validation_error:
        return 1, validation_error
    try:
        if shell:
            warnings.warn(
                "--gate-shell enables shell execution; use only trusted commands.",
                RuntimeWarning,
                stacklevel=2,
            )
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=False,
            )
        else:
            completed = subprocess.run(
                shlex.split(command),
                capture_output=True,
                text=True,
                check=False,
            )
    except Exception as exc:
        return 1, f"Gate command 실행 실패: {exc}"

    combined_output = "\n".join(filter(None, [completed.stdout.strip(), completed.stderr.strip()]))
    return completed.returncode, combined_output


def _default_regression_script() -> Path:
    return Path(__file__).resolve().parents[2] / "scripts" / "tests" / "run_regressions.py"


def run_regression_runner(
    *,
    script_override: Path | None,
    config: Path | None,
    suites: list[str],
    stop_on_failure: bool,
    json_out: Path | None,
    tag: str | None,
) -> tuple[int, str]:
    script_path = script_override or _default_regression_script()
    if not script_path.exists():
        return 1, f"Regression script not found: {script_path}"
    cmd = [sys.executable, str(script_path)]
    if config:
        cmd += ["--config", str(config)]
    for suite in suites:
        cmd += ["--suite", suite]
    if stop_on_failure:
        cmd.append("--stop-on-failure")
    if json_out:
        cmd += ["--json-out", str(json_out)]
    if tag:
        cmd += ["--tag", tag]
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(filter(None, [completed.stdout.strip(), completed.stderr.strip()]))
    return completed.returncode, output


def main() -> None:
    parser = argparse.ArgumentParser(description="Phoenix dataset/experiment watcher")
    parser.add_argument("--endpoint", default="http://localhost:6006", help="Phoenix base URL")
    parser.add_argument("--api-key", default=None, help="Phoenix API token (Cloud only)")
    parser.add_argument("--dataset-id", required=True, help="Dataset ID to monitor")
    parser.add_argument("--interval", type=int, default=60, help="Polling interval in seconds")
    parser.add_argument(
        "--state-file",
        type=Path,
        default=Path(".phoenix_watch_state.json"),
        help="File to persist last seen timestamp",
    )
    parser.add_argument("--slack-webhook", default=None, help="Slack webhook URL")
    parser.add_argument(
        "--issue-file",
        type=Path,
        default=None,
        help="Append new events to a markdown file (for manual issue triage)",
    )
    parser.add_argument(
        "--drift-key",
        default="embedding_drift_score",
        help="Drift metric to monitor (exp.metrics[drift-key]); set empty string to disable.",
    )
    parser.add_argument(
        "--drift-threshold",
        type=float,
        default=None,
        help="Raise alerts and trigger gate command when drift exceeds this value.",
    )
    parser.add_argument(
        "--gate-command",
        default=None,
        help="Command to execute (e.g., 'uv run evalvault gate ...') when drift exceeds threshold.",
    )
    parser.add_argument(
        "--gate-shell",
        action="store_true",
        help=("Run gate command via shell=True (trusted commands only, single-line only)."),
    )
    parser.add_argument(
        "--prompt-manifest",
        type=Path,
        default=None,
        help="Path to prompt_manifest.json for diff comparisons (optional).",
    )
    parser.add_argument(
        "--prompt-files",
        type=Path,
        nargs="*",
        default=[],
        help="Prompt files to diff each cycle (space separated).",
    )
    parser.add_argument(
        "--prompt-diff-lines",
        type=int,
        default=20,
        help="Maximum diff lines per prompt to include in alerts (0 to disable diffs).",
    )
    parser.add_argument(
        "--run-regressions",
        choices=("never", "event", "threshold"),
        default="never",
        help="Run regression suites on each event or only when drift exceeds the threshold.",
    )
    parser.add_argument(
        "--regression-config",
        type=Path,
        default=None,
        help="Optional path to regression config JSON (defaults to config/regressions/default.json).",
    )
    parser.add_argument(
        "--regression-suite",
        dest="regression_suites",
        action="append",
        default=[],
        help="Regression suite name to run (repeatable).",
    )
    parser.add_argument(
        "--regression-script",
        type=Path,
        default=None,
        help="Override path to scripts/tests/run_regressions.py.",
    )
    parser.add_argument(
        "--regression-stop-on-failure",
        action="store_true",
        help="Pass --stop-on-failure to the regression runner.",
    )
    parser.add_argument(
        "--regression-json-out",
        type=Path,
        default=None,
        help="Write regression JSON summary to this path when triggered.",
    )
    parser.add_argument("--once", action="store_true", help="Run one iteration and exit")
    args = parser.parse_args()
    args.drift_key = (args.drift_key or "").strip() or None

    client = Client(base_url=args.endpoint, api_key=args.api_key)
    last_seen = load_last_seen(args.state_file)

    while True:
        events, newest = poll_experiments(client, args.dataset_id, last_seen)
        prompt_entries = collect_prompt_diffs(args.prompt_manifest, args.prompt_files)
        prompt_summary_label = format_prompt_summary_label(prompt_entries)
        prompt_section_slack = format_prompt_section(
            prompt_entries,
            style="slack",
            max_diff_lines=args.prompt_diff_lines,
        )
        prompt_section_plain = format_prompt_section(
            prompt_entries,
            style="plain",
            max_diff_lines=args.prompt_diff_lines,
        )
        threshold_hit_this_cycle = False
        threshold_reason: str | None = None
        if events:
            for _when, exp in events:
                drift_value = extract_drift_score(exp, args.drift_key)
                message = format_event_with_drift(
                    exp,
                    drift_key=args.drift_key,
                    drift_value=drift_value,
                )
                combined_message = (
                    f"{message} | Prompt {prompt_summary_label}"
                    if prompt_summary_label
                    else message
                )
                print(f"[phoenix-watch] {combined_message}")
                if args.slack_webhook:
                    payload = combined_message
                    if prompt_section_slack:
                        payload = f"{combined_message}\n{prompt_section_slack}"
                    notify_slack(args.slack_webhook, payload)
                issue_payload = combined_message
                if prompt_section_plain:
                    issue_payload = f"{combined_message}\n{prompt_section_plain}"
                append_issue(args.issue_file, issue_payload)

                threshold_hit = (
                    args.drift_threshold is not None
                    and drift_value is not None
                    and drift_value >= args.drift_threshold
                )
                if threshold_hit:
                    alert = (
                        "⚠ Drift threshold exceeded: "
                        f"{drift_value:.3f} (key={args.drift_key}, "
                        f"threshold={args.drift_threshold:.3f})"
                    )
                    alert_message = (
                        f"{alert} | Prompt {prompt_summary_label}"
                        if prompt_summary_label
                        else alert
                    )
                    print(f"[phoenix-watch] {alert_message}")
                    alert_issue_payload = alert_message
                    if prompt_section_plain:
                        alert_issue_payload = f"{alert_message}\n{prompt_section_plain}"
                    append_issue(args.issue_file, alert_issue_payload)
                    if args.slack_webhook:
                        alert_payload = alert_message
                        if prompt_section_slack:
                            alert_payload = f"{alert_message}\n{prompt_section_slack}"
                        notify_slack(args.slack_webhook, alert_payload)

                    if args.gate_command:
                        exit_code, gate_output = run_gate_command(
                            args.gate_command,
                            shell=args.gate_shell,
                        )
                        gate_message = (
                            f"Triggered gate command '{args.gate_command}' (exit_code={exit_code})"
                        )
                        gate_message_with_prompt = (
                            f"{gate_message} | Prompt {prompt_summary_label}"
                            if prompt_summary_label
                            else gate_message
                        )
                        print(f"[phoenix-watch] {gate_message_with_prompt}")
                        if gate_output:
                            print(gate_output)
                        gate_issue_payload = gate_message_with_prompt
                        if prompt_section_plain:
                            gate_issue_payload = (
                                f"{gate_message_with_prompt}\n{prompt_section_plain}"
                            )
                        append_issue(args.issue_file, gate_issue_payload)
                        if gate_output:
                            append_issue(args.issue_file, gate_output)
                        if args.slack_webhook:
                            payload = gate_message_with_prompt
                            if prompt_section_slack:
                                payload = f"{payload}\n{prompt_section_slack}"
                            if gate_output:
                                payload = f"{payload}\n```\n{gate_output}\n```"
                            notify_slack(args.slack_webhook, payload)
                    if threshold_reason is None:
                        threshold_reason = (
                            f"drift {drift_value:.3f}/{args.drift_threshold:.3f}"
                            if args.drift_threshold is not None and drift_value is not None
                            else "drift-threshold"
                        )
                    threshold_hit_this_cycle = True

            save_last_seen(args.state_file, newest)
            last_seen = newest
        else:
            print("[phoenix-watch] No new experiments detected")

        regression_reason = None
        if args.run_regressions == "event" and events:
            regression_reason = "phoenix-event"
        elif args.run_regressions == "threshold" and threshold_hit_this_cycle:
            regression_reason = threshold_reason or "drift-threshold"

        if regression_reason and args.run_regressions != "never":
            exit_code, regression_output = run_regression_runner(
                script_override=args.regression_script,
                config=args.regression_config,
                suites=args.regression_suites,
                stop_on_failure=args.regression_stop_on_failure,
                json_out=args.regression_json_out,
                tag=regression_reason,
            )
            regression_message = (
                f"Triggered regression suites (reason={regression_reason}, exit_code={exit_code})"
            )
            regression_message_with_prompt = (
                f"{regression_message} | Prompt {prompt_summary_label}"
                if prompt_summary_label
                else regression_message
            )
            print(f"[phoenix-watch] {regression_message_with_prompt}")
            if regression_output:
                print(regression_output)
            issue_payload = regression_message_with_prompt
            if prompt_section_plain:
                issue_payload = f"{issue_payload}\n{prompt_section_plain}"
            append_issue(args.issue_file, issue_payload)
            if regression_output:
                append_issue(args.issue_file, regression_output)
            if args.slack_webhook:
                payload = regression_message_with_prompt
                if prompt_section_slack:
                    payload = f"{payload}\n{prompt_section_slack}"
                if regression_output:
                    payload = f"{payload}\n```\n{regression_output}\n```"
                notify_slack(args.slack_webhook, payload)

        if args.once:
            break
        time.sleep(max(5, args.interval))


if __name__ == "__main__":
    main()
