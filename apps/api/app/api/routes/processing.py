"""Processing endpoints (api_catalog.md) — runs, jobs, stats and the explorer.

Triggering a run executes the pipeline synchronously in-request (ADR-0009), mirroring
the sync trigger. All routes are RBAC-protected and tenant-scoped via ``Principal``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import (
    get_audit_service,
    get_chunk_repo,
    get_document_repo,
    get_enrichment_repo,
    get_processing_repo,
    get_processing_service,
)
from app.core.security import Principal, Role, require_role
from app.domain.chunks import (
    ChunkOut,
    DocumentProcessingDetail,
    EnrichmentOut,
    ProcessedDocumentListResponse,
    ProcessedDocumentOut,
)
from app.domain.processing import (
    ChunkStatsResponse,
    ProcessingEventListResponse,
    ProcessingEventOut,
    ProcessingRunListResponse,
    ProcessingRunOut,
    ProcessingTriggerRequest,
)
from app.repositories.chunks import ChunkRepository
from app.repositories.documents import DocumentRepository
from app.repositories.enrichment import EnrichmentRepository
from app.repositories.processing import ProcessingRepository
from app.services.audit_service import AuditService
from app.services.processing_service import ProcessingService

router = APIRouter(prefix="/processing", tags=["processing"])


@router.post("/runs", response_model=ProcessingRunOut)
async def trigger_processing(
    payload: ProcessingTriggerRequest | None = None,
    principal: Principal = Depends(require_role(Role.EDITOR)),
    service: ProcessingService = Depends(get_processing_service),
    audit: AuditService = Depends(get_audit_service),
) -> ProcessingRunOut:
    request = payload or ProcessingTriggerRequest()
    run = await service.run(
        principal.tenant_id, request.connector_id, request.limit
    )
    await audit.record(
        tenant_id=principal.tenant_id,
        actor=principal.subject,
        action="processing.run",
        resource_type="processing_run",
        resource_id=str(run.id),
        status=run.status.value,
        metadata={"processed": run.processed_count, "chunks": run.chunk_count},
    )
    return ProcessingRunOut.from_model(run)


@router.get("/runs", response_model=ProcessingRunListResponse)
async def list_runs(
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: ProcessingRepository = Depends(get_processing_repo),
) -> ProcessingRunListResponse:
    runs = await repo.list_runs(principal.tenant_id, limit)
    return ProcessingRunListResponse(runs=[ProcessingRunOut.from_model(r) for r in runs])


@router.get("/stats", response_model=ChunkStatsResponse)
async def get_stats(
    principal: Principal = Depends(require_role(Role.VIEWER)),
    enrichment_repo: EnrichmentRepository = Depends(get_enrichment_repo),
    chunk_repo: ChunkRepository = Depends(get_chunk_repo),
) -> ChunkStatsResponse:
    tenant = principal.tenant_id
    documents = await enrichment_repo.count_processed(tenant)
    total_chunks = await chunk_repo.total_count(tenant)
    total_chars = await chunk_repo.total_chars(tenant)
    distribution = await enrichment_repo.category_distribution(tenant)
    return ChunkStatsResponse(
        documents_processed=documents,
        total_chunks=total_chunks,
        total_chunk_chars=total_chars,
        avg_chunks_per_document=round(total_chunks / documents, 2) if documents else 0.0,
        avg_chunk_chars=round(total_chars / total_chunks, 2) if total_chunks else 0.0,
        category_distribution={cat.value: count for cat, count in distribution.items()},
    )


@router.get("/documents", response_model=ProcessedDocumentListResponse)
async def list_processed_documents(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: EnrichmentRepository = Depends(get_enrichment_repo),
) -> ProcessedDocumentListResponse:
    rows = await repo.list_processed(principal.tenant_id, limit, offset)
    return ProcessedDocumentListResponse(
        documents=[ProcessedDocumentOut.from_models(e, d) for e, d in rows]
    )


@router.get("/documents/{document_id}", response_model=DocumentProcessingDetail)
async def get_document_processing(
    document_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    doc_repo: DocumentRepository = Depends(get_document_repo),
    enrichment_repo: EnrichmentRepository = Depends(get_enrichment_repo),
    chunk_repo: ChunkRepository = Depends(get_chunk_repo),
) -> DocumentProcessingDetail:
    document = await doc_repo.get(principal.tenant_id, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    enrichment = await enrichment_repo.get_by_document(principal.tenant_id, document_id)
    chunks = await chunk_repo.list_by_document(principal.tenant_id, document_id)
    return DocumentProcessingDetail(
        document_id=document.id,
        title=document.title,
        url=document.url,
        source_type=document.source_type,
        external_id=document.external_id,
        enrichment=EnrichmentOut.from_model(enrichment) if enrichment else None,
        chunks=[ChunkOut.from_model(c) for c in chunks],
    )


@router.get("/runs/{run_id}", response_model=ProcessingRunOut)
async def get_run(
    run_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: ProcessingRepository = Depends(get_processing_repo),
) -> ProcessingRunOut:
    run = await repo.get_run(principal.tenant_id, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Processing run not found"
        )
    return ProcessingRunOut.from_model(run)


@router.get("/runs/{run_id}/events", response_model=ProcessingEventListResponse)
async def list_run_events(
    run_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: ProcessingRepository = Depends(get_processing_repo),
) -> ProcessingEventListResponse:
    run = await repo.get_run(principal.tenant_id, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Processing run not found"
        )
    events = await repo.list_events(principal.tenant_id, run_id)
    return ProcessingEventListResponse(
        events=[ProcessingEventOut.from_model(e) for e in events]
    )