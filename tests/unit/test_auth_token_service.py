"""Tests for the JWT token service (EvalVault Auth P1.1)."""

from __future__ import annotations

import pytest

from evalvault.adapters.outbound.auth.jwt_token_service import JwtTokenService
from evalvault.ports.outbound.auth_port import TokenError


def _service(**kwargs) -> JwtTokenService:
    return JwtTokenService(secret="unit-test-secret", **kwargs)


def test_empty_secret_rejected() -> None:
    with pytest.raises(ValueError):
        JwtTokenService(secret="")


def test_access_token_roundtrip_carries_claims() -> None:
    service = _service()
    token = service.issue_access_token("user-1", {"role": "admin"})
    payload = service.decode(token, expected_type="access")
    assert payload["sub"] == "user-1"
    assert payload["type"] == "access"
    assert payload["role"] == "admin"


def test_refresh_token_has_refresh_type() -> None:
    service = _service()
    payload = service.decode(service.issue_refresh_token("user-1"), expected_type="refresh")
    assert payload["type"] == "refresh"


def test_wrong_secret_is_rejected() -> None:
    token = _service().issue_access_token("user-1")
    with pytest.raises(TokenError):
        JwtTokenService(secret="different-secret").decode(token)


def test_expired_token_is_rejected() -> None:
    service = _service(access_ttl_seconds=-1)
    token = service.issue_access_token("user-1")
    with pytest.raises(TokenError):
        service.decode(token)


def test_wrong_token_type_is_rejected() -> None:
    service = _service()
    access = service.issue_access_token("user-1")
    with pytest.raises(TokenError):
        service.decode(access, expected_type="refresh")
