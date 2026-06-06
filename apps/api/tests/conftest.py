"""Shared test fixtures.

Tests must not require live datastores. ``client`` provides a TestClient over the
app; ``stub_datastores`` overrides the readiness dependency so datastore health can
be simulated deterministically.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_datastores
from app.core.config import Settings
from app.core.db.registry import DataStoreStatus
from app.main import create_app


class FakeDataStores:
    """Test double for the datastore registry — no network I/O."""

    def __init__(self, statuses: list[DataStoreStatus]) -> None:
        self._statuses = statuses

    async def connect(self) -> None: ...
    async def close(self) -> None: ...

    async def health_check(self) -> list[DataStoreStatus]:
        return self._statuses


@pytest.fixture
def settings() -> Settings:
    return Settings(env="development", log_level="WARNING")


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_client(settings: Settings):
    """Factory: build a client whose readiness sees the given datastore statuses."""

    def _make(statuses: list[DataStoreStatus]) -> TestClient:
        app = create_app(settings)
        app.dependency_overrides[get_datastores] = lambda: FakeDataStores(statuses)
        return TestClient(app)

    return _make
