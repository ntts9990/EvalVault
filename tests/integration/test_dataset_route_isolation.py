"""Live FastAPI non-run route project isolation: datasets + retriever-docs (G4 Block 1).

Drives the real app via TestClient with a real WebUIAdapter + real identity store
+ real JWT. Dataset/retriever-doc uploads are isolated into project-owned
subdirectories; legacy (no project context) behavior is preserved. CWD is moved
to a tmp dir so ``data/datasets`` / ``data/retriever_docs`` never touch the repo.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from evalvault.adapters.inbound.api.adapter import WebUIAdapter
from evalvault.adapters.inbound.api.main import create_app
from evalvault.adapters.inbound.api.path_safety import UnsafePathError
from evalvault.adapters.outbound.auth.jwt_token_service import JwtTokenService
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.adapters.outbound.storage.sqlite_identity import SqliteIdentityStorageAdapter
from evalvault.config.model_config import reset_model_config
from evalvault.config.settings import reset_settings
from evalvault.domain.entities.auth import Membership, Project, Role, User

SECRET = "dataset-isolation-secret"


class _FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed:{password}"


@pytest.fixture
def wired(tmp_path, monkeypatch):
    reset_settings()
    reset_model_config()
    monkeypatch.delenv("API_AUTH_TOKENS", raising=False)
    # Confine relative data/datasets + data/retriever_docs writes to tmp.
    monkeypatch.chdir(tmp_path)

    adapter = WebUIAdapter(storage=SQLiteStorageAdapter(db_path=tmp_path / "runs.db"))

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

    with patch("evalvault.adapters.inbound.api.main.create_adapter", return_value=adapter):
        app = create_app()
        app.state.identity_store = identity
        app.state.token_service = tokens
        app.state.password_hasher = _FakeHasher()
        with TestClient(app) as client:
            yield SimpleNamespace(
                adapter=adapter,
                client=client,
                tokens=tokens,
                editor=editor,
                viewer=viewer,
                bob=bob,
            )


def _auth(env, user):
    return {"Authorization": f"Bearer {env.tokens.issue_access_token(user.id)}"}


def _upload(env, user, project_id, *, filename="ds.json", path="/api/v1/runs/options/datasets"):
    headers = _auth(env, user)
    if project_id is not None:
        headers["X-Project-Id"] = project_id
    return env.client.post(
        path, files={"file": (filename, b'{"k": 1}', "application/json")}, headers=headers
    )


# --- dataset upload + list scoping ----------------------------------------


def test_editor_upload_then_member_list_is_scoped(wired):
    assert _upload(wired, wired.editor, "proj-a", filename="alpha.json").status_code == 200
    resp = wired.client.get(
        "/api/v1/runs/options/datasets",
        headers={**_auth(wired, wired.editor), "X-Project-Id": "proj-a"},
    )
    assert resp.status_code == 200
    assert "alpha.json" in {d["name"] for d in resp.json()}


def test_dataset_upload_is_cross_project_isolated(wired):
    assert _upload(wired, wired.editor, "proj-a", filename="secret-a.json").status_code == 200
    # bob (member of proj-b only) lists proj-b → must not see proj-a's dataset.
    resp = wired.client.get(
        "/api/v1/runs/options/datasets",
        headers={**_auth(wired, wired.bob), "X-Project-Id": "proj-b"},
    )
    assert resp.status_code == 200
    assert "secret-a.json" not in {d["name"] for d in resp.json()}


def test_list_non_member_is_404(wired):
    resp = wired.client.get(
        "/api/v1/runs/options/datasets",
        headers={**_auth(wired, wired.bob), "X-Project-Id": "proj-a"},
    )
    assert resp.status_code == 404


def test_list_with_project_but_no_principal_is_401(wired):
    resp = wired.client.get(
        "/api/v1/runs/options/datasets", headers={"X-Project-Id": "proj-a"}
    )
    assert resp.status_code == 401


def test_viewer_cannot_upload_403(wired):
    assert _upload(wired, wired.viewer, "proj-a").status_code == 403


def test_upload_with_project_but_no_principal_is_401(wired):
    resp = wired.client.post(
        "/api/v1/runs/options/datasets",
        files={"file": ("x.json", b"{}", "application/json")},
        headers={"X-Project-Id": "proj-a"},
    )
    assert resp.status_code == 401


def test_path_traversal_filename_still_rejected_under_project(wired):
    # The previous path-safety guard must remain intact with project scoping.
    assert _upload(wired, wired.editor, "proj-a", filename="../evil.json").status_code == 400


def test_start_rejects_foreign_project_dataset_path(wired):
    foreign_dataset = Path("data/datasets/proj-b/foreign.json").resolve()
    foreign_dataset.parent.mkdir(parents=True, exist_ok=True)
    foreign_dataset.write_text("{}", encoding="utf-8")

    resp = wired.client.post(
        "/api/v1/runs/start",
        json={
            "dataset_path": str(foreign_dataset),
            "metrics": ["exact_match"],
            "model": "stub",
            "project_id": "proj-a",
        },
        headers=_auth(wired, wired.editor),
    )

    assert resp.status_code == 400


# --- backward compatibility (no project context) --------------------------


def test_legacy_upload_and_list_without_project(wired):
    assert _upload(wired, wired.editor, None, filename="legacy.json").status_code == 200
    resp = wired.client.get("/api/v1/runs/options/datasets")
    assert resp.status_code == 200
    assert "legacy.json" in {d["name"] for d in resp.json()}


# --- retriever-docs upload (same storage/path surface) --------------------


def test_retriever_docs_viewer_cannot_upload_403(wired):
    resp = _upload(
        wired,
        wired.viewer,
        "proj-a",
        filename="docs.jsonl",
        path="/api/v1/runs/options/retriever-docs",
    )
    assert resp.status_code == 403


def test_retriever_docs_editor_upload_ok(wired):
    resp = _upload(
        wired,
        wired.editor,
        "proj-a",
        filename="docs.jsonl",
        path="/api/v1/runs/options/retriever-docs",
    )
    assert resp.status_code == 200


def test_retriever_docs_no_principal_with_project_is_401(wired):
    resp = wired.client.post(
        "/api/v1/runs/options/retriever-docs",
        files={"file": ("docs.jsonl", b"hi", "text/plain")},
        headers={"X-Project-Id": "proj-a"},
    )
    assert resp.status_code == 401


def test_retriever_docs_read_rejects_foreign_project_path(wired):
    foreign_docs = Path("data/retriever_docs/proj-b/docs.jsonl").resolve()
    foreign_docs.parent.mkdir(parents=True, exist_ok=True)
    foreign_docs.write_text('{"content":"secret"}\n', encoding="utf-8")

    with pytest.raises(UnsafePathError):
        wired.adapter._build_retriever(  # noqa: SLF001 - G4 boundary regression
            {"mode": "bm25", "docs_path": str(foreign_docs)},
            wired.adapter._settings,
            project_id="proj-a",
        )
