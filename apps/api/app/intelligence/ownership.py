"""Ownership intelligence — coverage and concentration over the graph (Phase 7).

Pure and deterministic. A tracked component (repository, service, document) is *owned*
if some ``owns`` (team → component) or ``modified`` (engineer → component) edge points
at it — the same evidence the trust layer uses, never guessed. The report gives
per-kind coverage, the orphaned components (no owner), and the owners carrying the most
load (key-person / bus-factor risk). Absence of ownership data is surfaced, not hidden.
"""

from __future__ import annotations

from app.domain.enums import EntityKind
from app.graph.base import GraphEntity, GraphRelationship
from app.intelligence.base import (
    NodeRef,
    OwnerLoad,
    OwnershipCoverage,
    OwnershipReport,
    kind_of,
)

# Components whose ownership we hold the platform accountable for.
TRACKED_KINDS = (EntityKind.REPOSITORY, EntityKind.SERVICE, EntityKind.DOCUMENT)


def analyze_ownership(
    entities_by_kind: dict[EntityKind, list[GraphEntity]],
    owns: list[GraphRelationship],
    modified: list[GraphRelationship],
    limit: int = 100,
) -> OwnershipReport:
    tracked_keys = {
        e.key for ents in entities_by_kind.values() for e in ents
    }
    ownership_edges = owns + modified
    owned_keys = {r.to_key for r in ownership_edges if r.to_key in tracked_keys}

    coverages: list[OwnershipCoverage] = []
    orphans: list[NodeRef] = []
    overall_total = 0
    overall_owned = 0
    for kind in TRACKED_KINDS:
        ents = entities_by_kind.get(kind, [])
        owned = sum(1 for e in ents if e.key in owned_keys)
        coverages.append(
            OwnershipCoverage(
                kind=kind,
                total=len(ents),
                owned=owned,
                unowned=len(ents) - owned,
                coverage=round(owned / len(ents), 4) if ents else 0.0,
            )
        )
        overall_total += len(ents)
        overall_owned += owned
        orphans.extend(
            NodeRef(e.key, e.name, kind) for e in ents if e.key not in owned_keys
        )

    orphans.sort(key=lambda n: (n.kind.value, n.name.lower()))
    return OwnershipReport(
        overall_total=overall_total,
        overall_owned=overall_owned,
        overall_coverage=round(overall_owned / overall_total, 4) if overall_total else 0.0,
        coverages=coverages,
        orphans=orphans[:limit],
        top_owners=_top_owners(ownership_edges, tracked_keys, limit),
    )


def _top_owners(
    edges: list[GraphRelationship], tracked_keys: set[str], limit: int
) -> list[OwnerLoad]:
    owned: dict[str, set[str]] = {}
    names: dict[str, str] = {}
    for edge in edges:
        if edge.to_key not in tracked_keys:
            continue
        owned.setdefault(edge.from_key, set()).add(edge.to_key)
        names.setdefault(edge.from_key, edge.from_name or edge.from_key)
    loads = [
        OwnerLoad(
            key=key,
            name=names[key],
            kind=kind_of(key),
            owned_count=len(targets),
        )
        for key, targets in owned.items()
    ]
    loads.sort(key=lambda o: (-o.owned_count, o.name.lower()))
    return loads[:limit]
