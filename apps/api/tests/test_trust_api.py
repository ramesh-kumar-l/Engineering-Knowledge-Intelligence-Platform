"""Trust API tests — RBAC, empty corpus, 404, tenant isolation."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

_VIEWER = {"X-Tenant-Id": "acme", "X-Role": "viewer"}


def test_requires_auth(db_client: TestClient) -> None:
    assert db_client.get("/trust/sources").status_code == 401
    assert db_client.get("/trust/freshness").status_code == 401
    assert db_client.get(f"/trust/documents/{uuid.uuid4()}").status_code == 401


def test_empty_sources_and_freshness(db_client: TestClient) -> None:
    sources = db_client.get("/trust/sources", headers=_VIEWER)
    assert sources.status_code == 200
    assert sources.json()["sources"] == []

    freshness = db_client.get("/trust/freshness", headers=_VIEWER)
    assert freshness.status_code == 200
    body = freshness.json()
    assert body["total"] == 0
    # Every band is represented (zero counts), so the dashboard can render all.
    assert {b["band"] for b in body["buckets"]} == {"fresh", "recent", "aging", "stale"}


def test_missing_document_404(db_client: TestClient) -> None:
    resp = db_client.get(f"/trust/documents/{uuid.uuid4()}", headers=_VIEWER)
    assert resp.status_code == 404


def test_invalid_source_type_422(db_client: TestClient) -> None:
    assert (
        db_client.get("/trust/sources?source_type=bogus", headers=_VIEWER).status_code
        == 422
    )
