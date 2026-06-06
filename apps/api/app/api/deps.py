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

from app.agents.agent_service import AgentService
from app.assistant.assistant_service import AssistantService
from app.core.crypto import SecretBox
from app.core.db import DataStores
from app.graph.neo4j_store import Neo4jGraphStore
from app.graph.store import GraphStore
from app.intelligence.intelligence_service import IntelligenceService
from app.repositories.agents import AgentRepository
from app.repositories.audit import AuditRepository
from app.repositories.chunks import ChunkRepository
from app.repositories.connectors import ConnectorRepository
from app.repositories.conversations import ConversationRepository
from app.repositories.documents import DocumentRepository
from app.repositories.embedding import EmbeddingRepository
from app.repositories.enrichment import EnrichmentRepository
from app.repositories.graph_build import GraphBuildRepository
from app.repositories.processing import ProcessingRepository
from app.repositories.sync import SyncRepository
from app.repositories.trust import TrustRepository
from app.retrieval.embedder import Embedder, HashingEmbedder
from app.retrieval.embedding_service import EmbeddingService
from app.retrieval.qdrant_store import QdrantVectorStore
from app.retrieval.search_service import SearchService
from app.retrieval.vector_store import VectorStore
from app.services.audit_service import AuditService
from app.services.connector_service import ConnectorService
from app.services.graph_service import GraphService
from app.services.processing_service import ProcessingService
from app.services.sync_service import SyncService
from app.trust.trust_service import TrustService

# Process-wide deterministic embedder (ADR-0014); stateless, safe to share.
_EMBEDDER = HashingEmbedder()


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


def get_embedder() -> Embedder:
    """The deterministic embedder (ADR-0014)."""
    return _EMBEDDER


def get_vector_store(request: Request) -> VectorStore:
    """The chunk vector store (Qdrant in production; ADR-0015)."""
    stores: DataStores = request.app.state.datastores
    return QdrantVectorStore(stores.qdrant)


def get_embedding_repo(
    session: AsyncSession = Depends(get_session),
) -> EmbeddingRepository:
    return EmbeddingRepository(session)


def get_embedding_service(
    session: AsyncSession = Depends(get_session),
    embedder: Embedder = Depends(get_embedder),
    store: VectorStore = Depends(get_vector_store),
) -> EmbeddingService:
    return EmbeddingService(
        EmbeddingRepository(session),
        ChunkRepository(session),
        embedder,
        store,
    )


def get_search_service(
    session: AsyncSession = Depends(get_session),
    embedder: Embedder = Depends(get_embedder),
    store: VectorStore = Depends(get_vector_store),
    graph_store: GraphStore = Depends(get_graph_store),
) -> SearchService:
    return SearchService(
        embedder,
        store,
        ChunkRepository(session),
        graph_store,
    )


def get_conversation_repo(
    session: AsyncSession = Depends(get_session),
) -> ConversationRepository:
    return ConversationRepository(session)


def get_assistant_service(
    session: AsyncSession = Depends(get_session),
    embedder: Embedder = Depends(get_embedder),
    store: VectorStore = Depends(get_vector_store),
    graph_store: GraphStore = Depends(get_graph_store),
) -> AssistantService:
    """Engineering Assistant over retrieval + graph + trust (Phase 6)."""
    chunk_repo = ChunkRepository(session)
    search = SearchService(embedder, store, chunk_repo, graph_store)
    trust = TrustService(TrustRepository(session), chunk_repo, graph_store)
    return AssistantService(
        search, trust, graph_store, ConversationRepository(session)
    )


def get_intelligence_service(
    session: AsyncSession = Depends(get_session),
    graph_store: GraphStore = Depends(get_graph_store),
) -> IntelligenceService:
    """Engineering Intelligence over the graph + trust layers (Phase 7)."""
    trust = TrustService(TrustRepository(session), ChunkRepository(session), graph_store)
    return IntelligenceService(graph_store, trust)


def get_agent_service(
    session: AsyncSession = Depends(get_session),
    embedder: Embedder = Depends(get_embedder),
    store: VectorStore = Depends(get_vector_store),
    graph_store: GraphStore = Depends(get_graph_store),
) -> AgentService:
    """Agent Layer over retrieval + trust + graph + intelligence (Phase 8)."""
    chunk_repo = ChunkRepository(session)
    search = SearchService(embedder, store, chunk_repo, graph_store)
    trust = TrustService(TrustRepository(session), chunk_repo, graph_store)
    intelligence = IntelligenceService(graph_store, trust)
    return AgentService(
        AgentRepository(session), search, trust, graph_store, intelligence
    )


def get_trust_repo(session: AsyncSession = Depends(get_session)) -> TrustRepository:
    return TrustRepository(session)


def get_trust_service(
    session: AsyncSession = Depends(get_session),
    graph_store: GraphStore = Depends(get_graph_store),
) -> TrustService:
    """Trust scoring over documents + processing/embedding state + the graph (Phase 5)."""
    return TrustService(
        TrustRepository(session),
        ChunkRepository(session),
        graph_store,
    )
