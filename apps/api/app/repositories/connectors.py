"""Connector data access. All queries are tenant-scoped (ADR-0006 isolation)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.connector import Connector


class ConnectorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, connector: Connector) -> Connector:
        self._session.add(connector)
        await self._session.flush()
        return connector

    async def get(self, tenant_id: str, connector_id: uuid.UUID) -> Connector | None:
        stmt = select(Connector).where(
            Connector.id == connector_id, Connector.tenant_id == tenant_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list(self, tenant_id: str) -> list[Connector]:
        stmt = (
            select(Connector)
            .where(Connector.tenant_id == tenant_id)
            .order_by(Connector.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
