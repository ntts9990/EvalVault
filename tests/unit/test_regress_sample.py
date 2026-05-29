"""Deterministic, DB-backed regress evidence generator (`evalvault regress-sample`).

These tests prove EvalVault can produce - from its own code, via the real
regression-gate path over a seeded temp SQLite DB - the T2 regress envelope that
``platform.adapters.evalvault_regress_adapter`` consumes. No network, no LLM, no
hosted tracker. They are the executable spec for the generation command
solution-platform calls instead of carrying a hand-authored static fixture.
"""

from __future__ import annotations

import json
import re
import statistics

import pytest
from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app
from evalvault.domain.services.regress_sample import REGRESS_SAMPLE_SCENARIOS

runner = CliRunner()

T3_RELEASE_VOCABULARY = re.compile(r"\b(promote|hold|rollback)\b", re.IGNORECASE)
EFFECT_LEVELS = {"negligible", "small", "medium", "large"}
# Mirror of platform.adapters.evalvault_regress_adapter.ALLOWED_EVALVAULT_STATUS;
# replicated (not imported) so the EvalVault suite has no cross-repo dependency.
ALLOWED_EVALVAULT_STATUS = {"passed", "failed"}


def _invoke(*args: str):
    return runner.invoke(app, ["regress-sample", *args])


def _assert_adapter_compatible(envelope: dict) -> None:
    """Replicate the required-field checks in ``map_evalvault_regress_payload``.

    Proves the envelope is consumable by the platform adapter without importing
    the platform package (which is not on EvalVault's path).
    """
    # _assert_t2_only: no T3 release vocabulary anywhere in the envelope.
    serialized = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
    leak = T3_RELEASE_VOCABULARY.search(serialized)
    assert leak is None, f"T2 envelope leaked T3 vocabulary: {leak and leak.group(0)!r}"

    assert envelope["command"] == "regress"
    assert envelope["status"] == "ok"

    data = envelope["data"]
    assert isinstance(data, dict)
    assert data["status"] in ALLOWED_EVALVAULT_STATUS

    # Adapter reads source_artifact_hash + evidence + a per-metric result row.
    assert isinstance(data["source_artifact_hash"], str)
    assert data["source_artifact_hash"].startswith("sha256:")
    evidence = data["evidence"]
    assert evidence["schema_version"] == "evalvault.regression-gate.hashes.v1"
    assert evidence["source_artifact_hash"] == data["source_artifact_hash"]
    for field in (
        "baseline_run_hash",
        "candidate_run_hash",
        "comparison_results_hash",
        "evidence_hash",
    ):
        assert isinstance(evidence[field], str) and evidence[field].startswith("sha256:"), field
    assert evidence["hash_algorithm"] == "sha256"

    results = data["results"]
    assert isinstance(results, list) and results
    for result in results:
        assert isinstance(result["metric"], str)
        assert isinstance(result["baseline_score"], (int, float))
        assert isinstance(result["candidate_score"], (int, float))


def test_quality_steady_scenario_has_exact_means() -> None:
    """The built-in scenario seeds exact-decimal means (0.91 / 0.9025)."""
    scenario = REGRESS_SAMPLE_SCENARIOS["quality-steady"]
    assert statistics.fmean(scenario.baseline_scores) == pytest.approx(0.91, abs=1e-9)
    assert statistics.fmean(scenario.candidate_scores) == pytest.approx(0.9025, abs=1e-9)


def test_regress_sample_is_adapter_compatible_and_passed() -> None:
    """End-to-end real path -> a passing T2 envelope the platform adapter accepts."""
    result = _invoke()
    assert result.exit_code == 0, result.stdout
    envelope = json.loads(result.stdout)

    _assert_adapter_compatible(envelope)

    data = envelope["data"]
    # Contract-stable fields (exact).
    assert data["status"] == "passed"
    assert data["regression_detected"] is False
    assert data["baseline_run_id"] == "baseline-quality-steady"
    assert data["candidate_run_id"] == "candidate-quality-steady"
    assert data["metrics"] == ["quality_score"]
    assert data["test"] == "t-test"
    assert data["fail_on_regression"] == 0.05
    assert data["parallel"] is True
    assert data["concurrency"] is None

    # Pinned wall-clock fields -> byte-stability.
    assert envelope["started_at"] == "2026-05-29T00:00:00Z"
    assert envelope["finished_at"] == "2026-05-29T00:00:00Z"
    assert envelope["duration_ms"] == 0

    (row,) = data["results"]
    assert row["metric"] == "quality_score"
    assert row["regression"] is False
    # Arithmetic fields: deterministic, asserted within ~1 ULP tolerance.
    assert row["baseline_score"] == pytest.approx(0.91, abs=1e-3)
    assert row["candidate_score"] == pytest.approx(0.9025, abs=1e-3)
    assert row["diff"] == pytest.approx(-0.0075, abs=1e-3)
    assert row["diff_percent"] == pytest.approx(-0.824176, abs=1e-3)
    # scipy-derived fields: range/sign only (per the regression-gate contract).
    assert 0.0 <= row["p_value"] <= 1.0
    assert row["effect_size"] < 0
    assert row["effect_level"] in EFFECT_LEVELS
    assert isinstance(row["is_significant"], bool)


def test_regress_sample_is_byte_deterministic() -> None:
    """Two invocations of the generator emit byte-identical JSON."""
    first = _invoke()
    second = _invoke()
    assert first.exit_code == 0 and second.exit_code == 0
    assert first.stdout == second.stdout


def test_regress_sample_writes_output_file(tmp_path) -> None:
    """`--output` writes the same stable JSON it prints (plus a trailing newline)."""
    out = tmp_path / "evalvault-regress-quality-steady.json"
    result = _invoke("--output", str(out))
    assert result.exit_code == 0
    assert out.exists()

    on_disk = out.read_text(encoding="utf-8")
    assert on_disk.endswith("\n")
    assert json.loads(on_disk) == json.loads(result.stdout)
    _assert_adapter_compatible(json.loads(on_disk))


def test_regress_sample_db_backed_path_seeds_real_sqlite(tmp_path) -> None:
    """`--db` routes through a real on-disk SQLite DB (the DB-backed regress path)."""
    db_path = tmp_path / "regress-sample.db"
    result = _invoke("--db", str(db_path))
    assert result.exit_code == 0, result.stdout
    assert db_path.exists(), "regress-sample should seed and use the provided SQLite DB"
    _assert_adapter_compatible(json.loads(result.stdout))


def test_regress_sample_rejects_unknown_scenario() -> None:
    """An unknown scenario name fails closed (exit 1), listing what is available."""
    result = _invoke("--scenario", "does-not-exist")
    assert result.exit_code == 1
    assert "quality-steady" in result.stdout
