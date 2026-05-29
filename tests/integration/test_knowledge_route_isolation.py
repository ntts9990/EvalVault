"""Live FastAPI knowledge-route project isolation (G4 Phase 1-2C).

Drives the real app via TestClient with a real identity store + real JWT. The
knowledge surface (`/api/v1/knowledge/*`) is isolated into project-owned
subdirectories (`data/raw/<project_id>`, `data/kg/<project_id>`) with
project-scoped jobs; legacy (no project context) keeps the shared
KNOWLEDGE_*_TOKENS behavior. CWD is moved to tmp so data/raw + data/kg never
touch the repo.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from evalvault.adapters.inbound.api.main import create_app
from evalvault.adapters.inbound.api.routers import knowledge
from evalvault.adapters.outbound.auth.jwt_token_service import JwtTokenService
from evalvault.adapters.outbound.storage.sqlite_identity import SqliteIdentityStorageAdapter
from evalvault.config.model_config import reset_model_config
from evalvault.config.settings import reset_settings
from evalvault.domain.entities.auth import Membership, Project, Role, User

SECRET = "knowledge-isolation-secret"


class _FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed:{password}"


@pytest.fixture(autouse=True)
def clear_kg_jobs():
    knowledge.KG_JOBS.clear()
    yield
    knowledge.KG_JOBS.clear()


@pytest.fixture
def wired(tmp_path, monkeypatch):
    reset_settings()
    reset_model_config()
    monkeypatch.delenv("API_AUTH_TOKENS", raising=False)
    monkeypatch.delenv("KNOWLEDGE_READ_TOKENS", raising=False)
    monkeypatch.delenv("KNOWLEDGE_WRITE_TOKENS", raising=False)
    monkeypatch.chdir(tmp_path)

    identity = SqliteIdentityStorageAdapter(db_path=tmp_path / "identity.db")
    identity.create_project(Project(name="A", slug="a", id="proj-a"))
    identity.create_project(Project(name="B", slug="b", id="proj-b"))
    editor = User(email="editor@x", hashed_password="h")
    viewer = User(email="viewer@x", hashed_password="h")
    bob = User(email="bob@x", hashed_password="h")
    for user in (editor, viewer, bob):
        identity.create_user(user)
    identity.add_membership(Membership(user_id=editor.id, project_id="proj-a", role=Role.editor))
    identity.add_membership(Membership(user_id=viewer.id, project_id="proj-a", role=Role.viewer))
    identity.add_membership(Membership(user_id=bob.id, project_id="proj-b", role=Role.editor))

    tokens = JwtTokenService(secret=SECRET)

    with patch("evalvault.adapters.inbound.api.main.create_adapter", return_value=MagicMock()):
        app = create_app()
        app.state.identity_store = identity
        app.state.token_service = tokens
        app.state.password_hasher = _FakeHasher()
        with TestClient(app) as client:
            yield SimpleNamespace(
                client=client, tokens=tokens, editor=editor, viewer=viewer, bob=bob
            )


def _auth(env, user):
    return {"Authorization": f"Bearer {env.tokens.issue_access_token(user.id)}"}


def _upload(env, user, project_id, *, filename="doc.txt", token=None):
    headers: dict[str, str] = {}
    if user is not None:
        headers.update(_auth(env, user))
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if project_id is not None:
        headers["X-Project-Id"] = project_id
    return env.client.post(
        "/api/v1/knowledge/upload",
        files={"files": (filename, b"hello world", "text/plain")},
        headers=headers,
    )


def _list(env, user, project_id, *, token=None):
    headers: dict[str, str] = {}
    if user is not None:
        headers.update(_auth(env, user))
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if project_id is not None:
        headers["X-Project-Id"] = project_id
    return env.client.get("/api/v1/knowledge/files", headers=headers)


# --- upload + list scoping ------------------------------------------------


def test_editor_upload_then_member_list_is_scoped(wired):
    assert _upload(wired, wired.editor, "proj-a", filename="alpha.txt").status_code == 200
    resp = _list(wired, wired.editor, "proj-a")
    assert resp.status_code == 200
    assert "alpha.txt" in resp.json()


def test_knowledge_upload_is_cross_project_isolated(wired):
    assert _upload(wired, wired.editor, "proj-a", filename="secret-a.txt").status_code == 200
    resp = _list(wired, wired.bob, "proj-b")
    assert resp.status_code == 200
    assert "secret-a.txt" not in resp.json()


def test_list_non_member_is_404(wired):
    assert _list(wired, wired.bob, "proj-a").status_code == 404


def test_list_with_project_but_no_principal_is_401(wired):
    assert _list(wired, None, "proj-a").status_code == 401


def test_upload_with_project_but_no_principal_is_401(wired):
    assert _upload(wired, None, "proj-a").status_code == 401


def test_viewer_cannot_upload_403(wired):
    assert _upload(wired, wired.viewer, "proj-a").status_code == 403


def test_traversal_filename_still_rejected_under_project(wired):
    assert _upload(wired, wired.editor, "proj-a", filename="../evil.txt").status_code == 400


# --- build + job/stats isolation ------------------------------------------


def test_viewer_cannot_build_403(wired):
    resp = wired.client.post(
        "/api/v1/knowledge/build",
        json={},
        headers={**_auth(wired, wired.viewer), "X-Project-Id": "proj-a"},
    )
    assert resp.status_code == 403


def test_build_job_status_is_project_scoped(wired):
    build = wired.client.post(
        "/api/v1/knowledge/build",
        json={},
        headers={**_auth(wired, wired.editor), "X-Project-Id": "proj-a"},
    )
    assert build.status_code == 202
    job_id = build.json()["job_id"]

    # Owner project can read its job.
    own = wired.client.get(
        f"/api/v1/knowledge/jobs/{job_id}",
        headers={**_auth(wired, wired.editor), "X-Project-Id": "proj-a"},
    )
    assert own.status_code == 200

    # A different project must not see the job (404, no leak).
    foreign = wired.client.get(
        f"/api/v1/knowledge/jobs/{job_id}",
        headers={**_auth(wired, wired.bob), "X-Project-Id": "proj-b"},
    )
    assert foreign.status_code == 404


def test_stats_requires_membership(wired):
    ok = wired.client.get(
        "/api/v1/knowledge/stats",
        headers={**_auth(wired, wired.editor), "X-Project-Id": "proj-a"},
    )
    assert ok.status_code == 200
    denied = wired.client.get(
        "/api/v1/knowledge/stats",
        headers={**_auth(wired, wired.bob), "X-Project-Id": "proj-a"},
    )
    assert denied.status_code == 404


def test_stats_uses_project_output_dir(wired):
    project_graph = "data/kg/proj-a/knowledge_graph.json"

    Path(project_graph).parent.mkdir(parents=True, exist_ok=True)
    Path(project_graph).write_text("{}", encoding="utf-8")

    project_a = wired.client.get(
        "/api/v1/knowledge/stats",
        headers={**_auth(wired, wired.editor), "X-Project-Id": "proj-a"},
    )
    assert project_a.status_code == 200
    assert project_a.json()["status"] == "available"

    project_b = wired.client.get(
        "/api/v1/knowledge/stats",
        headers={**_auth(wired, wired.bob), "X-Project-Id": "proj-b"},
    )
    assert project_b.status_code == 200
    assert project_b.json()["status"] == "not_built"


# --- legacy (no project context) shared-token behavior --------------------


def test_project_identity_bypasses_legacy_knowledge_tokens(wired, monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_READ_TOKENS", "rtok")
    monkeypatch.setenv("KNOWLEDGE_WRITE_TOKENS", "wtok")
    reset_settings()

    assert _upload(wired, wired.editor, "proj-a", filename="identity.txt").status_code == 200
    listed = _list(wired, wired.editor, "proj-a")
    assert listed.status_code == 200
    assert "identity.txt" in listed.json()


def test_project_shared_knowledge_token_is_not_membership(wired, monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_READ_TOKENS", "rtok")
    monkeypatch.setenv("KNOWLEDGE_WRITE_TOKENS", "wtok")
    reset_settings()

    assert _upload(wired, None, "proj-a", token="wtok").status_code == 401
    assert _list(wired, None, "proj-a", token="rtok").status_code == 401


def test_legacy_write_token_required_without_project(wired, monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_WRITE_TOKENS", "wtok")
    reset_settings()

    # Correct shared write token, no project → allowed (legacy).
    assert _upload(wired, None, None, token="wtok").status_code == 200
    # Missing token while write tokens are configured → 403 (legacy).
    assert _upload(wired, None, None, token=None).status_code == 403


def test_legacy_read_without_tokens_is_open(wired):
    # No KNOWLEDGE_*_TOKENS configured and no project → legacy open behavior.
    assert _list(wired, None, None).status_code == 200
