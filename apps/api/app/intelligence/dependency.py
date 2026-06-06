"""Dependency intelligence — risk and cycles over ``depends_on`` edges (Phase 7).

Pure and deterministic: takes the tenant's ``depends_on`` relationships and returns a
per-component risk profile plus any circular dependencies. Risk is driven mostly by
*fan-in* (how many components depend on this one — its blast radius if it breaks),
with smaller contributions from fan-out and cycle membership. Strongly connected
components of size > 1 (and self-loops) are reported as cycles.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.domain.enums import RiskBand
from app.graph.base import GraphRelationship
from app.intelligence import scoring
from app.intelligence.base import (
    DependencyCycle,
    DependencyNode,
    DependencyReport,
    NodeRef,
    kind_of,
)

# Saturation ceilings + weights for the risk blend (ADR-0020 heuristic).
_FAN_IN_CEIL = 4
_FAN_OUT_CEIL = 4
_W_FAN_IN = 0.55
_W_FAN_OUT = 0.20
_W_CYCLE = 0.25


def analyze_dependencies(
    relationships: list[GraphRelationship], node_limit: int = 100
) -> DependencyReport:
    names = _names(relationships)
    edges = {(r.from_key, r.to_key) for r in relationships}
    adj = _adjacency(names, edges)

    fan_out: dict[str, int] = dict.fromkeys(names, 0)
    fan_in: dict[str, int] = dict.fromkeys(names, 0)
    for src, dst in edges:
        if src == dst:
            continue  # self-loop adds no real fan; counted only as a cycle
        fan_out[src] += 1
        fan_in[dst] += 1

    self_loops = {src for src, dst in edges if src == dst}
    cycles = _cycles(adj, names, self_loops)
    cycle_members = {m.key for c in cycles for m in c.members}

    nodes = [
        _node(key, names[key], fan_in[key], fan_out[key], key in cycle_members)
        for key in names
    ]
    nodes.sort(key=lambda n: (-n.risk_score, n.name.lower()))

    by_risk: dict[str, int] = dict.fromkeys((b.value for b in RiskBand), 0)
    for node in nodes:
        by_risk[node.risk_band.value] += 1

    return DependencyReport(
        total_nodes=len(nodes),
        total_dependencies=len(edges),
        cycle_count=len(cycles),
        by_risk=by_risk,
        nodes=nodes[:node_limit],
        cycles=cycles,
    )


def _names(relationships: list[GraphRelationship]) -> dict[str, str]:
    """Display name per node key, preferring edge-endpoint metadata."""
    names: dict[str, str] = {}
    for r in relationships:
        names.setdefault(r.from_key, r.from_name or r.from_key)
        names.setdefault(r.to_key, r.to_name or r.to_key)
    return names


def _adjacency(
    keys: Iterable[str], edges: set[tuple[str, str]]
) -> dict[str, list[str]]:
    adj: dict[str, list[str]] = {k: [] for k in keys}
    for src, dst in edges:
        if src != dst:
            adj[src].append(dst)
    for out in adj.values():
        out.sort()
    return adj


def _node(
    key: str, name: str, fan_in: int, fan_out: int, in_cycle: bool
) -> DependencyNode:
    score = scoring.clamp(
        _W_FAN_IN * scoring.saturate(fan_in, _FAN_IN_CEIL)
        + _W_FAN_OUT * scoring.saturate(fan_out, _FAN_OUT_CEIL)
        + (_W_CYCLE if in_cycle else 0.0)
    )
    return DependencyNode(
        key=key,
        name=name,
        kind=kind_of(key),
        fan_in=fan_in,
        fan_out=fan_out,
        in_cycle=in_cycle,
        risk_score=round(score, 4),
        risk_band=scoring.risk_band(score),
    )


def _cycles(
    adj: dict[str, list[str]], names: dict[str, str], self_loops: set[str]
) -> list[DependencyCycle]:
    """Circular dependencies: multi-node SCCs plus single nodes with a self-edge."""
    cycles: list[DependencyCycle] = []
    for comp in _sccs(adj):
        if len(comp) <= 1 and comp[0] not in self_loops:
            continue
        refs = [NodeRef(k, names.get(k, k), kind_of(k)) for k in comp]
        refs.sort(key=lambda r: r.name.lower())
        cycles.append(DependencyCycle(members=refs))
    cycles.sort(key=lambda c: (-len(c.members), c.members[0].name.lower()))
    return cycles


def _sccs(adj: dict[str, list[str]]) -> list[list[str]]:
    """Tarjan's strongly-connected components, iterative (no recursion limit)."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    result: list[list[str]] = []
    counter = 0

    for start in sorted(adj):
        if start in index:
            continue
        work: list[tuple[str, int]] = [(start, 0)]
        while work:
            node, pi = work[-1]
            if pi == 0:
                index[node] = low[node] = counter
                counter += 1
                stack.append(node)
                on_stack.add(node)
            descend = False
            neighbors = adj[node]
            i = pi
            while i < len(neighbors):
                nxt = neighbors[i]
                if nxt not in index:
                    work[-1] = (node, i + 1)
                    work.append((nxt, 0))
                    descend = True
                    break
                if nxt in on_stack:
                    low[node] = min(low[node], index[nxt])
                i += 1
            if descend:
                continue
            if low[node] == index[node]:
                comp: list[str] = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    comp.append(member)
                    if member == node:
                        break
                result.append(comp)
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
    return result
