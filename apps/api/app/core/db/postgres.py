"""PostgreSQL client — system of record (ADR-0004).

Wraps a SQLAlchemy async engine and exposes an async session factory used by the
repository layer. Connection is lazy/pooled so a transient outage does not crash
startup — readiness reports it instead.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.db.base import DataStoreStatus
from app.models.base import Base


class PostgresStore:
    name = "postgres"

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        # pool_pre_ping recycles dead connections — resilience for long-lived pools.
        self._engine = create_async_engine(self._dsn, pool_pre_ping=True, future=True)
        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False
        )

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise RuntimeError("PostgresStore is not connected")
        return self._session_factory

    async def create_all(self) -> None:
        """Create ORM tables (dev convenience; production uses migrations)."""
        if self._engine is None:
            raise RuntimeError("PostgresStore is not connected")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def health_check(self) -> DataStoreStatus:
        if self._engine is None:
            return DataStoreStatus(self.name, healthy=False, detail="not connected")
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return DataStoreStatus(self.name, healthy=True)
        except Exception as exc:  # noqa: BLE001 - surfaced as readiness detail
            return DataStoreStatus(self.name, healthy=False, detail=str(exc))
