"""Shared datastore types — the contract every store client implements.

Kept separate from ``registry`` so concrete clients can depend on the contract
without importing the registry (avoids circular imports).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class DataStoreStatus:
    """Health result for a single store."""

    name: str
    healthy: bool
    detail: str | None = None


@runtime_checkable
class DataStore(Protocol):
    """Common lifecycle + health contract for every datastore client."""

    name: str

    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def health_check(self) -> DataStoreStatus: ...
