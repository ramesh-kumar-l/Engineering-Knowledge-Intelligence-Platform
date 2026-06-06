"""Agent API schemas (mirrored in packages/contracts) — Phase 8.

``ResultBody`` is the shape written by ``app/agents/serialize.py`` into
``AgentRun.result_json``, so it is validated directly on read for both the run response
and the Audit Trail / Execution Viewer.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.agents.catalog import AgentInfo
from app.domain.enums import (
    AgentStepStatus,
    AgentType,
    ConfidenceBand,
    FreshnessBand,
    RiskBand,
    SourceType,
    SyncStatus,
)
from app.models.agent import AgentRun, AgentStep


class AgentTypeInfo(BaseModel):
    type: AgentType
    label: str
    description: str
    needs_target: bool
    target_hint: str

    @classmethod
    def of(cls, info: AgentInfo) -> AgentTypeInfo:
        return cls(
            type=info.type,
            label=info.label,
            description=info.description,
            needs_target=info.needs_target,
            target_hint=info.target_hint,
        )


class AgentCatalogResponse(BaseModel):
    agents: list[AgentTypeInfo]


class RunAgentRequest(BaseModel):
    agent_type: AgentType
    target: str | None = Field(default=None, max_length=512)


class EvidenceOut(BaseModel):
    document_id: uuid.UUID
    title: str
    source_type: SourceType
    url: str | None
    snippet: str
    confidence: float
    confidence_band: ConfidenceBand
    freshness_band: FreshnessBand
    age_days: float | None
    owners: list[str]
    ownership_known: bool


class FindingOut(BaseModel):
    label: str
    detail: str
    severity: RiskBand | None
    refs: list[str]


class ActionOut(BaseModel):
    action: str
    priority: RiskBand
    rationale: str


class ResultBody(BaseModel):
    headline: str
    confidence: float
    confidence_band: ConfidenceBand
    findings: list[FindingOut]
    actions: list[ActionOut]
    evidence: list[EvidenceOut]


class StepOut(BaseModel):
    ordinal: int
    name: str
    status: AgentStepStatus
    summary: str
    detail: dict[str, Any] | None

    @classmethod
    def from_model(cls, step: AgentStep) -> StepOut:
        return cls(
            ordinal=step.ordinal,
            name=step.name,
            status=step.status,
            summary=step.summary,
            detail=step.detail_json,
        )


class AgentRunOut(BaseModel):
    id: uuid.UUID
    agent_type: AgentType
    target: str | None
    title: str
    status: SyncStatus
    confidence: float | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    step_count: int

    @classmethod
    def from_model(cls, run: AgentRun, step_count: int) -> AgentRunOut:
        return cls(
            id=run.id,
            agent_type=run.agent_type,
            target=run.target,
            title=run.title,
            status=run.status,
            confidence=run.confidence,
            created_by=run.created_by,
            created_at=run.created_at,
            updated_at=run.updated_at,
            step_count=step_count,
        )


class AgentRunListResponse(BaseModel):
    runs: list[AgentRunOut]


class AgentRunDetailResponse(BaseModel):
    run: AgentRunOut
    result: ResultBody | None
    steps: list[StepOut]

    @classmethod
    def of(cls, run: AgentRun, steps: list[AgentStep]) -> AgentRunDetailResponse:
        return cls(
            run=AgentRunOut.from_model(run, len(steps)),
            result=(
                ResultBody.model_validate(run.result_json)
                if run.result_json is not None
                else None
            ),
            steps=[StepOut.from_model(s) for s in steps],
        )
