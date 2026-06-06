"""Top-level API router — aggregates all route modules.

New layers (connectors, retrieval, assistant, …) register their routers here as the
roadmap phases land.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    connectors,
    documents,
    graph,
    graph_entities,
    health,
    processing,
    sync,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(connectors.router)
api_router.include_router(sync.router)
api_router.include_router(documents.router)
api_router.include_router(processing.router)
api_router.include_router(graph.router)
api_router.include_router(graph_entities.router)
