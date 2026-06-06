"""Deterministic graph projection (ADR-0013).

Derives entities and relationships from already-ingested data — connectors, documents
and their Phase 2 enrichment — with no LLM/NER, mirroring the deterministic processing
pipeline (ADR-0010). Pure and side-effect free: it takes loaded rows and returns the
graph to upsert, so it is fully unit-testable. Services, APIs and ``depends_on`` edges
are not auto-derivable and are added via editor curation instead.
"""

from __future__ import annotations

import re

from app.domain.enums import EntityKind, GraphSource, RelationshipType
from app.graph.base import GraphEntity, GraphRelationship, entity_key
from app.models.connector import Connector
from app.models.document import Document
from app.models.enrichment import DocumentEnrichment

_ADR_RE = re.compile(r"adr[\s:_-]*\d+", re.IGNORECASE)


class _Projection:
    """Accumulates de-duplicated entities/relationships for one tenant."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant = tenant_id
        self._entities: dict[str, GraphEntity] = {}
        self._rels: dict[tuple[str, str, str], GraphRelationship] = {}

    def entity(self, kind: EntityKind, key: str, name: str, **extra: str | None) -> str:
        if key not in self._entities:
            self._entities[key] = GraphEntity(
                tenant_id=self._tenant,
                kind=kind,
                key=key,
                name=name,
                source=GraphSource.PROJECTION,
                summary=extra.get("summary"),
                url=extra.get("url"),
                category=extra.get("category"),
            )
        return key

    def relate(self, type_: RelationshipType, from_key: str, to_key: str) -> None:
        self._rels[(type_.value, from_key, to_key)] = GraphRelationship(
            tenant_id=self._tenant,
            type=type_,
            from_key=from_key,
            to_key=to_key,
            source=GraphSource.PROJECTION,
        )

    def result(self) -> tuple[list[GraphEntity], list[GraphRelationship]]:
        return list(self._entities.values()), list(self._rels.values())


def _repo_for_connector(p: _Projection, connector: Connector) -> str:
    """Project a Repository (and owning Team) for a connector; return the repo key."""
    owner = connector.config.get("owner")
    repo = connector.config.get("repo")
    if owner and repo:
        repo_key = p.entity(EntityKind.REPOSITORY, entity_key(
            EntityKind.REPOSITORY, f"{owner}/{repo}"), f"{owner}/{repo}")
        team_key = p.entity(EntityKind.TEAM, entity_key(EntityKind.TEAM, owner), owner)
        p.relate(RelationshipType.OWNS, team_key, repo_key)
        return repo_key
    return p.entity(
        EntityKind.REPOSITORY,
        entity_key(EntityKind.REPOSITORY, f"connector:{connector.id}"),
        connector.name,
    )


def project(
    tenant_id: str,
    connectors: list[Connector],
    documents: list[tuple[Document, DocumentEnrichment | None]],
) -> tuple[list[GraphEntity], list[GraphRelationship]]:
    """Build the graph for a tenant from connectors + (document, enrichment) rows."""
    p = _Projection(tenant_id)
    repo_by_connector = {c.id: _repo_for_connector(p, c) for c in connectors}

    for document, enrichment in documents:
        if document.is_deleted:
            continue
        repo_key = repo_by_connector.get(document.connector_id)
        doc_key = p.entity(
            EntityKind.DOCUMENT,
            entity_key(EntityKind.DOCUMENT, str(document.id)),
            document.title,
            url=document.url,
            summary=enrichment.summary if enrichment else None,
            category=enrichment.category.value if enrichment else None,
        )

        author = (document.doc_metadata or {}).get("author")
        eng_key: str | None = None
        if author:
            eng_key = p.entity(EntityKind.ENGINEER, entity_key(
                EntityKind.ENGINEER, str(author)), str(author))
            p.relate(RelationshipType.MODIFIED, eng_key, doc_key)
            if repo_key:
                p.relate(RelationshipType.MODIFIED, eng_key, repo_key)

        _project_typed(p, document, enrichment, doc_key, repo_key, eng_key)

    return p.result()


def _project_typed(
    p: _Projection,
    document: Document,
    enrichment: DocumentEnrichment | None,
    doc_key: str,
    repo_key: str | None,
    eng_key: str | None,
) -> None:
    """Project Incident/ADR entities + their edges from a document's classification."""
    meta = document.doc_metadata or {}
    is_incident = enrichment is not None and enrichment.category.value == "incident"
    if is_incident:
        inc_key = p.entity(EntityKind.INCIDENT, entity_key(
            EntityKind.INCIDENT, str(document.id)), document.title, url=document.url)
        if repo_key:
            p.relate(RelationshipType.IMPACTS, inc_key, repo_key)
        if eng_key and meta.get("state") == "closed":
            p.relate(RelationshipType.RESOLVED, eng_key, inc_key)

    if _ADR_RE.match(document.title.strip()):
        adr_key = p.entity(EntityKind.ADR, entity_key(
            EntityKind.ADR, str(document.id)), document.title, url=document.url)
        if eng_key:
            p.relate(RelationshipType.MODIFIED, eng_key, adr_key)
