"""Shared route dependencies.

Exposes app-scoped singletons (datastores) to routes via FastAPI's dependency
injection, keeping route handlers free of global state.
"""

from __future__ import annotations

from fastapi import Request

from app.core.db import DataStores


def get_datastores(request: Request) -> DataStores:
    """Return the datastore registry created during app startup (lifespan)."""
    return request.app.state.datastores  # type: ignore[no-any-return]
