# Active Context

> Compressed "save state" for resuming work fast. Pairs with
> [`implementation_status.md`](implementation_status.md) (full status). Update before
> ending any major feature.

**Last updated:** 2026-06-06 (Phase 8)

## Where we are

Phase 8 — Agent Layer is **complete and verified**. **All roadmap phases (0–8) are now
delivered.** End-to-end: UI → API (JWT/RBAC, tenant-scoped) → Sync → documents →
Processing → chunks/enrichment → Graph build (Neo4j) and Embedding (Qdrant) → hybrid
Search → Trust scoring → Assistant (deterministic Q&A) → Intelligence (dependency /
debt / incident / ownership reports) → **Agents** (deterministic, fixed-plan agents that
compose all of the above and persist an auditable run + step trace + result snapshot).

## What just happened (this increment)

Built the agent layer in `app/agents/`: pure fixed-plan planners — `incident_agent`
(impact + resolution + owners), `onboarding_agent` (sources + owners + dependency
profile), `architecture_agent` (decisions + cycles + high-risk components + stale-doc
risk), `maintenance_agent` (corpus knowledge debt + orphans, no target) — plus `base.py`
(frozen `AgentReport`/`AgentFinding`/`AgentAction`/`AgentEvidence`/`AgentStepResult`),
`context.py` (`AgentContext` over retrieval + trust + graph + intelligence), `compose.py`
(trust-carrying evidence gathering, owner lookup, confidence aggregation), `catalog.py`,
`serialize.py`, and `agent_service.py` (dispatch → run → persist). New `AgentType` +
`AgentStepStatus` enums. Persistence: `AgentRun` + `AgentStep` (PostgreSQL) +
`AgentRepository`. APIs (`routes/agents.py`): `GET /agents/catalog`, `POST /agents/runs`
(audited), `GET /agents/runs`, `GET /agents/runs/{id}` (VIEWER, tenant-scoped). Three
screens: Agent Workspace, Agent Execution Viewer, Agent Audit Trail. TS contracts
(`agents.ts`). Added ADR-0021. **No new datastore, no model provider** — agents persist
their run/trace/result to PostgreSQL (the audit deliverable), composing the existing
layers deterministically.

Gates: API `ruff` clean · `mypy app` clean (138 files) · `pytest` **175/175**. Web
`lint` · `typecheck` · `build` all green (routes incl. /agents, /agents/[id],
/agents/audit).

## How to run it

```bash
docker compose -f infra/docker-compose.yml up -d          # PG + Neo4j + Qdrant
cd apps/api && uvicorn app.main:app --reload              # API on :8000 (auto-creates PG schema in dev)
cd apps/web && npm run dev                                # Web on :3000
```

Flow to exercise: add a GitHub connector → Run sync → Run processing → Build graph →
(curate `depends_on` edges) → embed (Search) → open **Agents** → run an agent (e.g.
Incident "checkout outage", or Knowledge Maintenance with no target) → review the
findings, prioritized actions, trust-carrying evidence and execution trace in the
Execution Viewer; the Audit Trail lists every run. Dev auth: web client sends
`X-Tenant-Id`/`X-Role` headers.

## Active decisions / constraints to remember

- Agents are **deterministic, fixed-plan and auditable** (ADR-0021): no model provider;
  they compose retrieval + graph + trust + intelligence and **persist** the run + step
  trace + result snapshot to PostgreSQL (no new datastore). Overall confidence = mean of
  cited trust, so **every result carries trust**. Planner failures are captured as a
  failed run (ADR-0009), never raised.
- Running an agent requires VIEWER and is audited (`agent.run`) — same call posture as the
  assistant (agents read knowledge; the run record is the user-scoped, reviewable
  artifact).
- The fixed plans + templated phrasing are the seam for an LLM-backed planner/tool-use
  upgrade behind `AgentService`; the persistence + audit contract stays the same. Runs are
  synchronous in-request (bounded) — no scheduling/triggers or worker yet.
- Keep files < 300 lines; one concern per file. Python schemas authoritative; TS
  `packages/contracts` mirror them.

## Next step

No further roadmap phases remain. Next investments are production-hardening items tracked
as debt (see [`implementation_status.md`](implementation_status.md) "Recommended next
action"): the remaining 5 connectors, Alembic migrations, OAuth/OIDC + SSO login UI, a
background worker for all run paths (incl. agents), and the LLM-backed upgrades behind
their existing seams. Each should be scoped + ADR'd before implementation. **STOP for
direction** before starting a hardening workstream.
