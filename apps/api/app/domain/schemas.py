"""API response schemas (the typed contract shared with the web app).

These mirror the TypeScript types in ``packages/contracts`` (see testing_strategy.md
R2 mitigation: contract parity between Python and TypeScript).
"""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness response — the process is up. No dependency checks."""

    status: str = "ok"
    version: str


class DependencyStatus(BaseModel):
    """Readiness detail for a single datastore dependency."""

    name: str
    healthy: bool
    detail: str | None = None


class ReadinessResponse(BaseModel):
    """Readiness response — the process AND its datastore dependencies."""

    status: str  # "ready" | "degraded"
    version: str
    dependencies: list[DependencyStatus]
