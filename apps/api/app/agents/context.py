"""Shared execution context handed to every agent planner (Phase 8).

Bundles the lower layers an agent composes so the planners take a single argument and
stay free of FastAPI/DI wiring. Kept separate from ``base`` (pure value objects) so the
value objects carry no service dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.graph.store import GraphStore
from app.intelligence.intelligence_service import IntelligenceService
from app.retrieval.search_service import SearchService
from app.trust.trust_service import TrustService


@dataclass(frozen=True)
class AgentContext:
    """The tenant scope + composed layers available to an agent."""

    tenant_id: str
    search: SearchService
    trust: TrustService
    graph: GraphStore
    intelligence: IntelligenceService
