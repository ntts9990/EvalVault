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


# --- Forecast track scenarios (Phase 1-5A, Tier A) ------------------------

ALL_SCENARIOS = (
    "quality-steady",
    "forecast-calibrated",
    "forecast-overconfident",
    "forecast-leakage",
    "forecast-insufficient-evidence",
)

# name, metric, baseline_mean, candidate_mean, fail_on_regression, status, regression
FORECAST_CASES = [
    ("forecast-calibrated", "forecast_calibration_score", 0.82, 0.80, 0.05, "passed", False),
    ("forecast-overconfident", "forecast_calibration_score", 0.80, 0.70, 0.06, "failed", True),
    ("forecast-leakage", "leakage_resistance_score", 0.95, 0.76, 0.06, "failed", True),
    (
        "forecast-insufficient-evidence",
        "forecast_resolution_coverage",
        0.80,
        0.74,
        0.05,
        "failed",
        True,
    ),
]


def test_registry_contains_all_tier_a_scenarios() -> None:
    assert set(REGRESS_SAMPLE_SCENARIOS) == set(ALL_SCENARIOS)


def test_forecast_scenarios_have_exact_means() -> None:
    for name, _metric, b_mean, c_mean, *_rest in FORECAST_CASES:
        sc = REGRESS_SAMPLE_SCENARIOS[name]
        assert statistics.fmean(sc.baseline_scores) == pytest.approx(b_mean, abs=1e-9), name
        assert statistics.fmean(sc.candidate_scores) == pytest.approx(c_mean, abs=1e-9), name


@pytest.mark.parametrize(
    ("name", "metric", "b_mean", "c_mean", "fail_on", "status", "regression"),
    FORECAST_CASES,
)
def test_forecast_scenario_envelope(
    name: str,
    metric: str,
    b_mean: float,
    c_mean: float,
    fail_on: float,
    status: str,
    regression: bool,
) -> None:
    """Each forecast scenario emits an adapter-compatible T2 envelope with the
    expected verdict and exact arithmetic."""
    result = _invoke("--scenario", name)
    assert result.exit_code == 0, result.stdout
    envelope = json.loads(result.stdout)

    _assert_adapter_compatible(envelope)

    data = envelope["data"]
    assert data["status"] == status
    assert data["regression_detected"] is regression
    assert data["metrics"] == [metric]
    assert data["baseline_run_id"] == f"baseline-{name}"
    assert data["candidate_run_id"] == f"candidate-{name}"
    assert data["fail_on_regression"] == fail_on
    assert data["test"] == "t-test"

    (row,) = data["results"]
    assert row["metric"] == metric
    assert row["regression"] is regression
    assert row["baseline_score"] == pytest.approx(b_mean, abs=1e-3)
    assert row["candidate_score"] == pytest.approx(c_mean, abs=1e-3)
    assert row["diff"] == pytest.approx(c_mean - b_mean, abs=1e-3)
    assert 0.0 <= row["p_value"] <= 1.0
    assert row["effect_level"] in EFFECT_LEVELS
    assert isinstance(row["is_significant"], bool)


@pytest.mark.parametrize("name", ALL_SCENARIOS)
def test_scenario_is_byte_deterministic(name: str) -> None:
    """Every scenario emits byte-identical JSON across invocations."""
    first = _invoke("--scenario", name)
    second = _invoke("--scenario", name)
    assert first.exit_code == 0 and second.exit_code == 0, (first.stdout, second.stdout)
    assert first.stdout == second.stdout


@pytest.mark.parametrize("name", ALL_SCENARIOS)
def test_scenario_has_no_t3_vocabulary(name: str) -> None:
    """No release vocabulary (promote/hold/rollback) in the envelope OR in the
    scenario's own identifiers (run IDs / dataset / metric / name)."""
    result = _invoke("--scenario", name)
    assert result.exit_code == 0, result.stdout
    serialized = json.dumps(json.loads(result.stdout), ensure_ascii=False, sort_keys=True)
    assert T3_RELEASE_VOCABULARY.search(serialized) is None, f"envelope leaked T3 vocab: {name}"

    sc = REGRESS_SAMPLE_SCENARIOS[name]
    for text in (
        sc.name,
        sc.metric,
        sc.dataset_name,
        sc.baseline_run_id,
        sc.candidate_run_id,
    ):
        assert T3_RELEASE_VOCABULARY.search(text) is None, f"identifier leaked T3 vocab: {text!r}"


# --- forecast-insufficient-evidence diagnostics (Phase 1-16A) -------------

INSUFFICIENT = "forecast-insufficient-evidence"


def test_insufficient_evidence_emits_zero_pair_diagnostics() -> None:
    """The scenario emits a failed T2 verdict plus zero-pair evidence diagnostics
    in the adapter-accepted `data.evidence_diagnostics` shape."""
    result = _invoke("--scenario", INSUFFICIENT)
    assert result.exit_code == 0, result.stdout
    envelope = json.loads(result.stdout)

    _assert_adapter_compatible(envelope)

    data = envelope["data"]
    assert data["status"] == "failed"
    assert data["metrics"] == ["forecast_resolution_coverage"]

    diagnostics = data["evidence_diagnostics"]
    assert diagnostics["eligible_pair_count"] == 0
    assert diagnostics["sample_coverage"] == 0
    assert diagnostics["resolution_card_count"] == 0
    # Stable, self-describing marker (no release vocabulary).
    assert diagnostics["schema_version"] == "evalvault.evidence-diagnostics.v1"
    assert T3_RELEASE_VOCABULARY.search(json.dumps(diagnostics, sort_keys=True)) is None


def test_only_insufficient_evidence_carries_diagnostics() -> None:
    """Diagnostics are additive: the other scenarios omit the key entirely so
    their envelopes remain byte-stable."""
    for name in ALL_SCENARIOS:
        envelope = json.loads(_invoke("--scenario", name).stdout)
        if name == INSUFFICIENT:
            assert "evidence_diagnostics" in envelope["data"]
        else:
            assert "evidence_diagnostics" not in envelope["data"], name


def test_insufficient_evidence_db_backed_path(tmp_path) -> None:
    """`--db` routes the new scenario through a real on-disk SQLite DB and still
    emits the diagnostics + failed verdict."""
    db_path = tmp_path / "regress-sample.db"
    result = _invoke("--scenario", INSUFFICIENT, "--db", str(db_path))
    assert result.exit_code == 0, result.stdout
    assert db_path.exists()
    data = json.loads(result.stdout)["data"]
    assert data["status"] == "failed"
    assert data["evidence_diagnostics"]["eligible_pair_count"] == 0
