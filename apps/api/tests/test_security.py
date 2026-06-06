"""RBAC scaffolding tests (ADR-0006).

Verifies the role hierarchy and the principal resolver. The route-level enforcement
contract (``require_role``) is exercised through ``Principal.has_at_least`` here and
will be exercised end-to-end once protected routes land in Phase 1.
"""

from __future__ import annotations

import pytest

from app.core.security import Principal, Role


@pytest.mark.parametrize(
    ("role", "required", "allowed"),
    [
        (Role.ADMIN, Role.VIEWER, True),
        (Role.EDITOR, Role.EDITOR, True),
        (Role.VIEWER, Role.EDITOR, False),
        (Role.ANONYMOUS, Role.VIEWER, False),
    ],
)
def test_role_hierarchy(role: Role, required: Role, allowed: bool) -> None:
    principal = Principal(tenant_id="t1", subject="s", role=role)
    assert principal.has_at_least(required) is allowed


def test_principal_is_tenant_scoped() -> None:
    principal = Principal(tenant_id="acme", subject="dev-user", role=Role.VIEWER)
    assert principal.tenant_id == "acme"
