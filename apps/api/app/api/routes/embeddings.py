"""Embedding (index) endpoints (api_catalog.md, Phase 4).

Triggering a run embeds the tenant's processed chunks into the vector store
synchronously (ADR-0009) and records an ``EmbeddingRun`` + events + an audit event.
All routes are RBAC-protected and tenant-scoped via ``Principal``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import (
    get_audit_service,
    get_embedder,
    get_embedding_repo,
    get_embedding_service,
    get_vector_store,
)
from app.core.security import Principal, Role, require_role
from app.domain.embedding import (
    EmbeddingEventListResponse,
    EmbeddingEventOut,
    EmbeddingRunListResponse,
    EmbeddingRunOut,
    EmbeddingStatsResponse,
    EmbeddingTriggerRequest,
)
from app.repositories.embedding import EmbeddingRepository
from app.retrieval.embedder import Embedder
from app.retrieval.embedding_service import EmbeddingService
from app.retrieval.vector_store import VectorStore
from app.services.audit_service import AuditService

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.post("/runs", response_model=EmbeddingRunOut)
async def trigger_embedding(
    payload: EmbeddingTriggerRequest | None = None,
    principal: Principal = Depends(require_role(Role.EDITOR)),
    service: EmbeddingService = Depends(get_embedding_service),
    audit: AuditService = Depends(get_audit_service),
) -> EmbeddingRunOut:
    request = payload or EmbeddingTriggerRequest()
    run = await service.embed(principal.tenant_id, request.force)
    await audit.record(
        tenant_id=principal.tenant_id,
        actor=principal.subject,
        action="embedding.run",
        resource_type="embedding_run",
        resource_id=str(run.id),
        status=run.status.value,
        metadata={"embedded": run.documents_embedded, "chunks": run.chunk_count},
    )
    return EmbeddingRunOut.from_model(run)


@router.get("/stats", response_model=EmbeddingStatsResponse)
async def get_stats(
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: EmbeddingRepository = Depends(get_embedding_repo),
    store: VectorStore = Depends(get_vector_store),
    embedder: Embedder = Depends(get_embedder),
) -> EmbeddingStatsResponse:
    return EmbeddingStatsResponse(
        documents_embedded=await repo.count_embedded_documents(principal.tenant_id),
        vectors=await store.count(principal.tenant_id),
        model=embedder.name,
        dimension=embedder.dimension,
    )


@router.get("/runs", response_model=EmbeddingRunListResponse)
async def list_runs(
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: EmbeddingRepository = Depends(get_embedding_repo),
) -> EmbeddingRunListResponse:
    runs = await repo.list_runs(principal.tenant_id, limit)
    return EmbeddingRunListResponse(runs=[EmbeddingRunOut.from_model(r) for r in runs])


@router.get("/runs/{run_id}", response_model=EmbeddingRunOut)
async def get_run(
    run_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: EmbeddingRepository = Depends(get_embedding_repo),
) -> EmbeddingRunOut:
    run = await repo.get_run(principal.tenant_id, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Embedding run not found"
        )
    return EmbeddingRunOut.from_model(run)


@router.get("/runs/{run_id}/events", response_model=EmbeddingEventListResponse)
async def list_run_events(
    run_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: EmbeddingRepository = Depends(get_embedding_repo),
) -> EmbeddingEventListResponse:
    run = await repo.get_run(principal.tenant_id, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Embedding run not found"
        )
    events = await repo.list_events(principal.tenant_id, run_id)
    return EmbeddingEventListResponse(
        events=[EmbeddingEventOut.from_model(e) for e in events]
    )
