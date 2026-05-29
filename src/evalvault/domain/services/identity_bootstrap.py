"""Idempotent admin bootstrap for project-isolated identity (EvalVault G4).

Creates (once) an admin superuser, the deterministic default project (whose id
equals ``DEFAULT_PROJECT_ID`` so legacy/unscoped runs belong to it), and an
admin membership. Safe to call on every startup. Driven by env in the API layer
(``EVALVAULT_ADMIN_EMAIL`` / ``EVALVAULT_ADMIN_PASSWORD``).
"""

from __future__ import annotations

from evalvault.domain.entities.auth import (
    DEFAULT_PROJECT_ID,
    Membership,
    Project,
    Role,
    User,
)
from evalvault.ports.outbound.auth_port import PasswordHasherPort
from evalvault.ports.outbound.identity_port import IdentityStoragePort

DEFAULT_PROJECT_SLUG = "default"
DEFAULT_PROJECT_NAME = "Default Project"


def bootstrap_admin(
    store: IdentityStoragePort,
    hasher: PasswordHasherPort,
    *,
    email: str,
    password: str,
    project_id: str = DEFAULT_PROJECT_ID,
    project_slug: str = DEFAULT_PROJECT_SLUG,
    project_name: str = DEFAULT_PROJECT_NAME,
) -> tuple[User, Project]:
    """Ensure an admin user, the default project, and admin membership exist.

    Idempotent: re-invocation returns the existing records without duplication.
    Returns the (user, project) pair.
    """
    user = store.get_user_by_email(email)
    if user is None:
        user = User(email=email, hashed_password=hasher.hash(password), is_superuser=True)
        store.create_user(user)

    project = store.get_project(project_id)
    if project is None:
        project = Project(name=project_name, slug=project_slug, id=project_id)
        store.create_project(project)

    if store.get_membership(user.id, project.id) is None:
        store.add_membership(Membership(user_id=user.id, project_id=project.id, role=Role.admin))

    return user, project
