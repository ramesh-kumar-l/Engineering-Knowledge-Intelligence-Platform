"""Processing API tests — trigger, stats, explorer, RBAC, tenant isolation (SQLite)."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

_EDITOR = {"X-Tenant-Id": "acme", "X-Role": "editor"}
_VIEWER = {"X-Tenant-Id": "acme", "X-Role": "viewer"}
_GITHUB_PAYLOAD = {
    "source_type": "github",
    "name": "My repo",
    "config": {"owner": "o", "repo": "r"},
    "secret": "ghp_token",
}


def _seed_connector(client: TestClient) -> str:
    created = client.post("/connectors", json=_GITHUB_PAYLOAD, headers=_EDITOR)
    assert created.status_code == 201
    return created.json()["id"]


def test_requires_auth(db_client: TestClient) -> None:
    assert db_client.post("/processing/runs").status_code == 401
    assert db_client.get("/processing/stats").status_code == 401


def test_trigger_requires_editor(db_client: TestClient) -> None:
    assert db_client.post("/processing/runs", headers=_VIEWER).status_code == 403


def test_empty_stats(db_client: TestClient) -> None:
    resp = db_client.get("/processing/stats", headers=_VIEWER)
    assert resp.status_code == 200
    body = resp.json()
    assert body["documents_processed"] == 0
    assert body["total_chunks"] == 0
    assert body["category_distribution"] == {}


def test_run_with_no_documents_succeeds(db_client: TestClient) -> None:
    resp = db_client.post("/processing/runs", headers=_EDITOR)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "succeeded"
    assert body["documents_seen"] == 0
    assert db_client.get("/processing/runs", headers=_VIEWER).json()["runs"]


def test_run_events_and_detail(db_client: TestClient) -> None:
    run_id = db_client.post("/processing/runs", headers=_EDITOR).json()["id"]
    events = db_client.get(f"/processing/runs/{run_id}/events", headers=_VIEWER)
    assert events.status_code == 200
    assert any(e["message"] == "Processing started" for e in events.json()["events"])


def test_missing_run_and_document_404(db_client: TestClient) -> None:
    assert db_client.get(f"/processing/runs/{uuid.uuid4()}", headers=_VIEWER).status_code == 404
    assert (
        db_client.get(f"/processing/documents/{uuid.uuid4()}", headers=_VIEWER).status_code
        == 404
    )


def test_tenant_isolation_on_runs(db_client: TestClient) -> None:
    db_client.post("/processing/runs", headers=_EDITOR)
    other = db_client.get(
        "/processing/runs", headers={"X-Tenant-Id": "other", "X-Role": "viewer"}
    )
    assert other.json()["runs"] == []


def test_processed_documents_empty_initially(db_client: TestClient) -> None:
    _seed_connector(db_client)
    resp = db_client.get("/processing/documents", headers=_VIEWER)
    assert resp.status_code == 200
    assert resp.json()["documents"] == []
