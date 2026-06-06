"""Intelligence API tests — RBAC + response shape over the in-memory stores (Phase 7)."""

from __future__ import annotations

from fastapi.testclient import TestClient

_VIEWER = {"X-Tenant-Id": "acme", "X-Role": "viewer"}

_ENDPOINTS = [
    "/intelligence/overview",
    "/intelligence/dependencies",
    "/intelligence/debt",
    "/intelligence/incidents",
    "/intelligence/ownership",
]


def test_requires_auth(db_client: TestClient) -> None:
    for path in _ENDPOINTS:
        assert db_client.get(path).status_code == 401


def test_endpoints_return_empty_reports(db_client: TestClient) -> None:
    for path in _ENDPOINTS:
        resp = db_client.get(path, headers=_VIEWER)
        assert resp.status_code == 200, path

    overview = db_client.get("/intelligence/overview", headers=_VIEWER).json()
    assert overview["debt_count"] == 0
    assert overview["incidents_total"] == 0
    assert overview["ownership_coverage"] == 0.0


def test_dependencies_shape(db_client: TestClient) -> None:
    body = db_client.get("/intelligence/dependencies", headers=_VIEWER).json()
    assert body["total_nodes"] == 0
    assert set(body["by_risk"]) == {"high", "medium", "low"}
    assert body["nodes"] == []
    assert body["cycles"] == []


def test_ownership_lists_tracked_kinds(db_client: TestClient) -> None:
    body = db_client.get("/intelligence/ownership", headers=_VIEWER).json()
    kinds = {c["kind"] for c in body["coverages"]}
    assert kinds == {"repository", "service", "document"}
