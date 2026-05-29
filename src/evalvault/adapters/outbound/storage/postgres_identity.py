"""PostgreSQL-backed identity storage (EvalVault G4 project isolation).

Implements ``IdentityStoragePort`` with the same tables and semantics as the
SQLite identity adapter, but uses native PostgreSQL booleans/timestamptz values.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Any

import psycopg  # type: ignore[import-not-found]
from psycopg.rows import dict_row  # type: ignore[import-not-found]

from evalvault.domain.entities.auth import ApiKey, Membership, Project, RefreshToken, Role, User

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS memberships (
    user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    role TEXT NOT NULL,
    CONSTRAINT fk_memberships_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_memberships_project_id
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, project_id)
);
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    hashed_key TEXT NOT NULL,
    prefix TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_api_keys_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_api_keys_prefix_unique ON api_keys(prefix);
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_refresh_tokens_user_id
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_refresh_token_hash_unique ON refresh_tokens(token_hash);
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_memberships_user_id'
          AND conrelid = 'memberships'::regclass
    ) THEN
        ALTER TABLE memberships
            ADD CONSTRAINT fk_memberships_user_id
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_memberships_project_id'
          AND conrelid = 'memberships'::regclass
    ) THEN
        ALTER TABLE memberships
            ADD CONSTRAINT fk_memberships_project_id
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_api_keys_user_id'
          AND conrelid = 'api_keys'::regclass
    ) THEN
        ALTER TABLE api_keys
            ADD CONSTRAINT fk_api_keys_user_id
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_refresh_tokens_user_id'
          AND conrelid = 'refresh_tokens'::regclass
    ) THEN
        ALTER TABLE refresh_tokens
            ADD CONSTRAINT fk_refresh_tokens_user_id
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;
"""


class PostgresIdentityStorageAdapter:
    """PostgreSQL implementation of ``IdentityStoragePort``."""

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 5432,
        database: str = "evalvault",
        user: str = "postgres",
        password: str = "",
        connection_string: str | None = None,
    ) -> None:
        if connection_string:
            self._conn_string = connection_string
        else:
            self._conn_string = (
                f"host={host} port={port} dbname={database} user={user} password={password}"
            )
        self._ensure_schema()

    @contextmanager
    def _conn(self):
        with psycopg.connect(self._conn_string, row_factory=dict_row) as conn:
            yield conn

    def _ensure_schema(self) -> None:
        with self._conn() as conn:
            conn.execute(_SCHEMA)

    # --- users -------------------------------------------------------------
    def create_user(self, user: User) -> str:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO users (id, email, hashed_password, is_active, is_superuser, created_at)"
                " VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    user.id,
                    user.email,
                    user.hashed_password,
                    user.is_active,
                    user.is_superuser,
                    user.created_at,
                ),
            )
        return user.id

    def get_user(self, user_id: str) -> User | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
        return self._row_to_user(row) if row else None

    def get_user_by_email(self, email: str) -> User | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = %s", (email,)).fetchone()
        return self._row_to_user(row) if row else None

    @staticmethod
    def _row_to_user(row: dict[str, Any]) -> User:
        return User(
            email=row["email"],
            hashed_password=row["hashed_password"],
            id=row["id"],
            is_active=bool(row["is_active"]),
            is_superuser=bool(row["is_superuser"]),
            created_at=_parse_datetime(row["created_at"]),
        )

    # --- projects ----------------------------------------------------------
    def create_project(self, project: Project) -> str:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, slug, created_at) VALUES (%s, %s, %s, %s)",
                (project.id, project.name, project.slug, project.created_at),
            )
        return project.id

    def get_project(self, project_id: str) -> Project | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = %s", (project_id,)).fetchone()
        return self._row_to_project(row) if row else None

    def get_project_by_slug(self, slug: str) -> Project | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM projects WHERE slug = %s", (slug,)).fetchone()
        return self._row_to_project(row) if row else None

    @staticmethod
    def _row_to_project(row: dict[str, Any]) -> Project:
        return Project(
            name=row["name"],
            slug=row["slug"],
            id=row["id"],
            created_at=_parse_datetime(row["created_at"]),
        )

    # --- memberships -------------------------------------------------------
    def add_membership(self, membership: Membership) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO memberships (user_id, project_id, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, project_id) DO UPDATE SET
                    role = EXCLUDED.role
                """,
                (membership.user_id, membership.project_id, str(membership.role)),
            )

    def get_membership(self, user_id: str, project_id: str) -> Membership | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM memberships WHERE user_id = %s AND project_id = %s",
                (user_id, project_id),
            ).fetchone()
        return self._row_to_membership(row) if row else None

    def list_memberships_for_user(self, user_id: str) -> list[Membership]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM memberships WHERE user_id = %s", (user_id,)
            ).fetchall()
        return [self._row_to_membership(row) for row in rows]

    @staticmethod
    def _row_to_membership(row: dict[str, Any]) -> Membership:
        return Membership(
            user_id=row["user_id"],
            project_id=row["project_id"],
            role=Role(row["role"]),
        )

    # --- API keys ----------------------------------------------------------
    def create_api_key(self, api_key: ApiKey) -> str:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO api_keys (id, user_id, name, hashed_key, prefix, created_at,"
                " last_used_at, revoked) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    api_key.id,
                    api_key.user_id,
                    api_key.name,
                    api_key.hashed_key,
                    api_key.prefix,
                    api_key.created_at,
                    api_key.last_used_at,
                    api_key.revoked,
                ),
            )
        return api_key.id

    def get_api_key_by_prefix(self, prefix: str) -> ApiKey | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM api_keys WHERE prefix = %s AND revoked = FALSE", (prefix,)
            ).fetchone()
        return self._row_to_api_key(row) if row else None

    def touch_api_key(self, api_key_id: str, when: datetime) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE api_keys SET last_used_at = %s WHERE id = %s",
                (when, api_key_id),
            )

    @staticmethod
    def _row_to_api_key(row: dict[str, Any]) -> ApiKey:
        last_used = row["last_used_at"]
        return ApiKey(
            user_id=row["user_id"],
            name=row["name"],
            hashed_key=row["hashed_key"],
            prefix=row["prefix"],
            id=row["id"],
            created_at=_parse_datetime(row["created_at"]),
            last_used_at=_parse_datetime(last_used) if last_used else None,
            revoked=bool(row["revoked"]),
        )

    # --- refresh tokens ----------------------------------------------------
    def create_refresh_token(self, token: RefreshToken) -> str:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, created_at,"
                " revoked) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    token.id,
                    token.user_id,
                    token.token_hash,
                    token.expires_at,
                    token.created_at,
                    token.revoked,
                ),
            )
        return token.id

    def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM refresh_tokens WHERE token_hash = %s", (token_hash,)
            ).fetchone()
        return self._row_to_refresh_token(row) if row else None

    def revoke_refresh_token(self, token_id: str) -> None:
        with self._conn() as conn:
            conn.execute("UPDATE refresh_tokens SET revoked = TRUE WHERE id = %s", (token_id,))

    @staticmethod
    def _row_to_refresh_token(row: dict[str, Any]) -> RefreshToken:
        return RefreshToken(
            user_id=row["user_id"],
            token_hash=row["token_hash"],
            expires_at=_parse_datetime(row["expires_at"]),
            id=row["id"],
            created_at=_parse_datetime(row["created_at"]),
            revoked=bool(row["revoked"]),
        )


def _parse_datetime(value: datetime | str) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(value)
