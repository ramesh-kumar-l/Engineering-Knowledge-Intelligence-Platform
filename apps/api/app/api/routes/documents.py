"""Document endpoints (api_catalog.md) — browse ingested knowledge artifacts."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_document_repo
from app.core.security import Principal, Role, require_role
from app.domain.documents import DocumentListResponse, DocumentOut
from app.repositories.documents import DocumentRepository

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    connector_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(require_role(Role.VIEWER)),
    repo: DocumentRepository = Depends(get_document_repo),
) -> DocumentListResponse:
    documents = await repo.list(principal.tenant_id, connector_id, limit, offset)
    return DocumentListResponse(documents=[DocumentOut.from_model(d) for d in documents])
