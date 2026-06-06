"""FastAPI application factory + lifespan wiring.

Composition root: builds settings, logging, datastore registry, middleware, and
routers. The modular monolith (system_architecture.md) is assembled here so each
concern stays independently testable.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.crypto import SecretBox
from app.core.db import DataStores
from app.core.logging import configure_logging
from app.middleware.audit import AuditLogMiddleware
from app.middleware.request_context import RequestContextMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Open datastore connections on startup; close them on shutdown."""
    settings: Settings = app.state.settings
    stores = DataStores(settings)
    app.state.datastores = stores
    await stores.connect()
    if settings.auto_create_schema:
        # Dev convenience: create ORM tables. Production manages schema via migrations.
        try:
            await stores.postgres.create_all()
        except Exception:  # noqa: BLE001 - DB may be unavailable; readiness reports it
            logging.getLogger("ekip").warning(
                "schema_bootstrap_skipped", extra={"extra": {"reason": "postgres unavailable"}}
            )
    logging.getLogger("ekip").info(
        "startup", extra={"extra": {"env": settings.env, "version": __version__}}
    )
    try:
        yield
    finally:
        await stores.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build a fully wired FastAPI app. Accepts injected settings for testing."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="EKIP API",
        version=__version__,
        description="Engineering Knowledge Intelligence Platform — backend API.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.secret_box = SecretBox(settings.secret_key)

    # Middleware order: outermost first. Correlation id wraps audit so audit logs
    # carry the request id.
    app.add_middleware(AuditLogMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
