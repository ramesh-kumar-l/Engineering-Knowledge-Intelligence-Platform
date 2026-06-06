"""Health & readiness endpoint tests (api_catalog.md)."""

from __future__ import annotations

from app import __version__
from app.core.db.registry import DataStoreStatus


def test_health_liveness(client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok", "version": __version__}


def test_health_sets_request_id_header(client) -> None:
    resp = client.get("/health")
    assert resp.headers.get("X-Request-Id")


def test_readiness_all_healthy_returns_200(make_client) -> None:
    client = make_client(
        [
            DataStoreStatus("postgres", healthy=True),
            DataStoreStatus("neo4j", healthy=True),
            DataStoreStatus("qdrant", healthy=True),
        ]
    )
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert {d["name"] for d in body["dependencies"]} == {"postgres", "neo4j", "qdrant"}


def test_readiness_degraded_returns_503(make_client) -> None:
    client = make_client(
        [
            DataStoreStatus("postgres", healthy=True),
            DataStoreStatus("neo4j", healthy=False, detail="connection refused"),
            DataStoreStatus("qdrant", healthy=True),
        ]
    )
    resp = client.get("/health/ready")
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "degraded"
    neo4j = next(d for d in body["dependencies"] if d["name"] == "neo4j")
    assert neo4j["healthy"] is False
    assert neo4j["detail"] == "connection refused"
