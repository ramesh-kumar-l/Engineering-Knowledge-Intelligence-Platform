"""Pure ownership analyzer — coverage, orphans and key-person load (Phase 7)."""

from __future__ import annotations

from app.domain.enums import EntityKind, GraphSource, RelationshipType
from app.graph.base import GraphEntity, GraphRelationship
from app.intelligence.ownership import analyze_ownership


def _entity(kind: EntityKind, key: str, name: str) -> GraphEntity:
    return GraphEntity(tenant_id="acme", kind=kind, key=key, name=name)


def _edge(rtype: RelationshipType, from_key: str, to_key: str) -> GraphRelationship:
    return GraphRelationship(
        tenant_id="acme",
        type=rtype,
        from_key=from_key,
        to_key=to_key,
        source=GraphSource.PROJECTION,
        from_name=from_key.split(":", 1)[1],
    )


def test_coverage_orphans_and_owners() -> None:
    by_kind = {
        EntityKind.REPOSITORY: [
            _entity(EntityKind.REPOSITORY, "repository:a", "a"),
            _entity(EntityKind.REPOSITORY, "repository:b", "b"),
        ],
        EntityKind.SERVICE: [_entity(EntityKind.SERVICE, "service:c", "c")],
        EntityKind.DOCUMENT: [_entity(EntityKind.DOCUMENT, "document:d", "d")],
    }
    owns = [_edge(RelationshipType.OWNS, "team:core", "repository:a")]
    modified = [_edge(RelationshipType.MODIFIED, "engineer:octo", "document:d")]

    report = analyze_ownership(by_kind, owns, modified)

    assert report.overall_total == 4
    assert report.overall_owned == 2  # repository:a + document:d
    assert report.overall_coverage == 0.5
    # repository:b and service:c are orphaned.
    orphan_keys = {o.key for o in report.orphans}
    assert orphan_keys == {"repository:b", "service:c"}
    # team:core owns one tracked component -> appears in top owners.
    top = {o.key: o.owned_count for o in report.top_owners}
    assert top["team:core"] == 1
    assert top["engineer:octo"] == 1


def test_coverage_handles_empty_kinds() -> None:
    report = analyze_ownership({EntityKind.SERVICE: []}, [], [])
    assert report.overall_total == 0
    assert report.overall_coverage == 0.0
    # All tracked kinds appear with zero totals.
    kinds = {c.kind for c in report.coverages}
    assert EntityKind.REPOSITORY in kinds
    assert EntityKind.DOCUMENT in kinds
