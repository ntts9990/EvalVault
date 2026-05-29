"""EvalVault G4 readiness proof builder.

The proof is intentionally plain JSON data. It lets downstream orchestrators
verify that EvalVault's repo-local gates are green without importing EvalVault
code or trusting ad hoc prose.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

EVALVAULT_READINESS_SCHEMA_VERSION = "evalvault.g4-readiness-proof.v1"
REQUIRED_EVALVAULT_G4_GATES = (
    "run_route_project_isolation",
    "dataset_route_project_isolation",
    "knowledge_route_project_isolation",
    "mcp_project_isolation",
    "postgres_identity_parity",
    "evidence_source_hash_fields",
)


def build_evalvault_readiness_proof(
    *,
    commit: str,
    gates: Mapping[str, Any],
    commands: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a validated EvalVault G4 readiness proof."""

    normalized_commit = commit.strip()
    if not normalized_commit:
        raise ValueError("readiness proof commit must be non-empty")

    normalized_gates = _normalize_gates(gates)
    normalized_commands = _normalize_commands(commands)
    return {
        "schema_version": EVALVAULT_READINESS_SCHEMA_VERSION,
        "repo": "EvalVault",
        "commit": normalized_commit,
        "status": "ready",
        "gates": normalized_gates,
        "commands": normalized_commands,
    }


def _normalize_gates(gates: Mapping[str, Any]) -> dict[str, bool]:
    actual = set(gates)
    required = set(REQUIRED_EVALVAULT_G4_GATES)
    if actual != required:
        missing = sorted(required - actual)
        unknown = sorted(actual - required)
        details: list[str] = []
        if missing:
            details.append("missing gates: " + ", ".join(missing))
        if unknown:
            details.append("unknown gates: " + ", ".join(unknown))
        raise ValueError("; ".join(details))

    failing = sorted(name for name, passed in gates.items() if passed is not True)
    if failing:
        raise ValueError("failing gates: " + ", ".join(failing))
    return dict.fromkeys(REQUIRED_EVALVAULT_G4_GATES, True)


def _normalize_commands(commands: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not commands:
        raise ValueError("readiness proof commands must be non-empty")

    normalized: list[dict[str, Any]] = []
    for index, command in enumerate(commands):
        name = command.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"readiness proof command {index} name must be non-empty")
        if command.get("passed") is not True:
            raise ValueError(f"readiness proof command {name!r} did not pass")

        normalized_command: dict[str, Any] = {
            "name": name.strip(),
            "passed": True,
        }
        for optional_field in ("command", "exit_code", "summary", "artifact"):
            value = command.get(optional_field)
            if value is not None:
                normalized_command[optional_field] = value
        normalized.append(normalized_command)
    return normalized


__all__ = [
    "EVALVAULT_READINESS_SCHEMA_VERSION",
    "REQUIRED_EVALVAULT_G4_GATES",
    "build_evalvault_readiness_proof",
]
