"""Search endpoint (api_catalog.md, Phase 4).

Hybrid retrieval over embedded chunks + the knowledge graph. Read-only and
tenant-scoped via ``Principal``; ``mode`` selects keyword/vector/hybrid ranking.
"""

from __future__ import annotations

from typing import get_args

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_search_service
from app.core.security import Principal, Role, require_role
from app.domain.search import SearchMode, SearchResponse
from app.retrieval.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(min_length=1, max_length=512),
    mode: SearchMode = Query(default="hybrid"),
    limit: int = Query(default=10, ge=1, le=50),
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    if mode not in get_args(SearchMode):  # defensive; FastAPI already validates
        mode = "hybrid"
    result = await service.search(principal.tenant_id, q, mode, limit)
    return SearchResponse.from_result(result)
