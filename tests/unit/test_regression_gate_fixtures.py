"""Fixture-only, no-network regression-gate examples (pass / fail / incomplete provenance).

These tests seed a temp SQLite DB from the curated fixtures under
``tests/fixtures/e2e/regression_gate/`` and invoke the real ``evalvault regress`` CLI
end-to-end — no OpenAI / MLflow / Phoenix / Langfuse / hosted tracker. They double as
the executable spec for the regression-gate decision contract (adapter-contract.md §2.1)
and validate the three golden envelopes adapter authors rely on.

Assertion granularity is deliberate (see fixtures README): contract fields are matched
exactly, score/diff fields use a 3-decimal tolerance to absorb cross-platform ~1 ULP
jitter, and scipy-derived statistical fields are checked by range/sign only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult

runner = CliRunner()

REGRESS_COMMAND_MODULE = "evalvault.adapters.inbound.cli.commands.regress"
FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "e2e" / "regression_gate"
EFFECT_LEVELS = {"negligible", "small", "medium", "large"}

# Contract-stable top-level report fields asserted for exact equality.
EXACT_REPORT_FIELDS = (
    "candidate_run_id",
    "baseline_run_id",
    "status",
    "regression_detected",
    "fail_on_regression",
    "test",
    "metrics",
    "parallel",
    "concurrency",
)
# Score/diff fields: deterministic arithmetic, asserted within 3-decimal tolerance.
TOLERANCE_RESULT_FIELDS = ("baseline_score", "candidate_score", "diff", "diff_percent")
T3_RELEASE_VOCABULARY = re.compile(r"\b(promote|hold|rollback)\b", re.IGNORECASE)


def _load_run(fixture_name: str) -> EvaluationRun:
    """Build an EvaluationRun from a compact run fixture (no network, no LLM)."""
    payload = json.loads((FIXTURE_DIR / "runs" / fixture_name).read_text(encoding="utf-8"))
    thresholds: dict[str, float] = payload.get("thresholds", {})
    results = [
        TestCaseResult(
            test_case_id=case["test_case_id"],
            metrics=[
                MetricScore(name=metric, score=score, threshold=thresholds.get(metric, 0.7))
                for metric, score in case["scores"].items()
            ],
        )
        for case in payload["cases"]
    ]
    return EvaluationRun(
        run_id=payload["run_id"],
        dataset_name=payload["dataset_name"],
        model_name=payload["model_name"],
        results=results,
        metrics_evaluated=list(payload["metrics_evaluated"]),
        thresholds=thresholds,
    )


def _load_expected(name: str) -> dict:
    return json.loads((FIXTURE_DIR / "expected" / name).read_text(encoding="utf-8"))


def _seed_and_invoke(
    tmp_path: Path, baseline_fixture: str, candidate_fixture: str
) -> tuple[int, dict]:
    """Seed a temp SQLite DB with the two fixture runs and run `regress --format json`."""
    db_path = tmp_path / "regress_fixtures.db"
    storage = SQLiteStorageAdapter(db_path=str(db_path))
    baseline = _load_run(baseline_fixture)
    candidate = _load_run(candidate_fixture)
    storage.save_run(baseline)
    storage.save_run(candidate)

    with patch(f"{REGRESS_COMMAND_MODULE}.build_storage_adapter", return_value=storage):
        result = runner.invoke(
            app,
            [
                "regress",
                candidate.run_id,
                "--baseline",
                baseline.run_id,
                "--format",
                "json",
                "--db",
                str(db_path),
            ],
        )
    payload = json.loads(result.stdout)
    return result.exit_code, payload


def _assert_envelope_shape(payload: dict, *, status: str) -> None:
    assert payload["command"] == "regress"
    assert payload["version"] == 1
    assert payload["status"] == status
    # Runtime fields are present but not value-asserted.
    for field in ("started_at", "finished_at", "duration_ms", "artifacts"):
        assert field in payload


def _assert_no_t3_release_vocabulary(payload: dict) -> None:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    match = T3_RELEASE_VOCABULARY.search(serialized)
    assert match is None, f"EvalVault T2 output emitted T3 vocabulary: {match.group(0)!r}"


def _assert_hash_anchored_evidence(data: dict) -> None:
    evidence = data["evidence"]
    assert data["source_artifact_hash"].startswith("sha256:")
    assert evidence["schema_version"] == "evalvault.regression-gate.hashes.v1"
    assert evidence["source_artifact_hash"] == data["source_artifact_hash"]
    for field in (
        "baseline_run_hash",
        "candidate_run_hash",
        "comparison_results_hash",
        "evidence_hash",
    ):
        assert evidence[field].startswith("sha256:"), field
    assert evidence["hash_algorithm"] == "sha256"


@pytest.mark.parametrize(
    ("baseline_fixture", "candidate_fixture"),
    [
        ("pass_baseline.json", "pass_candidate.json"),
        ("fail_baseline.json", "fail_candidate.json"),
        ("incomplete_baseline.json", "incomplete_candidate.json"),
    ],
)
def test_regress_json_output_never_emits_t3_release_vocabulary(
    tmp_path: Path,
    baseline_fixture: str,
    candidate_fixture: str,
) -> None:
    """RegressionGateReport is a T2 artifact and must not emit T3 release decisions."""
    _, payload = _seed_and_invoke(tmp_path, baseline_fixture, candidate_fixture)

    _assert_no_t3_release_vocabulary(payload)


def test_regress_fixture_pass(tmp_path: Path) -> None:
    """Candidate ≈ baseline → no regression, verdict 'passed', exit 0."""
    expected = _load_expected("pass.json")
    exit_code, payload = _seed_and_invoke(tmp_path, "pass_baseline.json", "pass_candidate.json")

    assert exit_code == expected["_meta"]["exit_code"] == 0
    _assert_envelope_shape(payload, status="ok")
    _assert_no_t3_release_vocabulary(payload)

    data = payload["data"]
    exp = expected["data"]
    for field in EXACT_REPORT_FIELDS:
        assert data[field] == exp[field], f"contract field drift: {field}"
    assert data["status"] == "passed"
    assert data["regression_detected"] is False
    _assert_hash_anchored_evidence(data)

    actual_by_metric = {r["metric"]: r for r in data["results"]}
    exp_by_metric = {r["metric"]: r for r in exp["results"]}
    assert set(actual_by_metric) == set(exp_by_metric)
    for metric, result in actual_by_metric.items():
        golden = exp_by_metric[metric]
        assert result["regression"] is False
        for field in TOLERANCE_RESULT_FIELDS:
            assert result[field] == pytest.approx(golden[field], abs=1e-3), f"{metric}.{field}"
        assert 0.0 <= result["p_value"] <= 1.0
        assert result["effect_level"] in EFFECT_LEVELS
        assert isinstance(result["is_significant"], bool)


def test_regress_fixture_hashes_are_stable_for_identical_inputs(tmp_path: Path) -> None:
    """Source/evidence hashes ignore wall-clock envelope fields."""
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    _, first = _seed_and_invoke(first_dir, "pass_baseline.json", "pass_candidate.json")
    _, second = _seed_and_invoke(second_dir, "pass_baseline.json", "pass_candidate.json")

    first_data = first["data"]
    second_data = second["data"]
    assert first_data["source_artifact_hash"] == second_data["source_artifact_hash"]
    assert first_data["evidence"] == second_data["evidence"]


def test_regress_fixture_fail(tmp_path: Path) -> None:
    """Candidate faithfulness drops 0.21 (> 0.05) → regression, verdict 'failed', exit 2."""
    expected = _load_expected("fail.json")
    exit_code, payload = _seed_and_invoke(tmp_path, "fail_baseline.json", "fail_candidate.json")

    assert exit_code == expected["_meta"]["exit_code"] == 2
    _assert_envelope_shape(payload, status="ok")
    _assert_no_t3_release_vocabulary(payload)

    data = payload["data"]
    exp = expected["data"]
    for field in EXACT_REPORT_FIELDS:
        assert data[field] == exp[field], f"contract field drift: {field}"
    assert data["status"] == "failed"
    assert data["regression_detected"] is True
    _assert_hash_anchored_evidence(data)

    actual_by_metric = {r["metric"]: r for r in data["results"]}
    exp_by_metric = {r["metric"]: r for r in exp["results"]}
    for metric, result in actual_by_metric.items():
        golden = exp_by_metric[metric]
        assert result["regression"] == golden["regression"], metric
        for field in TOLERANCE_RESULT_FIELDS:
            assert result[field] == pytest.approx(golden[field], abs=1e-3), f"{metric}.{field}"

    # The regressed metric carries a significant negative effect.
    faith = actual_by_metric["faithfulness"]
    assert faith["regression"] is True
    assert faith["diff"] < 0
    assert faith["effect_size"] < 0
    assert faith["p_value"] < 0.05
    assert faith["is_significant"] is True
    assert faith["effect_level"] in EFFECT_LEVELS
    # The stable metric does not regress.
    assert actual_by_metric["answer_relevancy"]["regression"] is False


def test_regress_fixture_incomplete_provenance(tmp_path: Path) -> None:
    """No shared metrics_evaluated → gate abstains: status 'error', exit 1, data null."""
    expected = _load_expected("incomplete_provenance.json")
    exit_code, payload = _seed_and_invoke(
        tmp_path, "incomplete_baseline.json", "incomplete_candidate.json"
    )

    assert exit_code == expected["_meta"]["exit_code"] == 1
    _assert_envelope_shape(payload, status="error")
    _assert_no_t3_release_vocabulary(payload)

    # Abstain semantics: never a passed/failed verdict, no report payload.
    assert payload["data"] is None
    assert payload["error_type"] == expected["error_type"] == "ValueError"
    assert payload["message"] == expected["message"]
    assert "shared metrics" in payload["message"]
    # Stable machine-readable taxonomy: error_code is the contract (error_type kept for compat).
    assert payload["error_code"] == expected["error_code"] == "EVAL_INCOMPLETE_PROVENANCE"
    assert payload["error_category"] == expected["error_category"] == "provenance"
