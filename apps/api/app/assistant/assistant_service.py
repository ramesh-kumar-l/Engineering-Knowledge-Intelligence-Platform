"""Engineering Assistant engine (Phase 6, ADR-0019).

Answers an engineering question deterministically by composing the existing layers:
hybrid retrieval (Phase 4) for evidence, the knowledge graph (Phase 3) for related
facts, and the trust layer (Phase 5) so every cited source carries confidence,
freshness and ownership. No model provider. Each exchange is persisted as a
conversation + messages for history and evidence review.
"""

from __future__ import annotations

import uuid

from app.assistant import composer, serialize
from app.assistant import intent as intent_mod
from app.assistant.base import AnswerEntity, Citation, OwnerRef, RelatedFact
from app.domain.enums import MessageRole
from app.graph.store import GraphStore
from app.models.conversation import Conversation, Message
from app.repositories.conversations import ConversationRepository
from app.retrieval.base import ChunkHit, EntityHit
from app.retrieval.search_service import SearchService
from app.trust.base import TrustProfile
from app.trust.trust_service import TrustService

_MAX_CITATIONS = 6
_MAX_RELATIONS = 6
_TITLE_CHARS = 80


class AssistantService:
    def __init__(
        self,
        search_service: SearchService,
        trust_service: TrustService,
        graph_store: GraphStore,
        conversations: ConversationRepository,
    ) -> None:
        self._search = search_service
        self._trust = trust_service
        self._graph = graph_store
        self._conversations = conversations

    async def ask(
        self,
        tenant_id: str,
        actor: str,
        question: str,
        conversation_id: uuid.UUID | None = None,
    ) -> tuple[Conversation, Message]:
        """Answer a question and persist the exchange; returns the assistant message."""
        question = question.strip()
        intent = intent_mod.classify(question)
        result = await self._search.search(tenant_id, question, "hybrid", _MAX_CITATIONS)
        citations = await self._citations(tenant_id, result.chunks)
        entities = [
            AnswerEntity(key=e.key, kind=e.kind, name=e.name, summary=e.summary)
            for e in result.entities
        ]
        focus_name, relations = await self._related(tenant_id, result.entities)
        answer = composer.compose(
            intent, question, citations, entities, relations, focus_name
        )

        conversation = await self._conversation(
            tenant_id, actor, question, conversation_id
        )
        await self._conversations.add_message(
            Message(
                conversation_id=conversation.id,
                tenant_id=tenant_id,
                role=MessageRole.USER,
                content=question,
            )
        )
        assistant_message = await self._conversations.add_message(
            Message(
                conversation_id=conversation.id,
                tenant_id=tenant_id,
                role=MessageRole.ASSISTANT,
                content=answer.summary,
                intent=answer.intent,
                confidence=answer.confidence,
                answer_json=serialize.to_dict(answer),
            )
        )
        await self._conversations.touch(conversation)
        return conversation, assistant_message

    async def list_conversations(
        self, tenant_id: str, limit: int = 50, offset: int = 0
    ) -> list[tuple[Conversation, int]]:
        return await self._conversations.list_recent(tenant_id, limit, offset)

    async def get_conversation(
        self, tenant_id: str, conversation_id: uuid.UUID
    ) -> tuple[Conversation, list[Message]] | None:
        conversation = await self._conversations.get(tenant_id, conversation_id)
        if conversation is None:
            return None
        messages = await self._conversations.list_messages(tenant_id, conversation_id)
        return conversation, messages

    async def _conversation(
        self,
        tenant_id: str,
        actor: str,
        question: str,
        conversation_id: uuid.UUID | None,
    ) -> Conversation:
        if conversation_id is not None:
            existing = await self._conversations.get(tenant_id, conversation_id)
            if existing is not None:
                return existing
        return await self._conversations.create(
            Conversation(
                tenant_id=tenant_id, title=_title(question), created_by=actor
            )
        )

    async def _citations(
        self, tenant_id: str, chunks: list[ChunkHit]
    ) -> list[Citation]:
        """Build a citation per chunk hit, carrying its document's Phase-5 trust.

        Trust profiles are fetched once per document (chunks from the same document
        share one profile), so this stays cheap for the handful of cited chunks.
        """
        profiles: dict[uuid.UUID, TrustProfile | None] = {}
        citations: list[Citation] = []
        for hit in chunks:
            if hit.document_id not in profiles:
                profiles[hit.document_id] = await self._trust.profile(
                    tenant_id, hit.document_id
                )
            profile = profiles[hit.document_id]
            if profile is None:
                continue
            citations.append(
                Citation(
                    document_id=hit.document_id,
                    title=hit.title,
                    source_type=profile.source.source_type,
                    url=hit.url,
                    chunk_id=hit.chunk_id,
                    ordinal=hit.ordinal,
                    snippet=hit.snippet,
                    confidence=profile.confidence,
                    confidence_band=profile.confidence_band,
                    freshness_band=profile.freshness_band,
                    age_days=profile.age_days,
                    owners=[OwnerRef(key=o.key, name=o.name) for o in profile.owners],
                    ownership_known=profile.ownership_known,
                )
            )
        return citations

    async def _related(
        self, tenant_id: str, entities: list[EntityHit]
    ) -> tuple[str | None, list[RelatedFact]]:
        """Neighborhood facts for the single most relevant matched entity (bounded)."""
        if not entities:
            return None, []
        focus = entities[0]
        neighborhood = await self._graph.neighborhood(tenant_id, focus.key)
        if neighborhood is None:
            return focus.name, []
        relations = [
            RelatedFact(
                relation=neighbor.type,
                direction=neighbor.direction,
                kind=neighbor.entity.kind,
                name=neighbor.entity.name,
                key=neighbor.entity.key,
            )
            for neighbor in neighborhood.neighbors
        ][:_MAX_RELATIONS]
        return focus.name, relations


def _title(question: str) -> str:
    text = " ".join(question.split())
    if not text:
        return "New conversation"
    return text[:_TITLE_CHARS] + ("…" if len(text) > _TITLE_CHARS else "")
