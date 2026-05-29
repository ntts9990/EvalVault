"""Role-gate + principal resolution helpers (EvalVault G4)."""

from __future__ import annotations

from evalvault.domain.entities.auth import Membership, Role, User
from evalvault.domain.services.authorization import (
    Principal,
    principal_from,
    role_satisfies,
)


def test_role_satisfies_ordering():
    assert role_satisfies(Role.admin, Role.viewer)
    assert role_satisfies(Role.admin, Role.editor)
    assert role_satisfies(Role.admin, Role.admin)
    assert role_satisfies(Role.editor, Role.viewer)
    assert role_satisfies(Role.editor, Role.editor)
    assert role_satisfies(Role.viewer, Role.viewer)
    # Insufficient rank fails.
    assert not role_satisfies(Role.viewer, Role.editor)
    assert not role_satisfies(Role.viewer, Role.admin)
    assert not role_satisfies(Role.editor, Role.admin)


def test_principal_member_role_checks():
    p = Principal(user_id="u1", email="u@x", memberships={"p1": Role.viewer, "p2": Role.editor})
    assert p.is_member("p1") and p.is_member("p2")
    assert not p.is_member("p3")
    assert p.role_in("p1") is Role.viewer
    assert p.role_in("p3") is None
    # viewer can read but not write; editor can write.
    assert p.can("p1", Role.viewer)
    assert not p.can("p1", Role.editor)
    assert p.can("p2", Role.editor)
    # Non-member cannot do anything.
    assert not p.can("p3", Role.viewer)
    assert set(p.project_ids()) == {"p1", "p2"}


def test_superuser_is_admin_everywhere():
    p = Principal(user_id="root", email="root@x", is_superuser=True)
    assert p.role_in("any-project") is Role.admin
    assert p.is_member("any-project")
    assert p.can("any-project", Role.admin)


def test_principal_from_user_and_memberships():
    user = User(email="u@x", hashed_password="h")
    memberships = [
        Membership(user_id=user.id, project_id="p1", role=Role.admin),
        Membership(user_id=user.id, project_id="p2", role=Role.viewer),
    ]
    p = principal_from(user, memberships)
    assert p.user_id == user.id
    assert p.email == "u@x"
    assert p.role_in("p1") is Role.admin
    assert p.role_in("p2") is Role.viewer
