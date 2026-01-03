"""Tests for the regression runner utilities."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from evalvault.scripts.regression_runner import (
    DEFAULT_CONFIG_PATH,
    RegressionSuite,
    format_summary,
    load_regression_config,
    run_regression_suites,
    select_suites,
)


def write_config(path: Path, suites: list[dict]) -> Path:
    payload = {"suites": suites}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_regression_config(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path / "regressions.json",
        [
            {
                "name": "unit",
                "command": [sys.executable, "-c", "print('unit')"],
                "timeout": 5,
            }
        ],
    )

    suites = load_regression_config(config_path)

    assert len(suites) == 1
    assert suites[0].name == "unit"
    assert suites[0].command[0] == sys.executable
    assert suites[0].timeout == 5


def test_default_config_path_exists() -> None:
    assert DEFAULT_CONFIG_PATH.exists()


def test_select_suites_filters_by_name() -> None:
    suites = [
        RegressionSuite(name="a", command=[sys.executable, "-c", "print('a')"]),
        RegressionSuite(name="b", command=[sys.executable, "-c", "print('b')"]),
    ]

    selected = select_suites(suites, ["b"])

    assert len(selected) == 1
    assert selected[0].name == "b"


def test_run_regression_suites_stop_on_failure(monkeypatch) -> None:
    suites = [
        RegressionSuite(
            name="pass",
            command=[sys.executable, "-c", "import sys; sys.exit(0)"],
        ),
        RegressionSuite(
            name="fail",
            command=[sys.executable, "-c", "import sys; sys.exit(1)"],
        ),
        RegressionSuite(
            name="after",
            command=[sys.executable, "-c", "print('skip')"],
        ),
    ]

    results = run_regression_suites(suites, stop_on_failure=True)

    assert len(results) == 2
    assert results[0].status == "passed"
    assert results[1].status in {"failed", "error"}


def test_format_summary_returns_human_readable_text() -> None:
    suites = [
        RegressionSuite(
            name="pass-suite",
            command=[sys.executable, "-c", "import sys; sys.exit(0)"],
        ),
    ]
    results = run_regression_suites(suites)

    summary = format_summary(results, tag="demo")

    assert "demo" in summary
    assert "pass-suite" in summary
