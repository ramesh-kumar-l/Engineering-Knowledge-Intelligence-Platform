"""Sync engine tests — change tracking and failure capture (against SQLite)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import FetchResult, RawDocument
from app.domain.enums import ConnectorStatus, SourceType, SyncStatus
from app.models.connector import Connector
from app.repositories.documents import DocumentRepository
from app.repositories.sync import SyncRepository
from app.services.sync_service import SyncService


class FakeConnector:
    source_type = SourceType.GITHUB

    def __init__(self, results: Sequence[FetchResult]) -> None:
        self._results = list(results)
        self._calls = 0

    async def fetch(self, cursor: str | None) -> FetchResult:
        result = self._results[self._calls]
        self._calls += 1
        return result


class BoomConnector:
    source_type = SourceType.GITHUB

    async def fetch(self, cursor: str | None) -> FetchResult:
        raise RuntimeError("boom")


async def _connector(session: AsyncSession) -> Connector:
    model = Connector(
        tenant_id="acme", source_type=SourceType.GITHUB, name="repo", config={}
    )
    session.add(model)
    await session.flush()
    return model


def _service(session: AsyncSession) -> SyncService:
    return SyncService(SyncRepository(session), DocumentRepository(session))


async def test_creates_then_reports_unchanged(db_session: AsyncSession) -> None:
    connector = await _connector(db_session)
    service = _service(db_session)
    doc = RawDocument(external_id="1", title="Title", content="hello")

    run1 = await service.run(connector, FakeConnector([FetchResult([doc], cursor="c1")]))
    assert run1.status == SyncStatus.SUCCEEDED
    assert run1.created_count == 1
    assert connector.cursor == "c1"

    run2 = await service.run(connector, FakeConnector([FetchResult([doc], cursor="c2")]))
    assert run2.created_count == 0
    assert run2.unchanged_count == 1
    assert connector.cursor == "c2"


async def test_detects_update(db_session: AsyncSession) -> None:
    connector = await _connector(db_session)
    service = _service(db_session)

    await service.run(
        connector, FakeConnector([FetchResult([RawDocument("1", "T", "v1")])])
    )
    run = await service.run(
        connector, FakeConnector([FetchResult([RawDocument("1", "T", "v2")])])
    )
    assert run.updated_count == 1


async def test_soft_delete(db_session: AsyncSession) -> None:
    connector = await _connector(db_session)
    service = _service(db_session)

    await service.run(connector, FakeConnector([FetchResult([RawDocument("1", "T", "v")])]))
    run = await service.run(
        connector, FakeConnector([FetchResult([], cursor="c", deleted_ids=["1"])])
    )
    assert run.deleted_count == 1


async def test_failure_is_recorded(db_session: AsyncSession) -> None:
    connector = await _connector(db_session)
    service = _service(db_session)

    run = await service.run(connector, BoomConnector())
    assert run.status == SyncStatus.FAILED
    assert run.error is not None and "boom" in run.error
    assert connector.status == ConnectorStatus.ERROR
