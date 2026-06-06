"""Security: RBAC + JWT authentication, ABAC-ready (ADR-0006/0008).

- A ``Principal`` carries tenant + role context (multi-tenant from day one).
- ``get_principal`` is the production security boundary: it verifies a bearer JWT
  (OAuth/OIDC-compatible) and derives the principal from its claims.
- A dev-only header fallback stays available outside production so the stack is
  exercisable without an identity provider (``Settings.header_auth_allowed``).
- ``require_role`` is a FastAPI dependency factory enforcing RBAC on routes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

import jwt
from fastapi import Depends, Header, HTTPException, Request, status

from app.core.config import Settings


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


def _parse_role(raw: str) -> Role:
    try:
        return Role(raw.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown role: {raw}"
        ) from None


def principal_from_token(token: str, settings: Settings) -> Principal:
    """Verify a bearer JWT and build the principal from its claims.

    Expected claims: ``sub`` (subject), ``tenant_id``, ``role``. Signature, audience,
    issuer and expiry are validated by PyJWT. Any failure is a 401.
    """
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={
                "require": ["sub"],
                "verify_aud": settings.jwt_audience is not None,
                "verify_iss": settings.jwt_issuer is not None,
            },
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    tenant_id = claims.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing tenant_id"
        )
    return Principal(
        tenant_id=str(tenant_id),
        subject=str(claims["sub"]),
        role=_parse_role(str(claims.get("role", Role.VIEWER.value))),
    )


def get_principal(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> Principal:
    """Resolve the authenticated principal for a request.

    Order: (1) a ``Bearer`` JWT is the real boundary; (2) outside production, a dev
    header fallback (``X-Tenant-Id``/``X-Role``) keeps the stack exercisable without
    an IdP; (3) otherwise 401.
    """
    settings: Settings = request.app.state.settings

    if authorization and authorization.lower().startswith("bearer "):
        return principal_from_token(authorization[7:].strip(), settings)

    if settings.header_auth_allowed and x_tenant_id:
        return Principal(
            tenant_id=x_tenant_id,
            subject="dev-user",
            role=_parse_role(x_role) if x_role else Role.VIEWER,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
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
