# Delivery Roadmap

Phases are **sequential and must not be skipped or reordered**. Each phase delivers a
usable product increment (backend + APIs + UI + observability + tests + docs) and ends
at a **phase gate**: STOP and wait for explicit user approval before continuing.

Legend: ✅ done · 🟡 in progress · ⬜ not started

---

## Phase 0 — Project Foundation ✅

Deliver: repository structure, memory bank, ADR framework, coding standards, CI/CD,
security baseline, design system.

Increments:
- ✅ **Docs increment** — memory bank + foundational ADRs + standards (this set).
- ✅ **Code walking-skeleton** — monorepo, FastAPI health/readiness, Next.js
  App Shell + Overview, docker-compose, CI, security scaffolding. All gates green.

**🚦 Phase gate — approved; Phase 1 delivered below.**

---

## Phase 1 — Knowledge Ingestion Layer 🟡

Sources: GitHub, GitLab, Jira, Confluence, Slack, Notion.
Capabilities: incremental sync, metadata extraction, change tracking.
UI: Connector Catalog, Connector Details, Sync Dashboard, Sync Logs.

Delivered:
- ✅ **Persistence** — PostgreSQL ORM (Connector, SyncRun, SyncEvent, Document,
  AuditEvent), tenant-scoped, async session layer.
- ✅ **Connector framework** — `Connector` protocol, 6-source catalog, registry;
  **GitHub connector** with incremental fetch (cursor/`since`). Remaining 5 sources
  registered as catalog entries (planned).
- ✅ **Sync engine** — content-hash change tracking (created/updated/unchanged/
  deleted), counters, log events, cursor advancement, failure capture (ADR-0009).
- ✅ **APIs** — connector catalog/CRUD/trigger-sync, sync runs/events, documents
  (api_catalog.md); RBAC-enforced + tenant-scoped.
- ✅ **Security** — JWT bearer auth as the production boundary, dev header fallback
  gated to non-prod; connector secrets encrypted at rest; **PostgreSQL-backed audit
  events** (ADR-0008).
- ✅ **UI** — Connector Catalog, Connector Details, Sync Dashboard, Sync Logs
  (server components + server actions).
- ✅ **Tests** — 30 passing (repos/sync/services/routes/auth/connector/crypto);
  ruff · mypy strict · pytest green; web lint/typecheck/build green.

Deferred to later (tracked in implementation_status.md): connectors for the other 5
sources, a durable background sync worker/queue, Alembic migrations, JWKS/SSO login UI.

**🚦 Phase gate — awaiting approval to proceed to Phase 2.**

---

## Phase 2 — Knowledge Processing Layer ⬜

Capabilities: parsing, chunking, classification, enrichment, summarization.
UI: Processing Dashboard, Chunk Statistics, Parsing Explorer, Processing Jobs.

**STOP — wait for approval.**

---

## Phase 3 — Knowledge Graph Layer ⬜

Entities: Engineer, Team, Repository, Service, API, Incident, ADR, Document.
Relationships: owns, depends_on, modified, impacts, resolved.
UI: Knowledge Explorer, Service Explorer, Team Explorer, Dependency Graph.

**STOP — wait for approval.**

---

## Phase 4 — Retrieval Layer ⬜

Capabilities: keyword retrieval, vector retrieval, graph retrieval, hybrid ranking.
UI: Global Search, Advanced Search, Search Explorer.

**STOP — wait for approval.**

---

## Phase 5 — Trust Layer ⬜

Capabilities: confidence scoring, freshness tracking, source attribution, ownership
validation.
UI: Trust Inspector, Source Explorer, Freshness Dashboard.

**STOP — wait for approval.**

---

## Phase 6 — Engineering Assistant ⬜

Capabilities: service understanding, ownership discovery, incident exploration,
architecture explanations.
UI: Assistant Workspace, Conversation History, Evidence Viewer.

**STOP — wait for approval.**

---

## Phase 7 — Engineering Intelligence ⬜

Capabilities: dependency intelligence, technical debt intelligence, incident
intelligence, ownership intelligence.
UI: Intelligence Dashboard, Technical Debt Dashboard, Dependency Risk Dashboard.

**STOP — wait for approval.**

---

## Phase 8 — Agent Layer ⬜

Capabilities: incident agents, onboarding agents, architecture agents, knowledge
maintenance agents.
UI: Agent Workspace, Agent Execution Viewer, Agent Audit Trail.

**STOP — wait for approval.**

---

See [`implementation_status.md`](implementation_status.md) for the live state and
[`screen_inventory.md`](screen_inventory.md) for per-phase screens.
