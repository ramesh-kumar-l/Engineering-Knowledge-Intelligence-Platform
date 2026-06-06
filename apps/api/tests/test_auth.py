"""Authentication tests — JWT bearer is the boundary; header fallback is dev-only."""

from __future__ import annotations

import jwt
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_valid_jwt_grants_access(db_client: TestClient, settings: Settings) -> None:
    token = jwt.encode(
        {"sub": "u1", "tenant_id": "acme", "role": "viewer"},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    resp = db_client.get("/connectors", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_invalid_jwt_is_rejected(db_client: TestClient) -> None:
    resp = db_client.get("/connectors", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_production_disables_header_fallback() -> None:
    app = create_app(Settings(env="production", auto_create_schema=False))
    with TestClient(app) as client:
        resp = client.get(
            "/connectors/catalog", headers={"X-Tenant-Id": "acme", "X-Role": "viewer"}
        )
        assert resp.status_code == 401
