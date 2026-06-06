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
from app.graph.neo4j_store import Neo4jGraphStore
from app.graph.store import GraphStore
from app.repositories.audit import AuditRepository
from app.repositories.chunks import ChunkRepository
from app.repositories.connectors import ConnectorRepository
from app.repositories.documents import DocumentRepository
from app.repositories.enrichment import EnrichmentRepository
from app.repositories.graph_build import GraphBuildRepository
from app.repositories.processing import ProcessingRepository
from app.repositories.sync import SyncRepository
from app.services.audit_service import AuditService
from app.services.connector_service import ConnectorService
from app.services.graph_service import GraphService
from app.services.processing_service import ProcessingService
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


def get_processing_service(
    session: AsyncSession = Depends(get_session),
) -> ProcessingService:
    return ProcessingService(
        ProcessingRepository(session),
        DocumentRepository(session),
        EnrichmentRepository(session),
        ChunkRepository(session),
    )


def get_sync_repo(session: AsyncSession = Depends(get_session)) -> SyncRepository:
    return SyncRepository(session)


def get_document_repo(session: AsyncSession = Depends(get_session)) -> DocumentRepository:
    return DocumentRepository(session)


def get_processing_repo(
    session: AsyncSession = Depends(get_session),
) -> ProcessingRepository:
    return ProcessingRepository(session)


def get_enrichment_repo(
    session: AsyncSession = Depends(get_session),
) -> EnrichmentRepository:
    return EnrichmentRepository(session)


def get_chunk_repo(session: AsyncSession = Depends(get_session)) -> ChunkRepository:
    return ChunkRepository(session)


def get_graph_store(request: Request) -> GraphStore:
    """The knowledge-graph store (Neo4j in production; ADR-0012)."""
    stores: DataStores = request.app.state.datastores
    return Neo4jGraphStore(stores.neo4j)


def get_graph_build_repo(
    session: AsyncSession = Depends(get_session),
) -> GraphBuildRepository:
    return GraphBuildRepository(session)


def get_graph_service(
    session: AsyncSession = Depends(get_session),
    store: GraphStore = Depends(get_graph_store),
) -> GraphService:
    return GraphService(
        GraphBuildRepository(session),
        ConnectorRepository(session),
        DocumentRepository(session),
        store,
    )
