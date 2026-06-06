"""Agent Layer endpoints (api_catalog.md, Phase 8).

Deterministic agents over retrieval + graph + trust + intelligence (ADR-0021); every
run persists an auditable trace + a trust-carrying result snapshot.
- ``GET /agents/catalog`` — available agents (Agent Workspace launcher);
- ``POST /agents/runs`` — run an agent (audited); returns the run with steps + result;
- ``GET /agents/runs`` — recent runs (Agent Audit Trail);
- ``GET /agents/runs/{id}`` — one run with its execution trace (Agent Execution Viewer).

All routes are tenant-scoped via ``Principal`` and require VIEWER (agents read knowledge;
the run record is a user-scoped, audited artifact).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.agents.agent_service import AgentService
from app.agents.catalog import catalog
from app.api.deps import get_agent_service, get_audit_service
from app.core.security import Principal, Role, require_role
from app.domain.agents import (
    AgentCatalogResponse,
    AgentRunDetailResponse,
    AgentRunListResponse,
    AgentRunOut,
    AgentTypeInfo,
    RunAgentRequest,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/catalog", response_model=AgentCatalogResponse)
async def get_catalog(
    principal: Principal = Depends(require_role(Role.VIEWER)),
) -> AgentCatalogResponse:
    return AgentCatalogResponse(agents=[AgentTypeInfo.of(i) for i in catalog()])


@router.post("/runs", response_model=AgentRunDetailResponse)
async def run_agent(
    payload: RunAgentRequest,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: AgentService = Depends(get_agent_service),
    audit: AuditService = Depends(get_audit_service),
) -> AgentRunDetailResponse:
    run = await service.run(
        principal.tenant_id, principal.subject, payload.agent_type, payload.target
    )
    await audit.record(
        tenant_id=principal.tenant_id,
        actor=principal.subject,
        action="agent.run",
        resource_type="agent_run",
        resource_id=str(run.id),
        metadata={"agent_type": run.agent_type.value, "status": run.status.value},
    )
    result = await service.get_run(principal.tenant_id, run.id)
    assert result is not None  # just created within this transaction
    return AgentRunDetailResponse.of(*result)


@router.get("/runs", response_model=AgentRunListResponse)
async def list_runs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: AgentService = Depends(get_agent_service),
) -> AgentRunListResponse:
    rows = await service.list_runs(principal.tenant_id, limit, offset)
    return AgentRunListResponse(
        runs=[AgentRunOut.from_model(run, n) for run, n in rows]
    )


@router.get("/runs/{run_id}", response_model=AgentRunDetailResponse)
async def get_run(
    run_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: AgentService = Depends(get_agent_service),
) -> AgentRunDetailResponse:
    result = await service.get_run(principal.tenant_id, run_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found"
        )
    return AgentRunDetailResponse.of(*result)
