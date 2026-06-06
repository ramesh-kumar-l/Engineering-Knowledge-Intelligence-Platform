"""Sync run + log endpoints (api_catalog.md) — powers the Sync Dashboard and Logs."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_sync_repo
from app.core.security import Principal, Role, require_role
from app.domain.sync import (
    SyncEventListResponse,
    SyncEventOut,
    SyncRunListResponse,
    SyncRunOut,
)
from app.repositories.sync import SyncRepository

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/runs", response_model=SyncRunListResponse)
async def list_runs(
    connector_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: SyncRepository = Depends(get_sync_repo),
) -> SyncRunListResponse:
    runs = await repo.list_runs(principal.tenant_id, connector_id, limit)
    return SyncRunListResponse(runs=[SyncRunOut.from_model(r) for r in runs])


@router.get("/runs/{run_id}", response_model=SyncRunOut)
async def get_run(
    run_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: SyncRepository = Depends(get_sync_repo),
) -> SyncRunOut:
    run = await repo.get_run(principal.tenant_id, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sync run not found")
    return SyncRunOut.from_model(run)


@router.get("/runs/{run_id}/events", response_model=SyncEventListResponse)
async def list_run_events(
    run_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: SyncRepository = Depends(get_sync_repo),
) -> SyncEventListResponse:
    run = await repo.get_run(principal.tenant_id, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sync run not found")
    events = await repo.list_events(principal.tenant_id, run_id)
    return SyncEventListResponse(events=[SyncEventOut.from_model(e) for e in events])
