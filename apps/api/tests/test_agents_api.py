"""Agent Layer API: auth, catalog, run round-trip, 404 (Phase 8).

Runs against the in-memory stores from ``db_client`` (empty corpus), so the focus is the
HTTP contract + persistence: agents still run, succeed and persist a trace on an empty
knowledge base, surfacing gaps rather than failing.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

_VIEWER = {"X-Tenant-Id": "acme", "X-Role": "viewer"}


def test_endpoints_require_auth(db_client: TestClient) -> None:
    assert db_client.get("/agents/catalog").status_code == 401
    assert db_client.get("/agents/runs").status_code == 401
    assert (
        db_client.post("/agents/runs", json={"agent_type": "maintenance"}).status_code
        == 401
    )


def test_catalog_lists_agents(db_client: TestClient) -> None:
    res = db_client.get("/agents/catalog", headers=_VIEWER)
    assert res.status_code == 200
    agents = res.json()["agents"]
    types = {a["type"] for a in agents}
    assert types == {"incident", "onboarding", "architecture", "maintenance"}
    maintenance = next(a for a in agents if a["type"] == "maintenance")
    assert maintenance["needs_target"] is False


def test_run_and_fetch_round_trip(db_client: TestClient) -> None:
    res = db_client.post(
        "/agents/runs", json={"agent_type": "maintenance"}, headers=_VIEWER
    )
    assert res.status_code == 200
    body = res.json()
    assert body["run"]["status"] == "succeeded"
    assert body["result"] is not None
    assert len(body["steps"]) >= 1
    run_id = body["run"]["id"]

    detail = db_client.get(f"/agents/runs/{run_id}", headers=_VIEWER)
    assert detail.status_code == 200
    assert detail.json()["run"]["id"] == run_id

    listing = db_client.get("/agents/runs", headers=_VIEWER)
    assert listing.status_code == 200
    assert any(r["id"] == run_id for r in listing.json()["runs"])


def test_run_incident_with_target(db_client: TestClient) -> None:
    res = db_client.post(
        "/agents/runs",
        json={"agent_type": "incident", "target": "checkout outage"},
        headers=_VIEWER,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["run"]["agent_type"] == "incident"
    assert body["run"]["target"] == "checkout outage"
    assert body["run"]["status"] == "succeeded"


def test_get_unknown_run_404(db_client: TestClient) -> None:
    res = db_client.get(
        "/agents/runs/00000000-0000-0000-0000-000000000000", headers=_VIEWER
    )
    assert res.status_code == 404


def test_tenant_isolation(db_client: TestClient) -> None:
    created = db_client.post(
        "/agents/runs", json={"agent_type": "maintenance"}, headers=_VIEWER
    ).json()["run"]["id"]
    other = {"X-Tenant-Id": "other", "X-Role": "viewer"}
    assert db_client.get(f"/agents/runs/{created}", headers=other).status_code == 404
    assert db_client.get("/agents/runs", headers=other).json()["runs"] == []
