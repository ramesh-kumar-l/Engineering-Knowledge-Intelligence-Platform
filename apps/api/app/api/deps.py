"""Shared route dependencies.

Exposes app-scoped singletons (datastores, secret box) and per-request resources
(DB session, repositories, services) to routes via FastAPI dependency injection,
keeping handlers free of global state. The session dependency owns the transaction:
it commits on success and rolls back on error.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import SecretBox
from app.core.db import DataStores
from app.repositories.audit import AuditRepository
from app.repositories.connectors import ConnectorRepository
from app.repositories.documents import DocumentRepository
from app.repositories.sync import SyncRepository
from app.services.audit_service import AuditService
from app.services.connector_service import ConnectorService
from app.services.sync_service import SyncService


def get_datastores(request: Request) -> DataStores:
    """Return the datastore registry created during app startup (lifespan)."""
    return request.app.state.datastores  # type: ignore[no-any-return]


def get_secret_box(request: Request) -> SecretBox:
    """Return the app-scoped secret box for credential encryption."""
    return request.app.state.secret_box  # type: ignore[no-any-return]


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a transactional session bound to the request lifecycle."""
    stores: DataStores = request.app.state.datastores
    async with stores.postgres.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_connector_service(
    session: AsyncSession = Depends(get_session),
    secret_box: SecretBox = Depends(get_secret_box),
) -> ConnectorService:
    return ConnectorService(ConnectorRepository(session), secret_box)


def get_sync_service(session: AsyncSession = Depends(get_session)) -> SyncService:
    return SyncService(SyncRepository(session), DocumentRepository(session))


def get_audit_service(session: AsyncSession = Depends(get_session)) -> AuditService:
    return AuditService(AuditRepository(session))


def get_sync_repo(session: AsyncSession = Depends(get_session)) -> SyncRepository:
    return SyncRepository(session)


def get_document_repo(session: AsyncSession = Depends(get_session)) -> DocumentRepository:
    return DocumentRepository(session)
