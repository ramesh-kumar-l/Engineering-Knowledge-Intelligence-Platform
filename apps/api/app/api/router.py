"""Top-level API router — aggregates all route modules.

New layers (connectors, retrieval, assistant, …) register their routers here as the
roadmap phases land.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter()
api_router.include_router(health.router)
