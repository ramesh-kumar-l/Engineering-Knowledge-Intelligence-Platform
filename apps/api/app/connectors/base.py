"""Connector contract + catalog types (Phase 1 ingestion).

A connector knows how to fetch changed documents from one source. It is deliberately
thin: it yields normalized ``RawDocument`` records and a new cursor; persistence,
change detection and bookkeeping live in the sync service. This keeps connectors easy
to add (one file each) and testable without a database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from app.domain.enums import SourceType


@dataclass(frozen=True)
class RawDocument:
    """A normalized document fetched from a source, before persistence."""

    external_id: str
    title: str
    content: str
    url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    source_updated_at: datetime | None = None


@dataclass(frozen=True)
class FetchResult:
    """Output of one fetch: changed documents, deletions, and the next cursor."""

    documents: list[RawDocument]
    cursor: str | None = None
    deleted_ids: list[str] = field(default_factory=list)


@runtime_checkable
class Connector(Protocol):
    """Fetches changed documents from a source incrementally."""

    source_type: SourceType

    async def fetch(self, cursor: str | None) -> FetchResult:
        """Return documents changed since ``cursor`` (None = full initial sync)."""
        ...


@dataclass(frozen=True)
class ConfigField:
    """A non-secret configuration input for a source (drives the catalog UI)."""

    key: str
    label: str
    required: bool = True


@dataclass(frozen=True)
class ConnectorSpec:
    """Catalog metadata describing a source type and how to configure it."""

    source_type: SourceType
    label: str
    description: str
    implemented: bool
    config_fields: list[ConfigField] = field(default_factory=list)
    # Name of the credential field, or None for sources needing no secret.
    secret_label: str | None = None
