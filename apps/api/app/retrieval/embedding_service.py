"""Embedding engine — indexes processed chunks into the vector store (Phase 4).

``embed`` selects documents whose chunks have changed since they were last embedded
(staleness via ``DocumentEmbeddingState``), re-embeds each document's chunks wholesale
into the vector store, and records an ``EmbeddingRun`` with counters + events
(synchronous execution, ADR-0009). Per-document failures are isolated and counted; a
run-level failure is captured on the run, not raised.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.enums import SyncEventLevel, SyncStatus
from app.models.document import Document
from app.models.embedding import (
    DocumentEmbeddingState,
    EmbeddingEvent,
    EmbeddingRun,
)
from app.repositories.chunks import ChunkRepository
from app.repositories.embedding import EmbeddingRepository
from app.retrieval.base import VectorPoint
from app.retrieval.embedder import Embedder
from app.retrieval.vector_store import VectorStore


def _now() -> datetime:
    return datetime.now(UTC)


class EmbeddingService:
    def __init__(
        self,
        embedding_repo: EmbeddingRepository,
        chunk_repo: ChunkRepository,
        embedder: Embedder,
        vector_store: VectorStore,
    ) -> None:
        self._runs = embedding_repo
        self._chunks = chunk_repo
        self._embedder = embedder
        self._store = vector_store

    async def embed(self, tenant_id: str, force: bool = False) -> EmbeddingRun:
        run = await self._runs.add_run(
            EmbeddingRun(
                tenant_id=tenant_id, status=SyncStatus.RUNNING, started_at=_now()
            )
        )
        self._event(run, SyncEventLevel.INFO, "Embedding started")
        try:
            await self._store.ensure_collection(self._embedder.dimension)
            documents = await self._chunks.list_documents_with_chunks(tenant_id)
            run.documents_seen = len(documents)
            for document in documents:
                await self._embed_document(run, document, force)

            run.status = SyncStatus.SUCCEEDED
            self._event(
                run,
                SyncEventLevel.INFO,
                f"Embedding succeeded: {run.documents_embedded} embedded, "
                f"{run.documents_skipped} skipped, {run.chunk_count} chunks, "
                f"{run.failed_count} failed",
            )
        except Exception as exc:  # noqa: BLE001 - recorded on the run, not raised
            run.status = SyncStatus.FAILED
            run.error = str(exc)
            self._event(run, SyncEventLevel.ERROR, f"Embedding failed: {exc}")
        finally:
            run.finished_at = _now()
        return run

    async def _embed_document(
        self, run: EmbeddingRun, document: Document, force: bool
    ) -> None:
        try:
            state = await self._runs.get_state(document.tenant_id, document.id)
            if (
                not force
                and state is not None
                and state.source_content_hash == document.content_hash
            ):
                run.documents_skipped += 1
                return

            chunks = await self._chunks.list_by_document(document.tenant_id, document.id)
            await self._store.delete_document(document.tenant_id, document.id)
            vectors = self._embedder.embed_batch([c.content for c in chunks])
            points = [
                VectorPoint(
                    tenant_id=document.tenant_id,
                    chunk_id=chunk.id,
                    document_id=document.id,
                    ordinal=chunk.ordinal,
                    content=chunk.content,
                    title=document.title,
                    url=document.url,
                    vector=vector,
                )
                for chunk, vector in zip(chunks, vectors, strict=True)
            ]
            await self._store.upsert(points)
            await self._record_state(document, len(points), state)
            run.documents_embedded += 1
            run.chunk_count += len(points)
        except Exception as exc:  # noqa: BLE001 - per-document failure is isolated
            run.failed_count += 1
            self._event(
                run,
                SyncEventLevel.ERROR,
                f"Document {document.external_id} failed: {exc}",
            )

    async def _record_state(
        self,
        document: Document,
        chunk_count: int,
        existing: DocumentEmbeddingState | None,
    ) -> None:
        if existing is None:
            await self._runs.add_state(
                DocumentEmbeddingState(
                    tenant_id=document.tenant_id,
                    document_id=document.id,
                    source_content_hash=document.content_hash,
                    chunk_count=chunk_count,
                    model=self._embedder.name,
                    embedded_at=_now(),
                )
            )
            return
        existing.source_content_hash = document.content_hash
        existing.chunk_count = chunk_count
        existing.model = self._embedder.name
        existing.embedded_at = _now()

    def _event(
        self, run: EmbeddingRun, level: SyncEventLevel, message: str
    ) -> None:
        self._runs.add_event(
            EmbeddingEvent(
                embedding_run_id=run.id,
                tenant_id=run.tenant_id,
                level=level,
                message=message,
            )
        )
