"""Shared test fixtures.

Tests must not require live datastores. ``client`` provides a TestClient over the
app; ``make_client`` simulates datastore health for readiness; ``db_client`` and
``db_session`` back the ingestion layer with an in-memory SQLite database so the real
repositories/services run without PostgreSQL.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - registers all tables on Base.metadata
from app.api.deps import (
    get_datastores,
    get_graph_store,
    get_session,
    get_vector_store,
)
from app.core.config import Settings
from app.core.db.registry import DataStoreStatus
from app.graph.store import InMemoryGraphStore
from app.main import create_app
from app.models.base import Base
from app.retrieval.vector_store import InMemoryVectorStore


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
    # auto_create_schema off: tests own their SQLite schema explicitly.
    return Settings(env="development", log_level="WARNING", auto_create_schema=False)


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


@pytest.fixture
async def db_sessionmaker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """In-memory SQLite shared across sessions via a single pooled connection."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def db_session(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with db_sessionmaker() as session:
        yield session


@pytest.fixture
def db_client(
    settings: Settings, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> Iterator[TestClient]:
    """A TestClient whose routes use the in-memory SQLite session."""
    app = create_app(settings)

    async def _get_session() -> AsyncIterator[AsyncSession]:
        async with db_sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = _get_session
    # Neo4j has no embeddable test engine; an in-memory store stands in for the graph
    # (ADR-0012), shared across requests so a build is visible to later reads.
    graph_store = InMemoryGraphStore()
    app.dependency_overrides[get_graph_store] = lambda: graph_store
    # Qdrant has no embeddable test engine; an in-memory store stands in for the vector
    # store (ADR-0015), shared across requests so an embed run is visible to later search.
    vector_store = InMemoryVectorStore()
    app.dependency_overrides[get_vector_store] = lambda: vector_store
    with TestClient(app) as test_client:
        yield test_client
