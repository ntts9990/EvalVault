"""MCP JSON-RPC project isolation for EvalVault G4.

The HTTP MCP surface keeps legacy shared-token access for no-project calls, but
project-scoped calls must use a real identity principal (JWT/API key) carried by
the Authorization bearer token.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from evalvault.adapters.inbound.api.adapter import WebUIAdapter
from evalvault.adapters.inbound.api.main import create_app
from evalvault.adapters.inbound.api.routers import mcp as mcp_router
from evalvault.adapters.outbound.auth.jwt_token_service import JwtTokenService
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.adapters.outbound.storage.sqlite_identity import SqliteIdentityStorageAdapter
from evalvault.config.model_config import reset_model_config
from evalvault.config.settings import reset_settings
from evalvault.domain.entities.auth import ApiKey, Membership, Project, Role, User
from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult

SECRET = "mcp-project-isolation-secret"


class _FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed:{password}"


def _run(run_id: str, project_id: str) -> EvaluationRun:
    return EvaluationRun(
        run_id=run_id,
        dataset_name="sample-dataset",
        model_name="sample-model",
        project_id=project_id,
        metrics_evaluated=["faithfulness"],
        started_at=datetime(2026, 1, 2, 10, 0, 0),
        results=[
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[MetricScore(name="faithfulness", score=0.92, threshold=0.8)],
            )
        ],
    )


@pytest.fixture
def wired(tmp_path, monkeypatch):
    reset_settings()
    reset_model_config()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MCP_ENABLED", "true")
    monkeypatch.setenv("MCP_AUTH_TOKENS", "shared-mcp-token")
    monkeypatch.setenv("API_AUTH_TOKENS", "api-service-token")
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("EVALVAULT_DB_PATH", str(tmp_path / "data" / "db" / "evalvault.db"))
    reset_settings()

    db_path = tmp_path / "data" / "db" / "evalvault.db"
    storage = SQLiteStorageAdapter(db_path=db_path)
    storage.save_run(_run("run-a", "proj-a"))
    storage.save_run(_run("run-b", "proj-b"))
    adapter = WebUIAdapter(storage=storage)

    identity = SqliteIdentityStorageAdapter(db_path=tmp_path / "identity.db")
    identity.create_project(Project(name="A", slug="a", id="proj-a"))
    identity.create_project(Project(name="B", slug="b", id="proj-b"))
    editor = User(email="editor@x", hashed_password="h")
    viewer = User(email="viewer@x", hashed_password="h")
    identity.create_user(editor)
    identity.create_user(viewer)
    identity.add_membership(Membership(user_id=editor.id, project_id="proj-a", role=Role.editor))
    identity.add_membership(Membership(user_id=viewer.id, project_id="proj-a", role=Role.viewer))
    raw_api_key = "ev_editor.secret"
    identity.create_api_key(
        ApiKey(
            user_id=editor.id,
            name="ci",
            prefix="ev_editor",
            hashed_key=_FakeHasher().hash(raw_api_key),
        )
    )
    tokens = JwtTokenService(secret=SECRET)

    with patch("evalvault.adapters.inbound.api.main.create_adapter", return_value=adapter):
        app = create_app()
        app.state.identity_store = identity
        app.state.token_service = tokens
        app.state.password_hasher = _FakeHasher()
        with TestClient(app) as client:
            yield SimpleNamespace(
                client=client,
                db_path=db_path,
                editor=editor,
                raw_api_key=raw_api_key,
                tokens=tokens,
            )

    reset_settings()


def _call_list_runs(wired, token: str, args: dict) -> dict:
    response = wired.client.post(
        "/api/v1/mcp",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "list_runs",
                "arguments": {"db_path": str(wired.db_path), **args},
            },
        },
    )
    assert response.status_code == 200
    return response.json()["result"]["structuredContent"]


def test_user_api_key_scopes_project_mcp_list_runs(wired) -> None:
    payload = _call_list_runs(wired, wired.raw_api_key, {"project_id": "proj-a"})

    assert payload["errors"] == []
    assert {run["run_id"] for run in payload["runs"]} == {"run-a"}


def test_user_jwt_scopes_project_mcp_list_runs(wired) -> None:
    token = wired.tokens.issue_access_token(wired.editor.id)
    payload = _call_list_runs(wired, token, {"project_id": "proj-a"})

    assert payload["errors"] == []
    assert {run["run_id"] for run in payload["runs"]} == {"run-a"}


def test_shared_mcp_token_without_project_keeps_legacy_access(wired) -> None:
    payload = _call_list_runs(wired, "shared-mcp-token", {})

    assert payload["errors"] == []
    assert {run["run_id"] for run in payload["runs"]} >= {"run-a", "run-b"}


def test_shared_mcp_token_does_not_probe_identity(wired, monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("shared MCP service token should not resolve identity")

    monkeypatch.setattr(mcp_router, "resolve_bearer_principal", fail_if_called)

    payload = _call_list_runs(wired, "shared-mcp-token", {})

    assert payload["errors"] == []
    assert {run["run_id"] for run in payload["runs"]} >= {"run-a", "run-b"}


def test_shared_mcp_token_does_not_grant_project_membership(wired) -> None:
    payload = _call_list_runs(wired, "shared-mcp-token", {"project_id": "proj-a"})

    assert [error["code"] for error in payload["errors"]] == ["EVAL_AUTH_REQUIRED"]
