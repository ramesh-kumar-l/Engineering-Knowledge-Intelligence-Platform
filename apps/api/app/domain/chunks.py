"""Document-processing result schemas — enrichment, chunks, explorer (mirrored in TS).

Powers the Parsing Explorer: a list of processed documents and a per-document detail
combining its enrichment with its chunks.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import DocumentCategory, ProcessingStatus, SourceType
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.enrichment import DocumentEnrichment


class ChunkOut(BaseModel):
    id: uuid.UUID
    ordinal: int
    content: str
    char_count: int
    token_estimate: int

    @classmethod
    def from_model(cls, model: Chunk) -> ChunkOut:
        return cls(
            id=model.id,
            ordinal=model.ordinal,
            content=model.content,
            char_count=model.char_count,
            token_estimate=model.token_estimate,
        )


class EnrichmentOut(BaseModel):
    document_id: uuid.UUID
    status: ProcessingStatus
    category: DocumentCategory
    summary: str
    keywords: list[str]
    language: str | None
    word_count: int
    char_count: int
    chunk_count: int
    error: str | None
    processed_at: datetime | None

    @classmethod
    def from_model(cls, model: DocumentEnrichment) -> EnrichmentOut:
        return cls(
            document_id=model.document_id,
            status=model.status,
            category=model.category,
            summary=model.summary,
            keywords=model.keywords,
            language=model.language,
            word_count=model.word_count,
            char_count=model.char_count,
            chunk_count=model.chunk_count,
            error=model.error,
            processed_at=model.processed_at,
        )


class ProcessedDocumentOut(BaseModel):
    """One row in the Parsing Explorer list — document identity + enrichment summary."""

    document_id: uuid.UUID
    title: str
    url: str | None
    source_type: SourceType
    external_id: str
    enrichment: EnrichmentOut

    @classmethod
    def from_models(
        cls, enrichment: DocumentEnrichment, document: Document
    ) -> ProcessedDocumentOut:
        return cls(
            document_id=document.id,
            title=document.title,
            url=document.url,
            source_type=document.source_type,
            external_id=document.external_id,
            enrichment=EnrichmentOut.from_model(enrichment),
        )


class ProcessedDocumentListResponse(BaseModel):
    documents: list[ProcessedDocumentOut]


class DocumentProcessingDetail(BaseModel):
    """Per-document processing detail: identity, enrichment and chunks."""

    document_id: uuid.UUID
    title: str
    url: str | None
    source_type: SourceType
    external_id: str
    enrichment: EnrichmentOut | None
    chunks: list[ChunkOut]
