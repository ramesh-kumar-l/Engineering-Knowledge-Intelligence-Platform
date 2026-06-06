"""Document API schemas (mirrored in packages/contracts).

Raw content is intentionally excluded from list responses; it is retained server-side
for the Phase 2 processing layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.domain.enums import SourceType
from app.models.document import Document


class DocumentOut(BaseModel):
    id: uuid.UUID
    connector_id: uuid.UUID
    source_type: SourceType
    external_id: str
    title: str
    url: str | None
    content_hash: str
    metadata: dict[str, Any]
    source_updated_at: datetime | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: Document) -> DocumentOut:
        return cls(
            id=model.id,
            connector_id=model.connector_id,
            source_type=model.source_type,
            external_id=model.external_id,
            title=model.title,
            url=model.url,
            content_hash=model.content_hash,
            metadata=model.doc_metadata,
            source_updated_at=model.source_updated_at,
            is_deleted=model.is_deleted,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class DocumentListResponse(BaseModel):
    documents: list[DocumentOut]
