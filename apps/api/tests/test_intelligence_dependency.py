"""Pure dependency analyzer — fan-in/out, risk and cycles (Phase 7)."""

from __future__ import annotations

from app.domain.enums import GraphSource, RelationshipType, RiskBand
from app.graph.base import GraphRelationship
from app.intelligence.dependency import analyze_dependencies


def _dep(from_key: str, to_key: str) -> GraphRelationship:
    return GraphRelationship(
        tenant_id="acme",
        type=RelationshipType.DEPENDS_ON,
        from_key=from_key,
        to_key=to_key,
        source=GraphSource.MANUAL,
        from_name=from_key.split(":", 1)[1],
        to_name=to_key.split(":", 1)[1],
    )


def test_empty_graph_reports_nothing() -> None:
    report = analyze_dependencies([])
    assert report.total_nodes == 0
    assert report.total_dependencies == 0
    assert report.cycle_count == 0
    assert report.nodes == []


def test_fan_in_drives_risk() -> None:
    # B is depended on by A and C -> highest blast radius.
    report = analyze_dependencies(
        [
            _dep("service:a", "service:b"),
            _dep("service:c", "service:b"),
            _dep("service:b", "service:d"),
        ]
    )
    by_key = {n.key: n for n in report.nodes}
    assert by_key["service:b"].fan_in == 2
    assert by_key["service:b"].fan_out == 1
    assert by_key["service:d"].fan_in == 1
    # Nodes are sorted by descending risk; the most-depended-on leads.
    assert report.nodes[0].key == "service:b"
    assert by_key["service:b"].risk_score >= by_key["service:d"].risk_score


def test_cycle_detected_and_members_flagged() -> None:
    report = analyze_dependencies(
        [
            _dep("service:x", "service:y"),
            _dep("service:y", "service:x"),
            _dep("service:z", "service:x"),
        ]
    )
    assert report.cycle_count == 1
    cycle = report.cycles[0]
    assert {m.key for m in cycle.members} == {"service:x", "service:y"}
    by_key = {n.key: n for n in report.nodes}
    assert by_key["service:x"].in_cycle is True
    assert by_key["service:y"].in_cycle is True
    assert by_key["service:z"].in_cycle is False


def test_self_loop_is_a_cycle() -> None:
    report = analyze_dependencies([_dep("service:loop", "service:loop")])
    assert report.cycle_count == 1
    node = report.nodes[0]
    assert node.in_cycle is True
    assert node.fan_in == 0 and node.fan_out == 0  # self-edge is not real fan


def test_by_risk_bands_sum_to_node_count() -> None:
    report = analyze_dependencies(
        [_dep("service:a", "service:b"), _dep("service:c", "service:b")]
    )
    assert sum(report.by_risk.values()) == report.total_nodes
    assert set(report.by_risk) == {b.value for b in RiskBand}
