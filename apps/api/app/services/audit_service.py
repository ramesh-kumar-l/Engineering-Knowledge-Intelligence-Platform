"""Audit service — persists sensitive actions to the PostgreSQL audit store.

Replaces the Phase 0 log-only scaffold for state-changing operations. The request id
is captured for correlation with structured logs.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import request_id_ctx
from app.models.audit import AuditEvent
from app.repositories.audit import AuditRepository


class AuditService:
    def __init__(self, repo: AuditRepository) -> None:
        self._repo = repo

    async def record(
        self,
        tenant_id: str,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        status: str = "success",
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        return await self._repo.add(
            AuditEvent(
                tenant_id=tenant_id,
                actor=actor,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                status=status,
                request_id=request_id_ctx.get(),
                event_metadata=metadata or {},
            )
        )
