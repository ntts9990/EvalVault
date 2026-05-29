"""Live FastAPI run-route project isolation (EvalVault G4 wiring).

Drives the real app via TestClient with a REAL WebUIAdapter over real SQLite run
storage + a real identity store + real JWT, so the route guard exercises
``BaseSQLStorageAdapter.get_run(project_id=...)`` and the principal/denial policy
end to end. Backward compatibility (no project context) is asserted too.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from evalvault.adapters.inbound.api.adapter import WebUIAdapter
from evalvault.adapters.inbound.api.main import create_app
from evalvault.adapters.outbound.auth.jwt_token_service import JwtTokenService
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.adapters.outbound.storage.sqlite_identity import SqliteIdentityStorageAdapter
from evalvault.config.model_config import reset_model_config
from evalvault.config.settings import reset_settings
from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.entities.auth import ApiKey, Membership, Project, Role, User

SECRET = "route-isolation-secret"


class _FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed:{password}"


def _run(run_id: str, project_id: str) -> EvaluationRun:
    return EvaluationRun(
        run_id=run_id,
        dataset_name="insurance-qa",
        model_name="gpt-5-nano",
        started_at=datetime(2026, 1, 2, 10, 0, 0),
        project_id=project_id,
        metrics_evaluated=["faithfulness"],
        thresholds={"faithfulness": 0.7},
        results=[
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
            )
        ],
    )


@pytest.fixture
def wired(tmp_path, monkeypatch):
    reset_settings()
    reset_model_config()
    monkeypatch.delenv("API_AUTH_TOKENS", raising=False)

    storage = SQLiteStorageAdapter(db_path=tmp_path / "runs.db")
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

    tokens = JwtTokenService(secret=SECRET)

    with patch("evalvault.adapters.inbound.api.main.create_adapter", return_value=adapter):
        app = create_app()
        app.state.identity_store = identity
        app.state.token_service = tokens
        app.state.password_hasher = _FakeHasher()
        with TestClient(app) as client:
            yield SimpleNamespace(
                adapter=adapter,
                client=client,
                identity=identity,
                tokens=tokens,
                editor=editor,
                viewer=viewer,
            )


def _auth(env, user):
    return {"Authorization": f"Bearer {env.tokens.issue_access_token(user.id)}"}


# --- backward compatibility (no project context) --------------------------


def test_legacy_list_without_project_returns_all(wired):
    resp = wired.client.get("/api/v1/runs/")
    assert resp.status_code == 200
    assert {r["run_id"] for r in resp.json()} >= {"run-a", "run-b"}


def test_legacy_get_without_project_succeeds(wired):
    resp = wired.client.get("/api/v1/runs/run-b")
    assert resp.status_code == 200
    assert resp.json()["summary"]["run_id"] == "run-b"


# --- list scoping ----------------------------------------------------------


def test_list_scoped_to_member_project(wired):
    resp = wired.client.get(
        "/api/v1/runs/", headers={**_auth(wired, wired.editor), "X-Project-Id": "proj-a"}
    )
    assert resp.status_code == 200
    assert {r["run_id"] for r in resp.json()} == {"run-a"}


def test_list_with_project_but_no_principal_is_401(wired):
    resp = wired.client.get("/api/v1/runs/", headers={"X-Project-Id": "proj-a"})
    assert resp.status_code == 401


def test_list_non_member_project_is_404(wired):
    resp = wired.client.get(
        "/api/v1/runs/", headers={**_auth(wired, wired.editor), "X-Project-Id": "proj-b"}
    )
    assert resp.status_code == 404


def test_identity_jwt_still_works_when_legacy_service_tokens_are_configured(
    wired, monkeypatch
):
    monkeypatch.setenv("API_AUTH_TOKENS", "shared-service-token")
    reset_settings()

    resp = wired.client.get(
        "/api/v1/runs/", headers={**_auth(wired, wired.editor), "X-Project-Id": "proj-a"}
    )

    assert resp.status_code == 200
    assert {r["run_id"] for r in resp.json()} == {"run-a"}


def test_shared_service_token_does_not_grant_project_membership(wired, monkeypatch):
    monkeypatch.setenv("API_AUTH_TOKENS", "shared-service-token")
    reset_settings()

    resp = wired.client.get(
        "/api/v1/runs/",
        headers={"Authorization": "Bearer shared-service-token", "X-Project-Id": "proj-a"},
    )

    assert resp.status_code == 401


def test_shared_service_token_without_project_keeps_legacy_access(wired, monkeypatch):
    monkeypatch.setenv("API_AUTH_TOKENS", "shared-service-token")
    reset_settings()

    resp = wired.client.get(
        "/api/v1/runs/", headers={"Authorization": "Bearer shared-service-token"}
    )

    assert resp.status_code == 200
    assert {r["run_id"] for r in resp.json()} >= {"run-a", "run-b"}


def test_user_api_key_project_scope_works_without_jwt_secret(wired):
    raw_key = "ev_editor.secret"
    wired.identity.create_api_key(
        ApiKey(
            user_id=wired.editor.id,
            name="ci",
            prefix="ev_editor",
            hashed_key=f"hashed:{raw_key}",
        )
    )
    wired.client.app.state.token_service = None

    resp = wired.client.get(
        "/api/v1/runs/",
        headers={"Authorization": f"Bearer {raw_key}", "X-Project-Id": "proj-a"},
    )

    assert resp.status_code == 200
    assert {r["run_id"] for r in resp.json()} == {"run-a"}


# --- get scoping (router guard) -------------------------------------------


def test_get_own_run_with_project_succeeds(wired):
    resp = wired.client.get(
        "/api/v1/runs/run-a", headers={**_auth(wired, wired.editor), "X-Project-Id": "proj-a"}
    )
    assert resp.status_code == 200


def test_get_foreign_run_under_own_project_is_404(wired):
    resp = wired.client.get(
        "/api/v1/runs/run-b", headers={**_auth(wired, wired.editor), "X-Project-Id": "proj-a"}
    )
    assert resp.status_code == 404


def test_get_with_project_but_no_principal_is_401(wired):
    resp = wired.client.get("/api/v1/runs/run-a", headers={"X-Project-Id": "proj-a"})
    assert resp.status_code == 401


def test_compare_foreign_run_is_404(wired):
    resp = wired.client.get(
        "/api/v1/runs/compare",
        params={"base": "run-a", "target": "run-b"},
        headers={**_auth(wired, wired.editor), "X-Project-Id": "proj-a"},
    )
    assert resp.status_code == 404


def test_prompt_diff_static_route_is_not_shadowed_by_run_id_route(wired, monkeypatch):
    def _fake_compare(base_run_id, target_run_id, *, max_lines=40, include_diff=True):
        return {
            "base_run_id": base_run_id,
            "target_run_id": target_run_id,
            "summary": [],
            "diffs": [],
        }

    monkeypatch.setattr(wired.adapter, "compare_prompt_sets", _fake_compare)

    resp = wired.client.get(
        "/api/v1/runs/prompt-diff",
        params={"base_run_id": "run-a", "target_run_id": "run-a"},
        headers={**_auth(wired, wired.editor), "X-Project-Id": "proj-a"},
    )

    assert resp.status_code == 200
    assert resp.json()["base_run_id"] == "run-a"


# --- role gates (writes) ---------------------------------------------------


def test_viewer_cannot_save_feedback_403(wired):
    resp = wired.client.post(
        "/api/v1/runs/run-a/feedback",
        json={"test_case_id": "tc-1", "thumb_feedback": "up"},
        headers={**_auth(wired, wired.viewer), "X-Project-Id": "proj-a"},
    )
    assert resp.status_code == 403


def test_viewer_cannot_start_run_403(wired):
    resp = wired.client.post(
        "/api/v1/runs/start",
        json={
            "dataset_path": "data/datasets/x.json",
            "metrics": ["faithfulness"],
            "model": "gpt-5-nano",
            "project_id": "proj-a",
        },
        headers=_auth(wired, wired.viewer),
    )
    assert resp.status_code == 403
