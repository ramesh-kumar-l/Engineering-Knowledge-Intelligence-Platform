"""Health & readiness endpoints (api_catalog.md).

- ``GET /health``  — liveness: the process is up (no dependency I/O). Used by the
  container HEALTHCHECK and load balancers.
- ``GET /health/ready`` — readiness: the process AND all datastores. Returns 503 when
  any dependency is unhealthy so orchestrators hold traffic until the stack is ready.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app import __version__
from app.api.deps import get_datastores
from app.core.db import DataStores
from app.domain.schemas import DependencyStatus, HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe — always cheap, never touches datastores."""
    return HealthResponse(status="ok", version=__version__)


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness(
    response: Response,
    stores: DataStores = Depends(get_datastores),
) -> ReadinessResponse:
    """Readiness probe — aggregates datastore health (ADR-0004)."""
    statuses = await stores.health_check()
    dependencies = [
        DependencyStatus(name=s.name, healthy=s.healthy, detail=s.detail)
        for s in statuses
    ]
    all_healthy = all(d.healthy for d in dependencies)
    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ready" if all_healthy else "degraded",
        version=__version__,
        dependencies=dependencies,
    )
