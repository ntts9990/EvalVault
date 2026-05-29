"""SQLite-backed identity storage (EvalVault G4 project isolation).

Implements ``IdentityStoragePort`` over a SQLite file. Tables are created
idempotently and can coexist in the same database file as the evaluation
tables. Datetimes are stored as ISO-8601 strings.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from evalvault.domain.entities.auth import ApiKey, Membership, Project, RefreshToken, Role, User

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    is_superuser INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memberships (
    user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY (user_id, project_id)
);
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    hashed_key TEXT NOT NULL,
    prefix TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_used_at TEXT,
    revoked INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(prefix);
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revoked INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_refresh_token_hash ON refresh_tokens(token_hash);
"""


class SqliteIdentityStorageAdapter:
    """SQLite implementation of ``IdentityStoragePort``."""

    def __init__(self, db_path: str | Path = "data/db/evalvault.db") -> None:
        self._db_path = str(db_path)
        parent = Path(self._db_path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    # --- users -------------------------------------------------------------
    def create_user(self, user: User) -> str:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO users (id, email, hashed_password, is_active, is_superuser, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user.id,
                    user.email,
                    user.hashed_password,
                    int(user.is_active),
                    int(user.is_superuser),
                    user.created_at.isoformat(),
                ),
            )
        return user.id

    def get_user(self, user_id: str) -> User | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._row_to_user(row) if row else None

    def get_user_by_email(self, email: str) -> User | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return self._row_to_user(row) if row else None

    @staticmethod
    def _row_to_user(row: sqlite3.Row) -> User:
        return User(
            email=row["email"],
            hashed_password=row["hashed_password"],
            id=row["id"],
            is_active=bool(row["is_active"]),
            is_superuser=bool(row["is_superuser"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # --- projects ----------------------------------------------------------
    def create_project(self, project: Project) -> str:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, slug, created_at) VALUES (?, ?, ?, ?)",
                (project.id, project.name, project.slug, project.created_at.isoformat()),
            )
        return project.id

    def get_project(self, project_id: str) -> Project | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return self._row_to_project(row) if row else None

    def get_project_by_slug(self, slug: str) -> Project | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone()
        return self._row_to_project(row) if row else None

    @staticmethod
    def _row_to_project(row: sqlite3.Row) -> Project:
        return Project(
            name=row["name"],
            slug=row["slug"],
            id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # --- memberships -------------------------------------------------------
    def add_membership(self, membership: Membership) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO memberships (user_id, project_id, role) VALUES (?, ?, ?)",
                (membership.user_id, membership.project_id, str(membership.role)),
            )

    def get_membership(self, user_id: str, project_id: str) -> Membership | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM memberships WHERE user_id = ? AND project_id = ?",
                (user_id, project_id),
            ).fetchone()
        return self._row_to_membership(row) if row else None

    def list_memberships_for_user(self, user_id: str) -> list[Membership]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM memberships WHERE user_id = ?", (user_id,)
            ).fetchall()
        return [self._row_to_membership(row) for row in rows]

    @staticmethod
    def _row_to_membership(row: sqlite3.Row) -> Membership:
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
                " last_used_at, revoked) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    api_key.id,
                    api_key.user_id,
                    api_key.name,
                    api_key.hashed_key,
                    api_key.prefix,
                    api_key.created_at.isoformat(),
                    api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                    int(api_key.revoked),
                ),
            )
        return api_key.id

    def get_api_key_by_prefix(self, prefix: str) -> ApiKey | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM api_keys WHERE prefix = ? AND revoked = 0", (prefix,)
            ).fetchone()
        return self._row_to_api_key(row) if row else None

    def touch_api_key(self, api_key_id: str, when: datetime) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
                (when.isoformat(), api_key_id),
            )

    @staticmethod
    def _row_to_api_key(row: sqlite3.Row) -> ApiKey:
        last_used = row["last_used_at"]
        return ApiKey(
            user_id=row["user_id"],
            name=row["name"],
            hashed_key=row["hashed_key"],
            prefix=row["prefix"],
            id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_used_at=datetime.fromisoformat(last_used) if last_used else None,
            revoked=bool(row["revoked"]),
        )

    # --- refresh tokens ----------------------------------------------------
    def create_refresh_token(self, token: RefreshToken) -> str:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, created_at,"
                " revoked) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    token.id,
                    token.user_id,
                    token.token_hash,
                    token.expires_at.isoformat(),
                    token.created_at.isoformat(),
                    int(token.revoked),
                ),
            )
        return token.id

    def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM refresh_tokens WHERE token_hash = ?", (token_hash,)
            ).fetchone()
        return self._row_to_refresh_token(row) if row else None

    def revoke_refresh_token(self, token_id: str) -> None:
        with self._conn() as conn:
            conn.execute("UPDATE refresh_tokens SET revoked = 1 WHERE id = ?", (token_id,))

    @staticmethod
    def _row_to_refresh_token(row: sqlite3.Row) -> RefreshToken:
        return RefreshToken(
            user_id=row["user_id"],
            token_hash=row["token_hash"],
            expires_at=datetime.fromisoformat(row["expires_at"]),
            id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            revoked=bool(row["revoked"]),
        )
