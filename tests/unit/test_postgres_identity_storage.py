from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from evalvault.adapters.outbound.storage import postgres_identity
from evalvault.adapters.outbound.storage.postgres_identity import PostgresIdentityStorageAdapter
from evalvault.domain.entities.auth import ApiKey, Membership, Project, RefreshToken, Role, User


def _mock_connect(monkeypatch):
    conn = MagicMock()
    connect = MagicMock()
    connect.return_value.__enter__.return_value = conn
    connect.return_value.__exit__.return_value = None
    monkeypatch.setattr(postgres_identity.psycopg, "connect", connect)
    return connect, conn


def _adapter(monkeypatch) -> tuple[PostgresIdentityStorageAdapter, MagicMock, MagicMock]:
    connect, conn = _mock_connect(monkeypatch)
    adapter = PostgresIdentityStorageAdapter(connection_string="postgresql://identity")
    conn.execute.assert_called_once()
    assert "CREATE TABLE IF NOT EXISTS users" in conn.execute.call_args.args[0]
    conn.reset_mock()
    return adapter, connect, conn


def test_connects_with_dict_rows_and_initializes_schema(monkeypatch) -> None:
    connect, conn = _mock_connect(monkeypatch)

    PostgresIdentityStorageAdapter(connection_string="postgresql://identity")

    connect.assert_called_with("postgresql://identity", row_factory=postgres_identity.dict_row)
    assert "CREATE TABLE IF NOT EXISTS api_keys" in conn.execute.call_args.args[0]
    assert "REFERENCES users(id) ON DELETE CASCADE" in conn.execute.call_args.args[0]
    assert "ALTER TABLE memberships" in conn.execute.call_args.args[0]
    assert "fk_memberships_project_id" in conn.execute.call_args.args[0]
    assert "CREATE UNIQUE INDEX IF NOT EXISTS idx_api_keys_prefix_unique" in (
        conn.execute.call_args.args[0]
    )
    assert "CREATE UNIQUE INDEX IF NOT EXISTS idx_refresh_token_hash_unique" in (
        conn.execute.call_args.args[0]
    )


def test_user_crud_queries_and_mapping(monkeypatch) -> None:
    adapter, _connect, conn = _adapter(monkeypatch)
    created_at = datetime(2026, 5, 29, tzinfo=UTC)
    user = User(
        id="u1",
        email="a@example.com",
        hashed_password="h",
        is_active=True,
        is_superuser=False,
        created_at=created_at,
    )

    assert adapter.create_user(user) == "u1"
    sql, params = conn.execute.call_args.args
    assert "INSERT INTO users" in sql
    assert params == ("u1", "a@example.com", "h", True, False, created_at)

    conn.reset_mock()
    conn.execute.return_value.fetchone.return_value = {
        "id": "u1",
        "email": "a@example.com",
        "hashed_password": "h",
        "is_active": True,
        "is_superuser": False,
        "created_at": created_at,
    }

    found = adapter.get_user_by_email("a@example.com")

    assert found is not None
    assert found.id == "u1"
    assert found.created_at == created_at
    assert conn.execute.call_args.args[1] == ("a@example.com",)


def test_project_and_membership_queries(monkeypatch) -> None:
    adapter, _connect, conn = _adapter(monkeypatch)
    created_at = datetime(2026, 5, 29, tzinfo=UTC)

    adapter.create_project(Project(id="p1", name="P", slug="p", created_at=created_at))
    assert "INSERT INTO projects" in conn.execute.call_args.args[0]

    conn.reset_mock()
    adapter.add_membership(Membership(user_id="u1", project_id="p1", role=Role.editor))
    sql, params = conn.execute.call_args.args
    assert "ON CONFLICT (user_id, project_id) DO UPDATE" in sql
    assert params == ("u1", "p1", "editor")

    conn.reset_mock()
    conn.execute.return_value.fetchall.return_value = [
        {"user_id": "u1", "project_id": "p1", "role": "editor"},
        {"user_id": "u1", "project_id": "p2", "role": "viewer"},
    ]
    memberships = adapter.list_memberships_for_user("u1")

    assert {m.project_id for m in memberships} == {"p1", "p2"}
    assert memberships[0].role is Role.editor


def test_api_key_lookup_touch_and_refresh_revoke(monkeypatch) -> None:
    adapter, _connect, conn = _adapter(monkeypatch)
    created_at = datetime(2026, 5, 29, tzinfo=UTC)
    last_used = created_at + timedelta(minutes=5)
    key = ApiKey(
        id="k1",
        user_id="u1",
        name="ci",
        hashed_key="hashed",
        prefix="ev_abc",
        created_at=created_at,
        last_used_at=last_used,
    )

    assert adapter.create_api_key(key) == "k1"
    sql, params = conn.execute.call_args.args
    assert "INSERT INTO api_keys" in sql
    assert params[-2:] == (last_used, False)

    conn.reset_mock()
    conn.execute.return_value.fetchone.return_value = {
        "id": "k1",
        "user_id": "u1",
        "name": "ci",
        "hashed_key": "hashed",
        "prefix": "ev_abc",
        "created_at": created_at,
        "last_used_at": last_used,
        "revoked": False,
    }
    found_key = adapter.get_api_key_by_prefix("ev_abc")
    assert found_key is not None and found_key.last_used_at == last_used

    conn.reset_mock()
    adapter.touch_api_key("k1", last_used)
    assert conn.execute.call_args.args[1] == (last_used, "k1")

    token = RefreshToken(
        id="r1",
        user_id="u1",
        token_hash="th",
        expires_at=created_at + timedelta(days=1),
        created_at=created_at,
    )
    conn.reset_mock()
    assert adapter.create_refresh_token(token) == "r1"
    assert "INSERT INTO refresh_tokens" in conn.execute.call_args.args[0]

    conn.reset_mock()
    adapter.revoke_refresh_token("r1")
    assert conn.execute.call_args.args[1] == ("r1",)
