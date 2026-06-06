"""Knowledge-graph engine (Phase 3).

``build`` projects a tenant's connectors + documents into the graph store
deterministically (ADR-0013) and records a ``GraphBuildRun`` with counters + events
(synchronous execution, ADR-0009). ``create_entity``/``create_relationship`` let an
editor curate entities and edges (e.g. Services and ``depends_on``) the projection
cannot derive. Read methods delegate to the store for the explorer screens.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.enums import (
    EntityKind,
    GraphSource,
    RelationshipType,
    SyncEventLevel,
    SyncStatus,
)
from app.graph import builder
from app.graph.base import (
    GraphEntity,
    GraphNeighborhood,
    GraphRelationship,
    GraphStats,
    entity_key,
    slugify,
)
from app.graph.store import GraphStore
from app.models.graph import GraphBuildEvent, GraphBuildRun
from app.repositories.connectors import ConnectorRepository
from app.repositories.documents import DocumentRepository
from app.repositories.graph_build import GraphBuildRepository


def _now() -> datetime:
    return datetime.now(UTC)


class GraphService:
    def __init__(
        self,
        build_repo: GraphBuildRepository,
        connector_repo: ConnectorRepository,
        document_repo: DocumentRepository,
        store: GraphStore,
    ) -> None:
        self._runs = build_repo
        self._connectors = connector_repo
        self._documents = document_repo
        self._store = store

    async def build(self, tenant_id: str, limit: int = 1000) -> GraphBuildRun:
        run = await self._runs.add_run(
            GraphBuildRun(
                tenant_id=tenant_id, status=SyncStatus.RUNNING, started_at=_now()
            )
        )
        self._event(run, SyncEventLevel.INFO, "Graph build started")
        try:
            await self._store.ensure_schema()
            connectors = await self._connectors.list(tenant_id)
            documents = list(
                await self._documents.list_with_enrichment(tenant_id, limit)
            )
            run.documents_seen = len(documents)

            entities, relationships = builder.project(tenant_id, connectors, documents)
            for entity in entities:
                await self._store.upsert_entity(entity)
            for rel in relationships:
                await self._store.upsert_relationship(rel)

            run.entity_count = len(entities)
            run.relationship_count = len(relationships)
            run.status = SyncStatus.SUCCEEDED
            self._event(
                run,
                SyncEventLevel.INFO,
                f"Graph build succeeded: {len(entities)} entities, "
                f"{len(relationships)} relationships from {len(documents)} documents",
            )
        except Exception as exc:  # noqa: BLE001 - recorded on the run, not raised
            run.status = SyncStatus.FAILED
            run.error = str(exc)
            self._event(run, SyncEventLevel.ERROR, f"Graph build failed: {exc}")
        finally:
            run.finished_at = _now()
        return run

    async def create_entity(
        self,
        tenant_id: str,
        kind: EntityKind,
        name: str,
        summary: str | None = None,
        url: str | None = None,
    ) -> GraphEntity:
        entity = GraphEntity(
            tenant_id=tenant_id,
            kind=kind,
            key=entity_key(kind, slugify(name)),
            name=name,
            source=GraphSource.MANUAL,
            summary=summary,
            url=url,
        )
        await self._store.upsert_entity(entity)
        return entity

    async def create_relationship(
        self,
        tenant_id: str,
        type: RelationshipType,
        from_kind: EntityKind,
        from_name: str,
        to_kind: EntityKind,
        to_name: str,
    ) -> GraphRelationship:
        """Curate an edge, auto-creating both endpoints if they do not exist yet."""
        src = await self.create_entity(tenant_id, from_kind, from_name)
        dst = await self.create_entity(tenant_id, to_kind, to_name)
        rel = GraphRelationship(
            tenant_id=tenant_id,
            type=type,
            from_key=src.key,
            to_key=dst.key,
            source=GraphSource.MANUAL,
            from_kind=src.kind,
            from_name=src.name,
            to_kind=dst.kind,
            to_name=dst.name,
        )
        await self._store.upsert_relationship(rel)
        return rel

    async def stats(self, tenant_id: str) -> GraphStats:
        return await self._store.stats(tenant_id)

    async def list_entities(
        self,
        tenant_id: str,
        kind: EntityKind | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[GraphEntity]:
        return await self._store.list_entities(tenant_id, kind, search, limit, offset)

    async def neighborhood(
        self, tenant_id: str, key: str
    ) -> GraphNeighborhood | None:
        return await self._store.neighborhood(tenant_id, key)

    async def list_relationships(
        self,
        tenant_id: str,
        type: RelationshipType | None = None,
        limit: int = 200,
    ) -> list[GraphRelationship]:
        return await self._store.list_relationships(tenant_id, type, limit)

    def _event(
        self, run: GraphBuildRun, level: SyncEventLevel, message: str
    ) -> None:
        self._runs.add_event(
            GraphBuildEvent(
                graph_build_run_id=run.id,
                tenant_id=run.tenant_id,
                level=level,
                message=message,
            )
        )
