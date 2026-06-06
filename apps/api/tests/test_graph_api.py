"""Graph API tests — build, explorer, curation, RBAC, tenant isolation (SQLite + memory)."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

_EDITOR = {"X-Tenant-Id": "acme", "X-Role": "editor"}
_VIEWER = {"X-Tenant-Id": "acme", "X-Role": "viewer"}


def test_requires_auth(db_client: TestClient) -> None:
    assert db_client.post("/graph/build").status_code == 401
    assert db_client.get("/graph/stats").status_code == 401


def test_build_requires_editor(db_client: TestClient) -> None:
    assert db_client.post("/graph/build", headers=_VIEWER).status_code == 403


def test_empty_stats(db_client: TestClient) -> None:
    resp = db_client.get("/graph/stats", headers=_VIEWER)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_entities"] == 0
    assert body["entities_by_kind"] == {}


def test_build_with_no_data_succeeds(db_client: TestClient) -> None:
    resp = db_client.post("/graph/build", headers=_EDITOR)
    assert resp.status_code == 200
    assert resp.json()["status"] == "succeeded"
    assert db_client.get("/graph/build/runs", headers=_VIEWER).json()["runs"]


def test_curate_entity_and_relationship_then_read(db_client: TestClient) -> None:
    created = db_client.post(
        "/graph/relationships",
        headers=_EDITOR,
        json={
            "type": "depends_on",
            "from_kind": "service",
            "from_name": "Checkout",
            "to_kind": "service",
            "to_name": "Payments",
        },
    )
    assert created.status_code == 200

    entities = db_client.get("/graph/entities?kind=service", headers=_VIEWER).json()
    assert {e["name"] for e in entities["entities"]} == {"Checkout", "Payments"}

    hood = db_client.get("/graph/entity?key=service:checkout", headers=_VIEWER)
    assert hood.status_code == 200
    assert hood.json()["neighbors"][0]["entity"]["key"] == "service:payments"

    deps = db_client.get("/graph/relationships?type=depends_on", headers=_VIEWER).json()
    assert len(deps["relationships"]) == 1


def test_create_entity_requires_editor(db_client: TestClient) -> None:
    resp = db_client.post(
        "/graph/entities",
        headers=_VIEWER,
        json={"kind": "service", "name": "Checkout"},
    )
    assert resp.status_code == 403


def test_missing_entity_and_run_404(db_client: TestClient) -> None:
    assert db_client.get("/graph/entity?key=service:nope", headers=_VIEWER).status_code == 404
    assert (
        db_client.get(f"/graph/build/runs/{uuid.uuid4()}", headers=_VIEWER).status_code
        == 404
    )


def test_tenant_isolation(db_client: TestClient) -> None:
    db_client.post(
        "/graph/entities",
        headers=_EDITOR,
        json={"kind": "service", "name": "Checkout"},
    )
    other = db_client.get(
        "/graph/entities", headers={"X-Tenant-Id": "other", "X-Role": "viewer"}
    )
    assert other.json()["entities"] == []


def test_build_run_events(db_client: TestClient) -> None:
    run_id = db_client.post("/graph/build", headers=_EDITOR).json()["id"]
    events = db_client.get(f"/graph/build/runs/{run_id}/events", headers=_VIEWER)
    assert events.status_code == 200
    assert any(e["message"] == "Graph build started" for e in events.json()["events"])
