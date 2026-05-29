"""End-to-end project-isolation proof (EvalVault G4).

Wires the REAL stack — SQLite identity store + SQLite run storage + JWT token
service + principal resolution + authorization policy — and proves cross-project
run get/list/compare denial, role gating, and principal resolution from both a
session JWT and an API key. No FastAPI app and no external services.

This is the integration evidence for the G4 lanes "API login/API-key principal
resolution", "current project selection", "viewer/editor/admin behavior", and
"cross-project run list/get/compare denial". Live FastAPI route wiring of these
primitives is the remaining step (see docs/phase1-real-adapter-readiness.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pytest

from evalvault.adapters.inbound.api.principal import (
    InsufficientRoleError,
    PrincipalRequiredError,
    ProjectAccessDeniedError,
    require_member,
    require_role,
    resolve_current_project_id,
    resolve_principal,
)
from evalvault.adapters.outbound.auth.jwt_token_service import JwtTokenService
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.adapters.outbound.storage.sqlite_identity import SqliteIdentityStorageAdapter
from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.auth import ApiKey, Membership, Project, Role, User


class _FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed:{password}"


@dataclass
class _Env:
    identity: SqliteIdentityStorageAdapter
    runs: SQLiteStorageAdapter
    tokens: JwtTokenService
    hasher: _FakeHasher
    alice: User  # editor in project-a
    bob: User  # editor in project-b
    viewer: User  # viewer in project-a


def _run(run_id: str, project_id: str) -> EvaluationRun:
    return EvaluationRun(
        run_id=run_id,
        dataset_name="insurance-qa",
        model_name="gpt-5-nano",
        started_at=datetime(2026, 1, 2, 10, 0, 0),
        project_id=project_id,
    )


@pytest.fixture
def env(tmp_path) -> _Env:
    identity = SqliteIdentityStorageAdapter(db_path=tmp_path / "identity.db")
    runs = SQLiteStorageAdapter(db_path=tmp_path / "runs.db")
    hasher = _FakeHasher()

    identity.create_project(Project(name="A", slug="a", id="project-a"))
    identity.create_project(Project(name="B", slug="b", id="project-b"))

    alice = User(email="alice@x", hashed_password="h")
    bob = User(email="bob@x", hashed_password="h")
    viewer = User(email="viewer@x", hashed_password="h")
    for user in (alice, bob, viewer):
        identity.create_user(user)
    identity.add_membership(Membership(user_id=alice.id, project_id="project-a", role=Role.editor))
    identity.add_membership(Membership(user_id=bob.id, project_id="project-b", role=Role.editor))
    identity.add_membership(Membership(user_id=viewer.id, project_id="project-a", role=Role.viewer))

    runs.save_run(_run("run-a", "project-a"))
    runs.save_run(_run("run-b", "project-b"))

    return _Env(identity, runs, JwtTokenService(secret="it-secret"), hasher, alice, bob, viewer)


# --- principal resolution -------------------------------------------------


def test_resolve_principal_from_session_jwt(env):
    token = env.tokens.issue_access_token(env.alice.id)
    principal = resolve_principal(
        token, identity_store=env.identity, token_service=env.tokens, hasher=env.hasher
    )
    assert principal is not None
    assert principal.user_id == env.alice.id
    assert principal.role_in("project-a") is Role.editor
    assert not principal.is_member("project-b")


def test_resolve_principal_from_api_key(env):
    raw = "ev_alice.supersecret"
    env.identity.create_api_key(
        ApiKey(
            user_id=env.alice.id,
            name="cli",
            hashed_key=env.hasher.hash(raw),
            prefix="ev_alice",
        )
    )
    principal = resolve_principal(
        raw, identity_store=env.identity, token_service=env.tokens, hasher=env.hasher
    )
    assert principal is not None and principal.user_id == env.alice.id


def test_resolve_principal_rejects_garbage_and_empty(env):
    for bad in (None, "", "not-a-token", "ev_unknown.secret"):
        assert (
            resolve_principal(
                bad, identity_store=env.identity, token_service=env.tokens, hasher=env.hasher
            )
            is None
        )


# --- current-project precedence -------------------------------------------


def test_current_project_precedence():
    assert resolve_current_project_id(header="h", query="q", body="b") == "h"
    assert resolve_current_project_id(header=None, query="q", body="b") == "q"
    assert resolve_current_project_id(header=None, query=None, body="b") == "b"
    assert resolve_current_project_id() is None


# --- cross-project denial (storage-enforced + policy) ---------------------


def _principal(env, user):
    token = env.tokens.issue_access_token(user.id)
    return resolve_principal(
        token, identity_store=env.identity, token_service=env.tokens, hasher=env.hasher
    )


def test_get_run_cross_project_denied(env):
    alice = _principal(env, env.alice)
    # Own-project run resolves under the principal's project.
    require_member(alice, "project-a")
    assert env.runs.get_run("run-a", project_id="project-a").run_id == "run-a"
    # Foreign project: policy denies (404) AND storage refuses to leak existence.
    with pytest.raises(ProjectAccessDeniedError):
        require_member(alice, "project-b")
    with pytest.raises(KeyError):
        env.runs.get_run("run-b", project_id="project-a")


def test_list_runs_scoped_to_member_project(env):
    a_ids = {r.run_id for r in env.runs.list_runs(project_id="project-a")}
    b_ids = {r.run_id for r in env.runs.list_runs(project_id="project-b")}
    assert a_ids == {"run-a"}
    assert b_ids == {"run-b"}


def test_compare_denied_when_one_run_is_foreign(env):
    alice = _principal(env, env.alice)
    # Comparing run-a (own) vs run-b (foreign): the foreign side is denied.
    require_member(alice, "project-a")
    with pytest.raises(ProjectAccessDeniedError):
        require_member(alice, "project-b")


def test_missing_principal_is_unauthorized(env):
    with pytest.raises(PrincipalRequiredError):
        require_member(None, "project-a")


# --- role gates (viewer/editor/admin) -------------------------------------


def test_viewer_can_read_but_not_write(env):
    viewer = _principal(env, env.viewer)
    # read ok
    require_role(viewer, "project-a", Role.viewer)
    # write denied
    with pytest.raises(InsufficientRoleError):
        require_role(viewer, "project-a", Role.editor)


def test_editor_can_write(env):
    alice = _principal(env, env.alice)
    require_role(alice, "project-a", Role.editor)  # no raise


def test_non_member_write_is_denied_as_not_found(env):
    bob = _principal(env, env.bob)  # member of project-b only
    with pytest.raises(ProjectAccessDeniedError):
        require_role(bob, "project-a", Role.viewer)
