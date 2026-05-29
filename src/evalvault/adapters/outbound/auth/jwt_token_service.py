"""JWT token service (PyJWT) — implements ``TokenServicePort``.

Issues short-lived access tokens and longer-lived refresh tokens, each tagged
with a ``type`` claim so an access token cannot be used where a refresh token
is expected (and vice versa). HS256 by default (single node / shared secret).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from evalvault.ports.outbound.auth_port import TokenError

# Sensible defaults: 15-minute access, 14-day refresh.
DEFAULT_ACCESS_TTL_SECONDS = 15 * 60
DEFAULT_REFRESH_TTL_SECONDS = 14 * 24 * 60 * 60


class JwtTokenService:
    def __init__(
        self,
        secret: str,
        *,
        algorithm: str = "HS256",
        access_ttl_seconds: int = DEFAULT_ACCESS_TTL_SECONDS,
        refresh_ttl_seconds: int = DEFAULT_REFRESH_TTL_SECONDS,
    ) -> None:
        if not secret:
            raise ValueError("JWT secret must not be empty")
        self._secret = secret
        self._algorithm = algorithm
        self._access_ttl = access_ttl_seconds
        self._refresh_ttl = refresh_ttl_seconds

    def _issue(self, subject: str, token_type: str, ttl: int, extra: dict[str, Any] | None) -> str:
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "sub": subject,
            "type": token_type,
            "iat": now,
            "exp": now + timedelta(seconds=ttl),
        }
        if extra:
            payload.update(extra)
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def issue_access_token(self, subject: str, extra: dict[str, Any] | None = None) -> str:
        return self._issue(subject, "access", self._access_ttl, extra)

    def issue_refresh_token(self, subject: str, extra: dict[str, Any] | None = None) -> str:
        return self._issue(subject, "refresh", self._refresh_ttl, extra)

    def decode(self, token: str, *, expected_type: str | None = None) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.PyJWTError as exc:
            raise TokenError(str(exc)) from exc
        if expected_type is not None and payload.get("type") != expected_type:
            raise TokenError(
                f"Expected token of type {expected_type!r}, got {payload.get('type')!r}"
            )
        return payload
