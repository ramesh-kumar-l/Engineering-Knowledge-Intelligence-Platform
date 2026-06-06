"""Pure incident analyzer — impact + resolution over the graph (Phase 7)."""

from __future__ import annotations

from app.domain.enums import EntityKind, GraphSource, RelationshipType
from app.graph.base import GraphEntity, GraphRelationship
from app.intelligence.incident import analyze_incidents


def _incident(key: str, name: str) -> GraphEntity:
    return GraphEntity(tenant_id="acme", kind=EntityKind.INCIDENT, key=key, name=name)


def _edge(rtype: RelationshipType, from_key: str, to_key: str) -> GraphRelationship:
    return GraphRelationship(
        tenant_id="acme",
        type=rtype,
        from_key=from_key,
        to_key=to_key,
        source=GraphSource.PROJECTION,
        to_name=to_key.split(":", 1)[1],
        to_kind=EntityKind(to_key.split(":", 1)[0]),
    )


def test_resolution_and_impact_counts() -> None:
    incidents = [_incident("incident:1", "Outage A"), _incident("incident:2", "Outage B")]
    impacts = [
        _edge(RelationshipType.IMPACTS, "incident:1", "repository:checkout"),
        _edge(RelationshipType.IMPACTS, "incident:2", "repository:checkout"),
        _edge(RelationshipType.IMPACTS, "incident:2", "repository:ledger"),
    ]
    resolved = [_edge(RelationshipType.RESOLVED, "engineer:octo", "incident:1")]

    report = analyze_incidents(incidents, impacts, resolved)

    assert report.total_incidents == 2
    assert report.resolved_count == 1
    assert report.unresolved_count == 1
    # Unresolved + widest blast radius surfaces first.
    assert report.incidents[0].key == "incident:2"
    assert report.incidents[0].resolved is False
    assert report.incidents[0].impacted_count == 2
    # checkout is hit by both incidents -> top impacted component.
    assert report.impacted_components[0].key == "repository:checkout"
    assert report.impacted_components[0].incident_count == 2


def test_no_incidents() -> None:
    report = analyze_incidents([], [], [])
    assert report.total_incidents == 0
    assert report.incidents == []
    assert report.impacted_components == []
