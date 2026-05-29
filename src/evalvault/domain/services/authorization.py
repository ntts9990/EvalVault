"""Project-scoped authorization helpers (EvalVault G4).

Pure logic for membership/role resolution. A ``Principal`` is an authenticated
caller plus its per-project roles; routes use it to gate reads/writes. Role
ordering is admin > editor > viewer.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from evalvault.domain.entities.auth import Membership, Role, User

_ROLE_RANK: dict[Role, int] = {Role.viewer: 0, Role.editor: 1, Role.admin: 2}


def role_satisfies(actual: Role, required: Role) -> bool:
    """True if ``actual`` meets or exceeds ``required`` (admin > editor > viewer)."""
    return _ROLE_RANK[actual] >= _ROLE_RANK[required]


@dataclass
class Principal:
    """An authenticated caller and its per-project roles.

    ``is_superuser`` (admin bootstrap account) is treated as admin on every
    project. ``memberships`` maps ``project_id`` → :class:`Role`.
    """

    user_id: str
    email: str
    is_superuser: bool = False
    memberships: dict[str, Role] = field(default_factory=dict)

    def role_in(self, project_id: str) -> Role | None:
        if self.is_superuser:
            return Role.admin
        return self.memberships.get(project_id)

    def is_member(self, project_id: str) -> bool:
        return self.role_in(project_id) is not None

    def can(self, project_id: str, required: Role) -> bool:
        """True if the principal holds at least ``required`` role on the project."""
        role = self.role_in(project_id)
        return role is not None and role_satisfies(role, required)

    def project_ids(self) -> list[str]:
        """Explicit project memberships (empty for a superuser with none)."""
        return list(self.memberships)


def principal_from(user: User, memberships: Iterable[Membership]) -> Principal:
    """Build a :class:`Principal` from a user and its memberships."""
    return Principal(
        user_id=user.id,
        email=user.email,
        is_superuser=user.is_superuser,
        memberships={m.project_id: m.role for m in memberships},
    )
