"""Outbound ports for authentication (EvalVault Auth P1.1).

Concrete adapters live under ``adapters/outbound/auth``. Keeping these behind
ports lets the identity source evolve (e.g. add an OIDC token adapter) without
touching the domain or routers.
"""

from __future__ import annotations

from typing import Any, Protocol


class TokenError(Exception):
    """Raised when a token is invalid, expired, or of an unexpected type."""


class PasswordHasherPort(Protocol):
    """Hash and verify user passwords."""

    def hash(self, password: str) -> str: ...

    def verify(self, password: str, hashed: str) -> bool: ...


class TokenServicePort(Protocol):
    """Issue and verify signed session tokens (access + refresh)."""

    def issue_access_token(self, subject: str, extra: dict[str, Any] | None = None) -> str: ...

    def issue_refresh_token(self, subject: str, extra: dict[str, Any] | None = None) -> str: ...

    def decode(self, token: str, *, expected_type: str | None = None) -> dict[str, Any]:
        """Return the decoded claims, or raise ``TokenError``.

        If ``expected_type`` is given, the token's ``type`` claim must match.
        """
        ...
