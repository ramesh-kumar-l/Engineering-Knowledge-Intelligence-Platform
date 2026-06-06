"""Security scaffolding — RBAC now, ABAC-ready (ADR-0006, security_requirements.md).

Phase 0 establishes the *shape* of authn/authz without a real identity provider:
- A ``Principal`` carries tenant + role context (multi-tenant from day one).
- ``require_role`` is a FastAPI dependency factory enforcing RBAC on routes.

Phase 1 replaces the dev principal resolver with OAuth/SSO token verification. The
route-level contract (``Depends(require_role(...))``) stays the same.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from fastapi import Depends, Header, HTTPException, status


class Role(StrEnum):
    """Coarse RBAC roles. ABAC attributes layer on top of these later."""

    ANONYMOUS = "anonymous"
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"


# Role hierarchy for "at least this role" checks.
_ROLE_RANK: dict[Role, int] = {
    Role.ANONYMOUS: 0,
    Role.VIEWER: 1,
    Role.EDITOR: 2,
    Role.ADMIN: 3,
}


@dataclass(frozen=True)
class Principal:
    """The authenticated actor for a request. Always tenant-scoped (ADR-0006)."""

    tenant_id: str
    subject: str
    role: Role

    def has_at_least(self, required: Role) -> bool:
        return _ROLE_RANK[self.role] >= _ROLE_RANK[required]


def get_principal(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> Principal:
    """Resolve the current principal.

    DEV-ONLY: derives identity from headers so the stack is exercisable end-to-end
    before OAuth/SSO lands in Phase 1. Defaults to an anonymous principal in the
    ``public`` tenant. This is intentionally NOT a security boundary yet.
    """
    role = Role.ANONYMOUS
    if x_role is not None:
        try:
            role = Role(x_role.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown role: {x_role}",
            ) from None
    return Principal(
        tenant_id=x_tenant_id or "public",
        subject="dev-user" if x_tenant_id else "anonymous",
        role=role,
    )


def require_role(minimum: Role) -> Callable[..., Principal]:
    """Dependency factory enforcing a minimum role (RBAC)."""

    def _dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has_at_least(minimum):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role '{minimum.value}' or higher",
            )
        return principal

    return _dependency
