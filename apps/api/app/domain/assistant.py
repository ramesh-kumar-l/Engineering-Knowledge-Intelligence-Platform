"""Assistant API schemas (mirrored in packages/contracts) — Phase 6.

The persisted answer snapshot (``Message.answer_json``) is written by
``app/assistant/serialize.py`` to exactly this ``AnswerBody`` shape, so it is
validated directly on read for both the ask response and Conversation History.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import (
    AssistantIntent,
    ConfidenceBand,
    EntityKind,
    FreshnessBand,
    MessageRole,
    RelationshipType,
    SourceType,
)
from app.models.conversation import Conversation, Message


class OwnerRefOut(BaseModel):
    key: str
    name: str


class CitationOut(BaseModel):
    document_id: uuid.UUID
    title: str
    source_type: SourceType
    url: str | None
    chunk_id: uuid.UUID | None
    ordinal: int | None
    snippet: str
    confidence: float
    confidence_band: ConfidenceBand
    freshness_band: FreshnessBand
    age_days: float | None
    owners: list[OwnerRefOut]
    ownership_known: bool


class AnswerEntityOut(BaseModel):
    key: str
    kind: EntityKind
    name: str
    summary: str | None


class RelatedFactOut(BaseModel):
    relation: RelationshipType
    direction: str
    kind: EntityKind
    name: str
    key: str


class AnswerBody(BaseModel):
    intent: AssistantIntent
    summary: str
    key_points: list[str]
    confidence: float
    confidence_band: ConfidenceBand
    citations: list[CitationOut]
    entities: list[AnswerEntityOut]
    relations: list[RelatedFactOut]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    conversation_id: uuid.UUID | None = None


class MessageOut(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime
    answer: AnswerBody | None

    @classmethod
    def from_model(cls, message: Message) -> MessageOut:
        return cls(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
            answer=(
                AnswerBody.model_validate(message.answer_json)
                if message.answer_json is not None
                else None
            ),
        )


class AskResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    answer: AnswerBody

    @classmethod
    def from_message(
        cls, conversation: Conversation, message: Message
    ) -> AskResponse:
        # An assistant message always carries an answer snapshot.
        assert message.answer_json is not None
        return cls(
            conversation_id=conversation.id,
            message_id=message.id,
            answer=AnswerBody.model_validate(message.answer_json),
        )


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int

    @classmethod
    def from_model(
        cls, conversation: Conversation, message_count: int
    ) -> ConversationOut:
        return cls(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=message_count,
        )


class ConversationListResponse(BaseModel):
    conversations: list[ConversationOut]


class ConversationDetailResponse(BaseModel):
    conversation: ConversationOut
    messages: list[MessageOut]
