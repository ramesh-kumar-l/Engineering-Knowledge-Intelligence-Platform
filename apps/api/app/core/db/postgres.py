"""PostgreSQL client — system of record (ADR-0004).

Wraps a SQLAlchemy async engine. Phase 0 only needs connectivity + a health probe;
ORM models and repositories arrive with the entities they back (Phase 1+).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.db.base import DataStoreStatus


class PostgresStore:
    name = "postgres"

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._engine: AsyncEngine | None = None

    async def connect(self) -> None:
        # pool_pre_ping recycles dead connections — resilience for long-lived pools.
        self._engine = create_async_engine(self._dsn, pool_pre_ping=True, future=True)

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None

    async def health_check(self) -> DataStoreStatus:
        if self._engine is None:
            return DataStoreStatus(self.name, healthy=False, detail="not connected")
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return DataStoreStatus(self.name, healthy=True)
        except Exception as exc:  # noqa: BLE001 - surfaced as readiness detail
            return DataStoreStatus(self.name, healthy=False, detail=str(exc))
