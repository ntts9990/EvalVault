from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app
from evalvault.domain.services.readiness_proof_service import (
    EVALVAULT_READINESS_SCHEMA_VERSION,
    REQUIRED_EVALVAULT_G4_GATES,
    build_evalvault_readiness_proof,
)

runner = CliRunner()

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "e2e" / "regression_gate"


def _ready_gates() -> dict[str, bool]:
    return dict.fromkeys(REQUIRED_EVALVAULT_G4_GATES, True)


def _commands() -> list[dict[str, object]]:
    return [{"name": "focused-suite", "passed": True, "exit_code": 0}]


def test_build_readiness_proof_ready_output() -> None:
    proof = build_evalvault_readiness_proof(
        commit="abc123",
        gates=_ready_gates(),
        commands=_commands(),
    )

    assert proof["schema_version"] == EVALVAULT_READINESS_SCHEMA_VERSION
    assert proof["repo"] == "EvalVault"
    assert proof["commit"] == "abc123"
    assert proof["status"] == "ready"
    assert proof["gates"] == _ready_gates()
    assert proof["commands"] == _commands()


def test_build_readiness_proof_rejects_missing_gate() -> None:
    gates = _ready_gates()
    gates.pop("mcp_project_isolation")

    try:
        build_evalvault_readiness_proof(commit="abc123", gates=gates, commands=_commands())
    except ValueError as exc:
        assert "missing gates: mcp_project_isolation" in str(exc)
    else:  # pragma: no cover - assertion branch
        raise AssertionError("expected missing gate to be rejected")


def test_build_readiness_proof_rejects_failing_command() -> None:
    try:
        build_evalvault_readiness_proof(
            commit="abc123",
            gates=_ready_gates(),
            commands=[{"name": "focused-suite", "passed": False, "exit_code": 1}],
        )
    except ValueError as exc:
        assert "did not pass" in str(exc)
    else:  # pragma: no cover - assertion branch
        raise AssertionError("expected failing command to be rejected")


def test_regress_readiness_proof_cli_writes_stable_json(tmp_path: Path) -> None:
    output = tmp_path / "proof.json"
    result = runner.invoke(
        app,
        [
            "regress-readiness-proof",
            "--evidence",
            str(FIXTURE_DIR / "g4_readiness_evidence.json"),
            "--commit",
            "abc123",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.stdout
    stdout_payload = json.loads(result.stdout)
    file_payload = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert file_payload["schema_version"] == EVALVAULT_READINESS_SCHEMA_VERSION
    assert file_payload["status"] == "ready"
    assert sorted(file_payload["gates"]) == sorted(REQUIRED_EVALVAULT_G4_GATES)
