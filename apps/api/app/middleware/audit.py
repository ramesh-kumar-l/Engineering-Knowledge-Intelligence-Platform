"""Audit logging middleware — scaffold (ADR-0006, security_requirements.md).

Phase 0 emits a structured audit log line for mutating requests (the tamper-evident,
persisted audit store lands with PostgreSQL-backed audit events in Phase 1). Read
requests are excluded to keep the audit trail focused on state changes.
"""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_logger = logging.getLogger("ekip.audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        if request.method in _AUDITED_METHODS:
            _logger.info(
                "audit",
                extra={
                    "extra": {
                        "event": "http_mutation",
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "tenant_id": request.headers.get("X-Tenant-Id", "public"),
                    }
                },
            )
        return response
