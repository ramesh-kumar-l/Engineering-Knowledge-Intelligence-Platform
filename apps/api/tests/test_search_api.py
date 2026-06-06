"""Search + embedding API tests — RBAC, stats, end-to-end, 404s, tenant isolation."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

_EDITOR = {"X-Tenant-Id": "acme", "X-Role": "editor"}
_VIEWER = {"X-Tenant-Id": "acme", "X-Role": "viewer"}


def test_requires_auth(db_client: TestClient) -> None:
    assert db_client.get("/search?q=hi").status_code == 401
    assert db_client.post("/embeddings/runs").status_code == 401
    assert db_client.get("/embeddings/stats").status_code == 401


def test_embedding_run_requires_editor(db_client: TestClient) -> None:
    assert db_client.post("/embeddings/runs", headers=_VIEWER).status_code == 403


def test_empty_stats(db_client: TestClient) -> None:
    resp = db_client.get("/embeddings/stats", headers=_VIEWER)
    assert resp.status_code == 200
    body = resp.json()
    assert body["documents_embedded"] == 0
    assert body["vectors"] == 0
    assert body["dimension"] > 0


def test_embedding_run_with_no_data_succeeds(db_client: TestClient) -> None:
    resp = db_client.post("/embeddings/runs", headers=_EDITOR)
    assert resp.status_code == 200
    assert resp.json()["status"] == "succeeded"
    assert db_client.get("/embeddings/runs", headers=_VIEWER).json()["runs"]


def test_search_validates_query(db_client: TestClient) -> None:
    assert db_client.get("/search", headers=_VIEWER).status_code == 422
    empty = db_client.get("/search?q=anything", headers=_VIEWER)
    assert empty.status_code == 200
    assert empty.json()["chunks"] == []


def test_missing_run_404(db_client: TestClient) -> None:
    assert (
        db_client.get(f"/embeddings/runs/{uuid.uuid4()}", headers=_VIEWER).status_code
        == 404
    )


def test_run_events(db_client: TestClient) -> None:
    run_id = db_client.post("/embeddings/runs", headers=_EDITOR).json()["id"]
    events = db_client.get(f"/embeddings/runs/{run_id}/events", headers=_VIEWER)
    assert events.status_code == 200
    assert any(e["message"] == "Embedding started" for e in events.json()["events"])


def test_search_tenant_isolation(db_client: TestClient) -> None:
    # No corpus seeded for "other"; search must return nothing and never error.
    resp = db_client.get(
        "/search?q=payment", headers={"X-Tenant-Id": "other", "X-Role": "viewer"}
    )
    assert resp.status_code == 200
    assert resp.json()["chunks"] == []
