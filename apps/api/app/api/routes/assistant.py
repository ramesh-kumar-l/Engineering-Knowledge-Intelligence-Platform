"""Engineering Assistant endpoints (api_catalog.md, Phase 6).

Deterministic Q&A over retrieval + graph + trust (ADR-0019); every answer carries
Phase-5 trust. Asking persists a conversation + messages (Conversation History) and
the answer's evidence snapshot (Evidence Viewer). All routes are tenant-scoped via
``Principal``; asking requires VIEWER (it reads knowledge — the conversation record is
a user-scoped convenience) and is audited.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_assistant_service, get_audit_service
from app.assistant.assistant_service import AssistantService
from app.core.security import Principal, Role, require_role
from app.domain.assistant import (
    AskRequest,
    AskResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationOut,
    MessageOut,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/ask", response_model=AskResponse)
async def ask(
    payload: AskRequest,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: AssistantService = Depends(get_assistant_service),
    audit: AuditService = Depends(get_audit_service),
) -> AskResponse:
    conversation, message = await service.ask(
        principal.tenant_id,
        principal.subject,
        payload.question,
        payload.conversation_id,
    )
    await audit.record(
        tenant_id=principal.tenant_id,
        actor=principal.subject,
        action="assistant.ask",
        resource_type="conversation",
        resource_id=str(conversation.id),
        metadata={"intent": message.intent.value if message.intent else None},
    )
    return AskResponse.from_message(conversation, message)


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: AssistantService = Depends(get_assistant_service),
) -> ConversationListResponse:
    rows = await service.list_conversations(principal.tenant_id, limit, offset)
    return ConversationListResponse(
        conversations=[ConversationOut.from_model(c, n) for c, n in rows]
    )


@router.get(
    "/conversations/{conversation_id}", response_model=ConversationDetailResponse
)
async def get_conversation(
    conversation_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: AssistantService = Depends(get_assistant_service),
) -> ConversationDetailResponse:
    result = await service.get_conversation(principal.tenant_id, conversation_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    conversation, messages = result
    return ConversationDetailResponse(
        conversation=ConversationOut.from_model(conversation, len(messages)),
        messages=[MessageOut.from_model(m) for m in messages],
    )
