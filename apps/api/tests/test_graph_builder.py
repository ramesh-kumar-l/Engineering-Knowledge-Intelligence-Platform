"""Graph projection unit tests — deterministic, no DB (ADR-0013)."""

from __future__ import annotations

import uuid

from app.domain.enums import DocumentCategory, EntityKind, RelationshipType, SourceType
from app.graph import builder
from app.models.connector import Connector
from app.models.document import Document
from app.models.enrichment import DocumentEnrichment


def _connector() -> Connector:
    c = Connector(
        tenant_id="acme",
        source_type=SourceType.GITHUB,
        name="repo",
        config={"owner": "octo", "repo": "app"},
    )
    c.id = uuid.uuid4()
    return c


def _document(connector_id: uuid.UUID, title: str, **meta: object) -> Document:
    d = Document(
        tenant_id="acme",
        connector_id=connector_id,
        source_type=SourceType.GITHUB,
        external_id="1",
        title=title,
        content_hash="h",
        doc_metadata=dict(meta),
        is_deleted=False,
    )
    d.id = uuid.uuid4()
    return d


def _enrichment(category: DocumentCategory) -> DocumentEnrichment:
    return DocumentEnrichment(
        tenant_id="acme",
        document_id=uuid.uuid4(),
        source_content_hash="h",
        category=category,
        summary="A summary",
    )


def _keys(entities: list) -> dict[str, EntityKind]:
    return {e.key: e.kind for e in entities}


def test_github_connector_projects_repository_and_owning_team() -> None:
    entities, rels = builder.project("acme", [_connector()], [])
    keys = _keys(entities)
    assert "repository:octo/app" in keys
    assert "team:octo" in keys
    assert any(
        r.type == RelationshipType.OWNS
        and r.from_key == "team:octo"
        and r.to_key == "repository:octo/app"
        for r in rels
    )


def test_author_modifies_document_and_repository() -> None:
    connector = _connector()
    doc = _document(connector.id, "Fix login", author="alice")
    entities, rels = builder.project("acme", [connector], [(doc, None)])
    keys = _keys(entities)
    assert "engineer:alice" in keys
    assert f"document:{doc.id}" in keys
    rel_pairs = {(r.type, r.from_key, r.to_key) for r in rels}
    assert (RelationshipType.MODIFIED, "engineer:alice", f"document:{doc.id}") in rel_pairs
    assert (
        RelationshipType.MODIFIED,
        "engineer:alice",
        "repository:octo/app",
    ) in rel_pairs


def test_incident_impacts_repo_and_closed_incident_is_resolved() -> None:
    connector = _connector()
    doc = _document(connector.id, "Outage", author="bob", state="closed")
    entities, rels = builder.project(
        "acme", [connector], [(doc, _enrichment(DocumentCategory.INCIDENT))]
    )
    assert f"incident:{doc.id}" in _keys(entities)
    rel_pairs = {(r.type, r.from_key, r.to_key) for r in rels}
    assert (
        RelationshipType.IMPACTS,
        f"incident:{doc.id}",
        "repository:octo/app",
    ) in rel_pairs
    assert (RelationshipType.RESOLVED, "engineer:bob", f"incident:{doc.id}") in rel_pairs


def test_adr_title_projects_adr_entity() -> None:
    connector = _connector()
    doc = _document(connector.id, "ADR-0007: Choose Neo4j", author="carol")
    entities, _ = builder.project("acme", [connector], [(doc, None)])
    assert f"adr:{doc.id}" in _keys(entities)


def test_deleted_document_is_skipped() -> None:
    connector = _connector()
    doc = _document(connector.id, "Gone", author="alice")
    doc.is_deleted = True
    entities, _ = builder.project("acme", [connector], [(doc, None)])
    keys = _keys(entities)
    assert "engineer:alice" not in keys
    assert f"document:{doc.id}" not in keys
