"""Processing engine — runs the pipeline over a tenant's documents (Phase 2).

Selects documents needing (re)processing, runs the deterministic pipeline per
document, and persists chunks + a 1:1 enrichment. Per-document failures are recorded
on the document (status=failed) and counted, without aborting the run; a run-level
failure is captured on the ``ProcessingRun`` (ADR-0009 synchronous execution model).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

from app.domain.enums import ProcessingStatus, SyncEventLevel, SyncStatus
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.enrichment import DocumentEnrichment
from app.models.processing import ProcessingEvent, ProcessingRun
from app.processing import pipeline
from app.processing.base import ProcessingOutput
from app.repositories.chunks import ChunkRepository
from app.repositories.documents import DocumentRepository
from app.repositories.enrichment import EnrichmentRepository
from app.repositories.processing import ProcessingRepository


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


class ProcessingService:
    def __init__(
        self,
        processing_repo: ProcessingRepository,
        document_repo: DocumentRepository,
        enrichment_repo: EnrichmentRepository,
        chunk_repo: ChunkRepository,
    ) -> None:
        self._runs = processing_repo
        self._docs = document_repo
        self._enrichments = enrichment_repo
        self._chunks = chunk_repo

    async def run(
        self,
        tenant_id: str,
        connector_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> ProcessingRun:
        run = await self._runs.add_run(
            ProcessingRun(
                tenant_id=tenant_id,
                connector_id=connector_id,
                status=SyncStatus.RUNNING,
                started_at=_now(),
            )
        )
        self._event(run, SyncEventLevel.INFO, "Processing started")

        try:
            documents = await self._docs.list_pending_processing(
                tenant_id, connector_id, limit
            )
            self._event(
                run, SyncEventLevel.INFO, f"Selected {len(documents)} documents"
            )
            for document in documents:
                run.documents_seen += 1
                await self._process_one(run, document)

            run.status = SyncStatus.SUCCEEDED
            self._event(
                run,
                SyncEventLevel.INFO,
                f"Processing succeeded: {run.processed_count} processed, "
                f"{run.chunk_count} chunks, {run.failed_count} failed",
            )
        except Exception as exc:  # noqa: BLE001 - recorded on the run, not raised
            run.status = SyncStatus.FAILED
            run.error = str(exc)
            self._event(run, SyncEventLevel.ERROR, f"Processing failed: {exc}")
        finally:
            run.finished_at = _now()

        return run

    async def _process_one(self, run: ProcessingRun, document: Document) -> None:
        try:
            output = pipeline.process(
                document.title, document.raw_content, document.doc_metadata
            )
            await self._store_chunks(document, output)
            await self._upsert_enrichment(document, output)
            run.processed_count += 1
            run.chunk_count += len(output.chunks)
        except Exception as exc:  # noqa: BLE001 - per-document failure is isolated
            run.failed_count += 1
            await self._mark_failed(document, str(exc))
            self._event(
                run,
                SyncEventLevel.ERROR,
                f"Document {document.external_id} failed: {exc}",
            )

    async def _store_chunks(
        self, document: Document, output: ProcessingOutput
    ) -> None:
        chunks = [
            Chunk(
                tenant_id=document.tenant_id,
                document_id=document.id,
                ordinal=chunk.ordinal,
                content=chunk.content,
                content_hash=_hash(chunk.content),
                char_count=chunk.char_count,
                token_estimate=chunk.token_estimate,
            )
            for chunk in output.chunks
        ]
        await self._chunks.replace_for_document(document.tenant_id, document.id, chunks)

    async def _upsert_enrichment(
        self, document: Document, output: ProcessingOutput
    ) -> None:
        existing = await self._enrichments.get_by_document(
            document.tenant_id, document.id
        )
        e = output.enrichment
        if existing is None:
            await self._enrichments.add(
                DocumentEnrichment(
                    tenant_id=document.tenant_id,
                    document_id=document.id,
                    source_content_hash=document.content_hash,
                    status=ProcessingStatus.PROCESSED,
                    category=output.category,
                    summary=output.summary,
                    keywords=e.keywords,
                    language=e.language,
                    word_count=e.word_count,
                    char_count=e.char_count,
                    chunk_count=len(output.chunks),
                    error=None,
                    processed_at=_now(),
                )
            )
            return
        existing.source_content_hash = document.content_hash
        existing.status = ProcessingStatus.PROCESSED
        existing.category = output.category
        existing.summary = output.summary
        existing.keywords = e.keywords
        existing.language = e.language
        existing.word_count = e.word_count
        existing.char_count = e.char_count
        existing.chunk_count = len(output.chunks)
        existing.error = None
        existing.processed_at = _now()

    async def _mark_failed(self, document: Document, error: str) -> None:
        existing = await self._enrichments.get_by_document(
            document.tenant_id, document.id
        )
        if existing is None:
            await self._enrichments.add(
                DocumentEnrichment(
                    tenant_id=document.tenant_id,
                    document_id=document.id,
                    source_content_hash=document.content_hash,
                    status=ProcessingStatus.FAILED,
                    error=error,
                    processed_at=_now(),
                )
            )
            return
        existing.source_content_hash = document.content_hash
        existing.status = ProcessingStatus.FAILED
        existing.error = error
        existing.processed_at = _now()

    def _event(
        self, run: ProcessingRun, level: SyncEventLevel, message: str
    ) -> None:
        self._runs.add_event(
            ProcessingEvent(
                processing_run_id=run.id,
                tenant_id=run.tenant_id,
                level=level,
                message=message,
            )
        )
