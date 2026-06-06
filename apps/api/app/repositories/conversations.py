"""Conversation + message persistence (tenant-scoped) — Phase 6.

Backs Conversation History (list + detail) and the assistant's own writes. Every
query is filtered by ``tenant_id`` so conversations never leak across tenants.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import _now
from app.models.conversation import Conversation, Message


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, conversation: Conversation) -> Conversation:
        self._session.add(conversation)
        await self._session.flush()
        return conversation

    async def add_message(self, message: Message) -> Message:
        self._session.add(message)
        await self._session.flush()
        return message

    async def touch(self, conversation: Conversation) -> None:
        """Bump the conversation's recency after appending messages."""
        conversation.updated_at = _now()
        await self._session.flush()

    async def get(
        self, tenant_id: str, conversation_id: uuid.UUID
    ) -> Conversation | None:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.tenant_id == tenant_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_recent(
        self, tenant_id: str, limit: int = 50, offset: int = 0
    ) -> list[tuple[Conversation, int]]:
        """Conversations (most recent first) with their message counts."""
        message_count = func.count(Message.id)
        stmt = (
            select(Conversation, message_count)
            .outerjoin(Message, Message.conversation_id == Conversation.id)
            .where(Conversation.tenant_id == tenant_id)
            .group_by(Conversation.id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(row[0], int(row[1])) for row in rows]

    async def list_messages(
        self, tenant_id: str, conversation_id: uuid.UUID
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(
                Message.tenant_id == tenant_id,
                Message.conversation_id == conversation_id,
            )
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
