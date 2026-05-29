"""Identity & authorization domain entities (EvalVault Auth P1.1).

Project-scoped multi-tenancy: a ``User`` is granted a ``Role`` on a ``Project``
via a ``Membership``; data is isolated per project. ``ApiKey`` enables
programmatic (CLI/MCP/CI) access; ``RefreshToken`` backs session rotation.
These are pure data holders — hashing/token logic lives behind the auth ports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4


class Role(StrEnum):
    """Project membership role. Order reflects privilege (admin > editor > viewer)."""

    admin = "admin"
    editor = "editor"
    viewer = "viewer"


def _new_id() -> str:
    return uuid4().hex


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class User:
    email: str
    hashed_password: str
    id: str = field(default_factory=_new_id)
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = field(default_factory=_now)


@dataclass
class Project:
    name: str
    slug: str
    id: str = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_now)


@dataclass
class Membership:
    user_id: str
    project_id: str
    role: Role = Role.viewer


@dataclass
class ApiKey:
    """A per-user programmatic credential. Only ``hashed_key`` is stored; the
    plaintext key is shown once at creation. ``prefix`` aids lookup/display."""

    user_id: str
    name: str
    hashed_key: str
    prefix: str
    id: str = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_now)
    last_used_at: datetime | None = None
    revoked: bool = False


@dataclass
class RefreshToken:
    user_id: str
    token_hash: str
    expires_at: datetime
    id: str = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_now)
    revoked: bool = False
