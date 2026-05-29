"""Principal resolution + project authorization policy for the web API (G4).

Resolves an authenticated :class:`Principal` from either a session access JWT or
a per-user API key, resolves the current project with a documented precedence,
and encodes the denial policy. These helpers are framework-light (duck-typed
ports) so they can be unit/integration tested without a running FastAPI app and
then wired into route dependencies.

## Denial policy (authored for G4, see docs/phase1-real-adapter-readiness.md)
- No / unresolvable principal when auth is required → **401**.
- Authenticated non-member of the target project → **404** (do not leak the
  existence of foreign-project resources).
- Member whose role is below the required level for a write → **403**.

## Current-project precedence (documented)
``X-Project-Id`` header → ``project_id`` query param → request-body ``project_id``.
"""

from __future__ import annotations

from evalvault.domain.entities.auth import Role
from evalvault.domain.services.authorization import Principal, principal_from
from evalvault.ports.outbound.auth_port import PasswordHasherPort, TokenError, TokenServicePort
from evalvault.ports.outbound.identity_port import IdentityStoragePort


class PrincipalRequiredError(Exception):
    """No usable principal could be resolved (maps to HTTP 401)."""


class ProjectAccessDeniedError(Exception):
    """Caller is not a member of the target project (maps to HTTP 404).

    404 (not 403) so a non-member cannot distinguish a foreign project/run from
    a non-existent one.
    """


class InsufficientRoleError(Exception):
    """Member lacks the required role for the operation (maps to HTTP 403)."""


def resolve_current_project_id(
    *,
    header: str | None = None,
    query: str | None = None,
    body: str | None = None,
) -> str | None:
    """Resolve the current project id with documented precedence.

    Precedence: ``X-Project-Id`` header → ``project_id`` query → body field.
    """
    for candidate in (header, query, body):
        if candidate:
            return candidate
    return None


def resolve_principal(
    raw_token: str | None,
    *,
    identity_store: IdentityStoragePort,
    token_service: TokenServicePort,
    hasher: PasswordHasherPort,
) -> Principal | None:
    """Resolve a :class:`Principal` from a session access JWT or an API key.

    Returns ``None`` when the token is missing/invalid or the user is inactive.
    """
    if not raw_token:
        return None

    # (a) Session access JWT (browser cookie / Authorization bearer).
    try:
        claims = token_service.decode(raw_token, expected_type="access")
    except TokenError:
        claims = None
    if claims is not None:
        subject = claims.get("sub")
        user = identity_store.get_user(subject) if subject else None
        if user is not None and user.is_active:
            return principal_from(user, identity_store.list_memberships_for_user(user.id))

    # (b) Per-user API key, formatted ``<prefix>.<secret>``.
    prefix = raw_token.split(".", 1)[0]
    api_key = identity_store.get_api_key_by_prefix(prefix)
    if (
        api_key is not None
        and not api_key.revoked
        and hasher.verify(raw_token, api_key.hashed_key)
    ):
        user = identity_store.get_user(api_key.user_id)
        if user is not None and user.is_active:
            return principal_from(user, identity_store.list_memberships_for_user(user.id))

    return None


def require_member(principal: Principal | None, project_id: str) -> Principal:
    """Assert the principal is a member of ``project_id`` (else 401/404)."""
    if principal is None:
        raise PrincipalRequiredError("Authentication required")
    if not principal.is_member(project_id):
        # Hide existence of foreign projects/runs.
        raise ProjectAccessDeniedError(project_id)
    return principal


def require_role(principal: Principal | None, project_id: str, required: Role) -> Principal:
    """Assert membership AND at least ``required`` role (else 401/404/403)."""
    resolved = require_member(principal, project_id)
    if not resolved.can(project_id, required):
        raise InsufficientRoleError(f"requires role >= {required}")
    return resolved
