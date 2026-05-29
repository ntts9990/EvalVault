"""Identity storage CRUD + admin bootstrap (EvalVault G4).

Fast, local SQLite only. Proves the identity persistence + membership resolution
+ idempotent admin bootstrap lanes required by the G4 test spec.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from evalvault.adapters.outbound.storage.sqlite_identity import SqliteIdentityStorageAdapter
from evalvault.domain.entities.auth import (
    DEFAULT_PROJECT_ID,
    ApiKey,
    Membership,
    Project,
    RefreshToken,
    Role,
    User,
)
from evalvault.domain.services.identity_bootstrap import bootstrap_admin


class _FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed:{password}"


@pytest.fixture
def store(tmp_path):
    return SqliteIdentityStorageAdapter(db_path=tmp_path / "identity.db")


def test_user_crud_round_trip(store):
    user = User(email="a@example.com", hashed_password="h")
    store.create_user(user)
    assert store.get_user(user.id).email == "a@example.com"
    assert store.get_user_by_email("a@example.com").id == user.id
    assert store.get_user("missing") is None
    assert store.get_user_by_email("nobody@example.com") is None


def test_project_crud_round_trip(store):
    project = Project(name="Insurance QA", slug="insurance-qa")
    store.create_project(project)
    assert store.get_project(project.id).slug == "insurance-qa"
    assert store.get_project_by_slug("insurance-qa").id == project.id
    assert store.get_project("missing") is None


def test_membership_resolution(store):
    store.add_membership(Membership(user_id="u1", project_id="p1", role=Role.editor))
    store.add_membership(Membership(user_id="u1", project_id="p2", role=Role.viewer))
    m = store.get_membership("u1", "p1")
    assert m is not None and m.role is Role.editor
    assert store.get_membership("u1", "p-none") is None
    assert {m.project_id for m in store.list_memberships_for_user("u1")} == {"p1", "p2"}


def test_api_key_lookup_and_touch(store):
    key = ApiKey(user_id="u1", name="ci", hashed_key="hk", prefix="ev_abc")
    store.create_api_key(key)
    found = store.get_api_key_by_prefix("ev_abc")
    assert found is not None and found.user_id == "u1"
    when = datetime(2026, 5, 29, tzinfo=UTC)
    store.touch_api_key(key.id, when)
    assert store.get_api_key_by_prefix("ev_abc").last_used_at == when


def test_revoked_api_key_not_returned(store):
    key = ApiKey(user_id="u1", name="ci", hashed_key="hk", prefix="ev_rev", revoked=True)
    store.create_api_key(key)
    assert store.get_api_key_by_prefix("ev_rev") is None


def test_refresh_token_round_trip_and_revoke(store):
    token = RefreshToken(
        user_id="u1",
        token_hash="th",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    store.create_refresh_token(token)
    assert store.get_refresh_token("th").user_id == "u1"
    store.revoke_refresh_token(token.id)
    assert store.get_refresh_token("th").revoked is True


def test_bootstrap_admin_creates_user_project_membership(store):
    user, project = bootstrap_admin(
        store, _FakeHasher(), email="admin@example.com", password="pw"
    )
    assert user.is_superuser is True
    assert store.get_user_by_email("admin@example.com") is not None
    # Default project id equals the storage default so legacy runs belong to it.
    assert project.id == DEFAULT_PROJECT_ID
    membership = store.get_membership(user.id, project.id)
    assert membership is not None and membership.role is Role.admin


def test_bootstrap_admin_is_idempotent(store):
    u1, p1 = bootstrap_admin(store, _FakeHasher(), email="admin@example.com", password="pw")
    u2, p2 = bootstrap_admin(store, _FakeHasher(), email="admin@example.com", password="pw")
    assert u1.id == u2.id
    assert p1.id == p2.id
    assert len(store.list_memberships_for_user(u1.id)) == 1
