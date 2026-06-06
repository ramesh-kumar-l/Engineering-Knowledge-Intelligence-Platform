"""Incident intelligence — impact and resolution over the graph (Phase 7).

Pure and deterministic. Inputs are the tenant's incident entities and the
``impacts`` (incident → component) and ``resolved`` (engineer → incident) edges. An
incident is resolved iff some engineer ``resolved`` it; its impact is the set of
components it touches. Components are ranked by how many incidents have impacted them
(recurring blast radius), and unresolved incidents surface first.
"""

from __future__ import annotations

from app.graph.base import GraphEntity, GraphRelationship
from app.intelligence.base import (
    ImpactedComponent,
    IncidentInsight,
    IncidentReport,
    NodeRef,
    kind_of,
)


def analyze_incidents(
    incidents: list[GraphEntity],
    impacts: list[GraphRelationship],
    resolved: list[GraphRelationship],
    limit: int = 100,
) -> IncidentReport:
    resolved_keys = {r.to_key for r in resolved}
    impacted_by_incident: dict[str, list[NodeRef]] = {}
    component_counts: dict[str, int] = {}
    component_ref: dict[str, NodeRef] = {}

    for edge in impacts:
        ref = NodeRef(
            edge.to_key,
            edge.to_name or edge.to_key,
            edge.to_kind or kind_of(edge.to_key),
        )
        impacted_by_incident.setdefault(edge.from_key, []).append(ref)
        component_counts[edge.to_key] = component_counts.get(edge.to_key, 0) + 1
        component_ref.setdefault(edge.to_key, ref)

    insights: list[IncidentInsight] = []
    resolved_count = 0
    for inc in incidents:
        impacted = sorted(
            impacted_by_incident.get(inc.key, []), key=lambda n: n.name.lower()
        )
        is_resolved = inc.key in resolved_keys
        resolved_count += int(is_resolved)
        insights.append(
            IncidentInsight(
                key=inc.key,
                name=inc.name,
                url=inc.url,
                resolved=is_resolved,
                impacted_count=len(impacted),
                impacted=impacted,
            )
        )

    # Unresolved + widest blast radius first; stable by name.
    insights.sort(key=lambda i: (i.resolved, -i.impacted_count, i.name.lower()))

    components = [
        ImpactedComponent(
            key=key,
            name=component_ref[key].name,
            kind=component_ref[key].kind,
            incident_count=count,
        )
        for key, count in component_counts.items()
    ]
    components.sort(key=lambda c: (-c.incident_count, c.name.lower()))

    return IncidentReport(
        total_incidents=len(incidents),
        resolved_count=resolved_count,
        unresolved_count=len(incidents) - resolved_count,
        incidents=insights[:limit],
        impacted_components=components[:limit],
    )
