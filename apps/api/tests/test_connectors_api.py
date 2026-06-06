"""Connector / sync / document API tests (RBAC + tenant isolation)."""

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


def test_catalog_lists_sources(db_client: TestClient) -> None:
    resp = db_client.get("/connectors/catalog", headers=_VIEWER)
    assert resp.status_code == 200
    sources = resp.json()["sources"]
    github = next(s for s in sources if s["source_type"] == "github")
    assert github["implemented"] is True
    assert {s["source_type"] for s in sources} >= {"github", "jira", "slack"}


def test_unauthenticated_request_rejected(db_client: TestClient) -> None:
    assert db_client.get("/connectors").status_code == 401


def test_create_then_list_and_get(db_client: TestClient) -> None:
    created = db_client.post("/connectors", json=_GITHUB_PAYLOAD, headers=_EDITOR)
    assert created.status_code == 201
    body = created.json()
    assert body["source_type"] == "github"
    assert body["has_secret"] is True
    assert "secret" not in body  # write-only credential

    listed = db_client.get("/connectors", headers=_VIEWER)
    assert len(listed.json()["connectors"]) == 1

    fetched = db_client.get(f"/connectors/{body['id']}", headers=_VIEWER)
    assert fetched.status_code == 200


def test_create_requires_editor_role(db_client: TestClient) -> None:
    resp = db_client.post("/connectors", json=_GITHUB_PAYLOAD, headers=_VIEWER)
    assert resp.status_code == 403


def test_create_validates_required_config(db_client: TestClient) -> None:
    payload = {**_GITHUB_PAYLOAD, "config": {}}
    resp = db_client.post("/connectors", json=payload, headers=_EDITOR)
    assert resp.status_code == 422


def test_cannot_create_unimplemented_source(db_client: TestClient) -> None:
    payload = {"source_type": "slack", "name": "x", "config": {}, "secret": "t"}
    resp = db_client.post("/connectors", json=payload, headers=_EDITOR)
    assert resp.status_code == 422


def test_tenant_isolation(db_client: TestClient) -> None:
    db_client.post("/connectors", json=_GITHUB_PAYLOAD, headers=_EDITOR)
    other = db_client.get(
        "/connectors", headers={"X-Tenant-Id": "other", "X-Role": "viewer"}
    )
    assert other.json()["connectors"] == []


def test_sync_missing_connector_returns_404(db_client: TestClient) -> None:
    resp = db_client.post(f"/connectors/{uuid.uuid4()}/sync", headers=_EDITOR)
    assert resp.status_code == 404


def test_sync_runs_and_documents_start_empty(db_client: TestClient) -> None:
    assert db_client.get("/sync/runs", headers=_VIEWER).json()["runs"] == []
    assert db_client.get("/documents", headers=_VIEWER).json()["documents"] == []
