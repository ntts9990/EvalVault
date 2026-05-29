"""Outbound port for identity persistence (EvalVault G4 project isolation).

Persists users, projects, memberships, API keys, and refresh tokens. Kept
separate from ``StoragePort`` (evaluation data) so identity has its own
focused contract and can be backed independently. Pure persistence — hashing
and token signing live behind ``PasswordHasherPort`` / ``TokenServicePort``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from evalvault.domain.entities.auth import ApiKey, Membership, Project, RefreshToken, User


class IdentityStoragePort(Protocol):
    # --- users -------------------------------------------------------------
    def create_user(self, user: User) -> str: ...

    def get_user(self, user_id: str) -> User | None: ...

    def get_user_by_email(self, email: str) -> User | None: ...

    # --- projects ----------------------------------------------------------
    def create_project(self, project: Project) -> str: ...

    def get_project(self, project_id: str) -> Project | None: ...

    def get_project_by_slug(self, slug: str) -> Project | None: ...

    # --- memberships -------------------------------------------------------
    def add_membership(self, membership: Membership) -> None: ...

    def get_membership(self, user_id: str, project_id: str) -> Membership | None: ...

    def list_memberships_for_user(self, user_id: str) -> list[Membership]: ...

    # --- API keys ----------------------------------------------------------
    def create_api_key(self, api_key: ApiKey) -> str: ...

    def get_api_key_by_prefix(self, prefix: str) -> ApiKey | None: ...

    def touch_api_key(self, api_key_id: str, when: datetime) -> None: ...

    # --- refresh tokens ----------------------------------------------------
    def create_refresh_token(self, token: RefreshToken) -> str: ...

    def get_refresh_token(self, token_hash: str) -> RefreshToken | None: ...

    def revoke_refresh_token(self, token_id: str) -> None: ...
