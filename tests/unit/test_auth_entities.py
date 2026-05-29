"""Tests for the identity domain entities (EvalVault Auth P1.1)."""

from __future__ import annotations

from evalvault.domain.entities.auth import ApiKey, Membership, Project, Role, User


def test_role_is_string_enum() -> None:
    assert Role.admin == "admin"
    assert Role.editor == "editor"
    assert Role.viewer == "viewer"


def test_user_defaults() -> None:
    user = User(email="a@example.com", hashed_password="hashed")
    assert user.id
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.created_at is not None


def test_entities_get_unique_ids() -> None:
    a = User(email="a@example.com", hashed_password="x")
    b = User(email="b@example.com", hashed_password="y")
    assert a.id != b.id


def test_membership_defaults_to_viewer() -> None:
    membership = Membership(user_id="u1", project_id="p1")
    assert membership.role is Role.viewer


def test_project_and_apikey_construct() -> None:
    project = Project(name="Insurance QA", slug="insurance-qa")
    assert project.id and project.slug == "insurance-qa"
    key = ApiKey(user_id="u1", name="ci", hashed_key="h", prefix="ev_abc")
    assert key.revoked is False and key.prefix == "ev_abc"
