"""Knowledge-graph build + stats endpoints (api_catalog.md, Phase 3).

Triggering a build projects the tenant's ingested data into the graph store
synchronously (ADR-0009) and records a ``GraphBuildRun`` + events + an audit event.
All routes are RBAC-protected and tenant-scoped via ``Principal``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_audit_service, get_graph_build_repo, get_graph_service
from app.core.security import Principal, Role, require_role
from app.domain.graph import (
    GraphBuildEventListResponse,
    GraphBuildEventOut,
    GraphBuildRunListResponse,
    GraphBuildRunOut,
    GraphBuildTriggerRequest,
    GraphStatsResponse,
)
from app.repositories.graph_build import GraphBuildRepository
from app.services.audit_service import AuditService
from app.services.graph_service import GraphService

router = APIRouter(prefix="/graph", tags=["graph"])


@router.post("/build", response_model=GraphBuildRunOut)
async def trigger_build(
    payload: GraphBuildTriggerRequest | None = None,
    principal: Principal = Depends(require_role(Role.EDITOR)),
    service: GraphService = Depends(get_graph_service),
    audit: AuditService = Depends(get_audit_service),
) -> GraphBuildRunOut:
    request = payload or GraphBuildTriggerRequest()
    run = await service.build(principal.tenant_id, request.limit)
    await audit.record(
        tenant_id=principal.tenant_id,
        actor=principal.subject,
        action="graph.build",
        resource_type="graph_build_run",
        resource_id=str(run.id),
        status=run.status.value,
        metadata={"entities": run.entity_count, "relationships": run.relationship_count},
    )
    return GraphBuildRunOut.from_model(run)


@router.get("/stats", response_model=GraphStatsResponse)
async def get_stats(
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: GraphService = Depends(get_graph_service),
) -> GraphStatsResponse:
    return GraphStatsResponse.from_stats(await service.stats(principal.tenant_id))


@router.get("/build/runs", response_model=GraphBuildRunListResponse)
async def list_runs(
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: GraphBuildRepository = Depends(get_graph_build_repo),
) -> GraphBuildRunListResponse:
    runs = await repo.list_runs(principal.tenant_id, limit)
    return GraphBuildRunListResponse(runs=[GraphBuildRunOut.from_model(r) for r in runs])


@router.get("/build/runs/{run_id}", response_model=GraphBuildRunOut)
async def get_run(
    run_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: GraphBuildRepository = Depends(get_graph_build_repo),
) -> GraphBuildRunOut:
    run = await repo.get_run(principal.tenant_id, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Graph build run not found"
        )
    return GraphBuildRunOut.from_model(run)


@router.get("/build/runs/{run_id}/events", response_model=GraphBuildEventListResponse)
async def list_run_events(
    run_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: GraphBuildRepository = Depends(get_graph_build_repo),
) -> GraphBuildEventListResponse:
    run = await repo.get_run(principal.tenant_id, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Graph build run not found"
        )
    events = await repo.list_events(principal.tenant_id, run_id)
    return GraphBuildEventListResponse(
        events=[GraphBuildEventOut.from_model(e) for e in events]
    )
