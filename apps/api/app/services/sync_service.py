"""Sync engine — runs a connector and reconciles its documents (Phase 1).

Responsibilities: drive a connector's incremental fetch, detect created/updated/
unchanged/deleted documents via content hashing, record a ``SyncRun`` with counters
and log events, and advance the connector cursor. Connector failures are captured on
the run (status=failed) rather than raised, so the failure is always persisted.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from app.connectors.base import Connector, RawDocument
from app.domain.enums import (
    ConnectorStatus,
    SyncEventLevel,
    SyncStatus,
)
from app.models.connector import Connector as ConnectorModel
from app.models.document import Document
from app.models.sync import SyncEvent, SyncRun
from app.repositories.documents import DocumentRepository
from app.repositories.sync import SyncRepository


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


class SyncService:
    def __init__(self, sync_repo: SyncRepository, doc_repo: DocumentRepository) -> None:
        self._sync_repo = sync_repo
        self._doc_repo = doc_repo

    async def run(self, connector_model: ConnectorModel, connector: Connector) -> SyncRun:
        run = await self._sync_repo.add_run(
            SyncRun(
                tenant_id=connector_model.tenant_id,
                connector_id=connector_model.id,
                status=SyncStatus.RUNNING,
                started_at=_now(),
            )
        )
        self._event(run, SyncEventLevel.INFO, "Sync started")

        try:
            result = await connector.fetch(connector_model.cursor)
            self._event(run, SyncEventLevel.INFO, f"Fetched {len(result.documents)} documents")
            for raw in result.documents:
                await self._reconcile(connector_model, run, raw)
            for external_id in result.deleted_ids:
                await self._soft_delete(connector_model, run, external_id)

            connector_model.cursor = result.cursor
            connector_model.last_synced_at = _now()
            connector_model.status = ConnectorStatus.ACTIVE
            run.status = SyncStatus.SUCCEEDED
            self._event(
                run,
                SyncEventLevel.INFO,
                f"Sync succeeded: +{run.created_count} ~{run.updated_count} "
                f"-{run.deleted_count} ={run.unchanged_count}",
            )
        except Exception as exc:  # noqa: BLE001 - recorded on the run, not raised
            run.status = SyncStatus.FAILED
            run.error = str(exc)
            connector_model.status = ConnectorStatus.ERROR
            self._event(run, SyncEventLevel.ERROR, f"Sync failed: {exc}")
        finally:
            run.finished_at = _now()

        return run

    async def _reconcile(
        self, connector_model: ConnectorModel, run: SyncRun, raw: RawDocument
    ) -> None:
        run.documents_seen += 1
        content_hash = _hash(raw.content)
        existing = await self._doc_repo.get_by_external_id(
            connector_model.tenant_id, connector_model.id, raw.external_id
        )
        if existing is None:
            await self._doc_repo.add(
                Document(
                    tenant_id=connector_model.tenant_id,
                    connector_id=connector_model.id,
                    source_type=connector_model.source_type,
                    external_id=raw.external_id,
                    title=raw.title,
                    url=raw.url,
                    content_hash=content_hash,
                    raw_content=raw.content,
                    doc_metadata=raw.metadata,
                    source_updated_at=raw.source_updated_at,
                )
            )
            run.created_count += 1
        elif existing.content_hash != content_hash or existing.is_deleted:
            existing.title = raw.title
            existing.url = raw.url
            existing.content_hash = content_hash
            existing.raw_content = raw.content
            existing.doc_metadata = raw.metadata
            existing.source_updated_at = raw.source_updated_at
            existing.is_deleted = False
            run.updated_count += 1
        else:
            run.unchanged_count += 1

    async def _soft_delete(
        self, connector_model: ConnectorModel, run: SyncRun, external_id: str
    ) -> None:
        existing = await self._doc_repo.get_by_external_id(
            connector_model.tenant_id, connector_model.id, external_id
        )
        if existing is not None and not existing.is_deleted:
            existing.is_deleted = True
            run.deleted_count += 1

    def _event(self, run: SyncRun, level: SyncEventLevel, message: str) -> None:
        self._sync_repo.add_event(
            SyncEvent(
                sync_run_id=run.id,
                tenant_id=run.tenant_id,
                level=level,
                message=message,
            )
        )
