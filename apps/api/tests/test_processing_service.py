"""Processing engine tests — pipeline persistence, idempotency, reprocessing (SQLite)."""

from __future__ import annotations

import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import ProcessingStatus, SourceType, SyncStatus
from app.models.connector import Connector
from app.models.document import Document
from app.repositories.chunks import ChunkRepository
from app.repositories.documents import DocumentRepository
from app.repositories.enrichment import EnrichmentRepository
from app.repositories.processing import ProcessingRepository
from app.services.processing_service import ProcessingService


def _service(session: AsyncSession) -> ProcessingService:
    return ProcessingService(
        ProcessingRepository(session),
        DocumentRepository(session),
        EnrichmentRepository(session),
        ChunkRepository(session),
    )


async def _document(session: AsyncSession, content: str) -> Document:
    connector = Connector(
        tenant_id="acme", source_type=SourceType.GITHUB, name="repo", config={}
    )
    session.add(connector)
    await session.flush()
    doc = Document(
        tenant_id="acme",
        connector_id=connector.id,
        source_type=SourceType.GITHUB,
        external_id="1",
        title="Login bug",
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
        raw_content=content,
        doc_metadata={"labels": ["bug"]},
    )
    session.add(doc)
    await session.flush()
    return doc


async def test_processes_document_into_chunks_and_enrichment(
    db_session: AsyncSession,
) -> None:
    doc = await _document(db_session, "The login page crashes for some users. " * 20)
    service = _service(db_session)

    run = await service.run("acme")
    assert run.status == SyncStatus.SUCCEEDED
    assert run.processed_count == 1
    assert run.chunk_count >= 1

    enrichment = await EnrichmentRepository(db_session).get_by_document("acme", doc.id)
    assert enrichment is not None
    assert enrichment.status == ProcessingStatus.PROCESSED
    assert enrichment.summary
    chunks = await ChunkRepository(db_session).list_by_document("acme", doc.id)
    assert len(chunks) == run.chunk_count


async def test_processing_is_idempotent_until_content_changes(
    db_session: AsyncSession,
) -> None:
    doc = await _document(db_session, "Initial content about caching.")
    service = _service(db_session)

    await service.run("acme")
    second = await service.run("acme")
    assert second.documents_seen == 0  # nothing pending the second time

    # Simulate a sync updating the document content.
    doc.raw_content = "Brand new content about deployment pipelines and rollout."
    doc.content_hash = hashlib.sha256(doc.raw_content.encode()).hexdigest()
    await db_session.flush()

    third = await service.run("acme")
    assert third.processed_count == 1


async def test_skips_deleted_documents(db_session: AsyncSession) -> None:
    doc = await _document(db_session, "Some content")
    doc.is_deleted = True
    await db_session.flush()

    run = await _service(db_session).run("acme")
    assert run.documents_seen == 0
