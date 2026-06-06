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

## Phase 1 — Knowledge Ingestion Layer ✅

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

**🚦 Phase gate — approved; Phase 2 delivered below.**

---

## Phase 2 — Knowledge Processing Layer ✅

Capabilities: parsing, chunking, classification, enrichment, summarization.
UI: Processing Dashboard, Chunk Statistics, Parsing Explorer, Processing Jobs.

Delivered:
- ✅ **Pipeline** — deterministic, dependency-light steps in `app/processing/`
  (parser, chunker, classifier, enricher, summarizer) composed by `pipeline.process`;
  pluggable for an LLM-backed upgrade (ADR-0010).
- ✅ **Persistence** — `ProcessingRun`/`ProcessingEvent`, 1:1 `DocumentEnrichment`,
  and `Chunk` (PostgreSQL; vectorization deferred to Retrieval, ADR-0011). Reprocessing
  is driven by `source_content_hash` staleness.
- ✅ **Processing engine** — `ProcessingService` selects pending/stale/failed docs,
  runs the pipeline per document, replaces chunks, upserts enrichment, records
  counters + events; per-document failures isolated, run failure captured (ADR-0009).
- ✅ **APIs** — trigger/list/get processing runs + events, chunk stats, processed-doc
  list + per-document detail (api_catalog.md); RBAC-enforced + tenant-scoped.
- ✅ **UI** — Processing Dashboard, Processing Jobs, Chunk Statistics, Parsing Explorer
  (server components + a run server action).
- ✅ **Tests** — 50 passing (pipeline units, service idempotency/reprocessing,
  routes/RBAC/stats/tenant); ruff · mypy strict · pytest green; web lint/typecheck/build.

Deferred to later (tracked in implementation_status.md): LLM-backed classification/
summarization, embedding chunks into Qdrant (Retrieval), background processing worker,
richer per-source parsers, language detection beyond a coarse heuristic.

**🚦 Phase gate — approved; Phase 3 delivered below.**

---

## Phase 3 — Knowledge Graph Layer ✅

Entities: Engineer, Team, Repository, Service, API, Incident, ADR, Document.
Relationships: owns, depends_on, modified, impacts, resolved.
UI: Knowledge Explorer, Service Explorer, Team Explorer, Dependency Graph.

Delivered:
- ✅ **Graph store (Neo4j)** — ``GraphStore`` protocol with a Cypher-backed
  ``Neo4jGraphStore`` (single ``:Entity`` label + typed edges, tenant-scoped uniqueness)
  and an ``InMemoryGraphStore`` for offline tests (ADR-0012). Neo4j is now in use.
- ✅ **Deterministic projection** — ``app/graph/builder.py`` derives Repository/Team/
  Engineer/Document/Incident/ADR entities and owns/modified/impacts/resolved edges from
  connectors + documents + enrichment; idempotent upserts (ADR-0013).
- ✅ **Curation** — editor-only ``POST /graph/entities`` + ``/graph/relationships``
  declare Services/APIs and ``depends_on`` edges (audited), auto-creating endpoints.
- ✅ **Build engine** — ``GraphService.build`` projects synchronously and records a
  ``GraphBuildRun`` + events (ADR-0009); failures captured, not raised.
- ✅ **APIs** — build/stats/runs/events + entities/entity-neighborhood/relationships +
  curation (api_catalog.md); RBAC-enforced + tenant-scoped.
- ✅ **UI** — Knowledge Explorer, Entity Detail, Service Explorer, Team Explorer,
  Dependency Graph (+ add-dependency form), Graph Build Jobs.
- ✅ **Tests** — 71 passing (builder projection, in-memory store, build/curation service,
  routes/RBAC/tenant/404); ruff · mypy strict (81 files) · pytest green; web
  lint/typecheck/build green.

Deferred to later (tracked in implementation_status.md): LLM/NER entity extraction for
richer auto-derived edges (incl. auto ``depends_on``), graph-backed retrieval (Phase 4),
a background build worker, and Neo4j RS-level migrations/indices beyond the key
constraint.

**🚦 Phase gate — approved; Phase 4 delivered below.**

---

## Phase 4 — Retrieval Layer ✅

Capabilities: keyword retrieval, vector retrieval, graph retrieval, hybrid ranking.
UI: Global Search, Advanced Search, Search Explorer.

Delivered:
- ✅ **Embeddings** — a deterministic ``HashingEmbedder`` behind an ``Embedder`` protocol
  (signed feature hashing → unit vectors; no model provider, offline; ADR-0014).
- ✅ **Vector store** — ``VectorStore`` protocol with a ``QdrantVectorStore`` (one
  collection, tenant_id payload filter) and an ``InMemoryVectorStore`` for offline tests
  (ADR-0015). Qdrant is now in use.
- ✅ **Embedding engine** — ``EmbeddingService`` embeds processed chunks synchronously
  (ADR-0009), recording an ``EmbeddingRun``/``Event`` + a per-document staleness ledger
  (``DocumentEmbeddingState``) so re-runs embed only changed documents.
- ✅ **Hybrid search** — keyword (portable ``LIKE`` candidates, deterministic ranking) +
  vector retrieval fused by reciprocal rank (ADR-0016), plus a knowledge-graph entity
  facet; ``mode`` = keyword/vector/hybrid.
- ✅ **APIs** — `POST /embeddings/runs`, embedding stats/runs/events, `GET /search`
  (api_catalog.md); RBAC-enforced + tenant-scoped; embedding runs audited.
- ✅ **UI** — Global Search, Advanced Search, Search Explorer (index stats + embed action
  + recent runs), Embedding Jobs (run detail + logs). "Search" enabled in nav.
- ✅ **Tests** — 98 passing (embedder, fusion, keyword, in-memory vector store, embedding
  service staleness/force, hybrid search, search/embedding routes RBAC/404/tenant);
  ruff · mypy strict (96 files) · pytest green; web lint/typecheck/build green.

Deferred to later (tracked in implementation_status.md): model-backed embeddings, a
background embedding worker, PostgreSQL full-text (``tsvector``/GIN) for keyword recall at
scale, learned/weighted hybrid ranking, and re-ranking.

**🚦 Phase gate — approved; Phase 5 delivered below.**

---

## Phase 5 — Trust Layer ✅

Capabilities: confidence scoring, freshness tracking, source attribution, ownership
validation.
UI: Trust Inspector, Source Explorer, Freshness Dashboard.

Delivered:
- ✅ **Deterministic scoring** — pure ``app/trust/scoring.py``: age-based freshness
  (score + band), a five-signal weighted confidence (freshness, ownership, processed,
  embedded, richness) with a per-signal contribution breakdown, and confidence bands.
  No models; computed **on read**, nothing persisted (ADR-0017).
- ✅ **Trust read model** — ``TrustRepository`` joins each document to its processing
  (``DocumentEnrichment``) and embedding (``DocumentEmbeddingState``) state in one
  tenant-scoped query; outer joins keep coverage gaps visible (lower confidence).
- ✅ **Ownership from the graph** — owners are engineers with a ``modified`` edge into a
  document node, read from the ``GraphStore``; absence is reported as *ownership
  unknown*, never guessed (ADR-0018).
- ✅ **Trust engine** — ``TrustService`` assembles a per-document profile (confidence,
  freshness, source provenance, owners, supporting excerpts), a Source Explorer list,
  and a corpus Freshness summary.
- ✅ **APIs** — `GET /trust/documents/{id}`, `/trust/sources`, `/trust/freshness`
  (api_catalog.md); RBAC-enforced + tenant-scoped; read-only (no trigger).
- ✅ **UI** — Trust Inspector (why-this-score breakdown, source, owners, evidence),
  Source Explorer (provenance + trust bands), Freshness Dashboard (distribution +
  needs-attention). "Trust" enabled in nav.
- ✅ **Tests** — 114 passing (+16: pure scoring, service profile/sources/freshness +
  tenant isolation, routes RBAC/404/422); ruff · mypy strict (103 files) · pytest
  green; web lint/typecheck/build green.

Deferred to later (tracked in implementation_status.md): learned/calibrated confidence
weights, a cached/materialized trust read model for large corpora, richer ownership
(CODEOWNERS / team-of-repo inheritance), and trust observability metrics over time.

**🚦 Phase gate — approved; Phase 6 delivered below.**

---

## Phase 6 — Engineering Assistant ✅

Capabilities: service understanding, ownership discovery, incident exploration,
architecture explanations.
UI: Assistant Workspace, Conversation History, Evidence Viewer.

Delivered:
- ✅ **Deterministic engine** — ``app/assistant/`` composes existing layers, no model
  provider (ADR-0019): ``intent.py`` (ordered keyword classification into SERVICE/
  OWNERSHIP/INCIDENT/ARCHITECTURE/GENERAL), ``composer.py`` (extractive, templated
  answer assembly), ``serialize.py`` (answer→JSON snapshot). All pure/offline-testable.
- ✅ **Orchestration** — ``AssistantService`` classifies → hybrid-retrieves (Phase 4) →
  attaches Phase-5 trust to every cited document → enriches with one bounded graph
  neighborhood (Phase 3) → composes. Overall answer confidence is the mean of the cited
  documents' trust, so **every answer carries trust**.
- ✅ **Persistence** — ``Conversation`` + ``Message`` (PostgreSQL); an assistant message
  stores a JSON answer snapshot (summary, citations-with-trust, related facts) faithful
  to generation time. ``ConversationRepository`` is tenant-scoped.
- ✅ **APIs** — `POST /assistant/ask` (VIEWER, audited), `GET /assistant/conversations`,
  `GET /assistant/conversations/{id}` (api_catalog.md); tenant-scoped.
- ✅ **UI** — Assistant Workspace (ask + recent), conversation thread (answers with trust
  + follow-ups), Conversation History, Evidence Viewer (all cited sources ranked by
  trust, linked to the Trust Inspector). "Assistant" enabled in nav.
- ✅ **Tests** — **138 passing** (+24: intent, composer, service ask/continue/list/tenant,
  routes RBAC/round-trip/404/422); ruff · mypy strict (113 files) · pytest green; web
  lint/tsc/build green.

Deferred to later (tracked in implementation_status.md): LLM-backed answer synthesis +
intent classification behind the same seams, multi-hop graph reasoning (enrichment is
bounded to one neighborhood), streaming responses, conversation rename/delete, and
relevance/answer-quality evaluation harness.

**🚦 Phase gate — approved; Phase 7 delivered below.**

---

## Phase 7 — Engineering Intelligence ✅

Capabilities: dependency intelligence, technical debt intelligence, incident
intelligence, ownership intelligence.
UI: Intelligence Dashboard, Technical Debt Dashboard, Dependency Risk Dashboard.

Delivered:
- ✅ **Deterministic engine** — ``app/intelligence/`` composes the graph (Phase 3) and
  trust (Phase 5), no model provider and no new datastore (ADR-0020); one pure module per
  concern: ``dependency`` (fan-in/out, blast-radius risk, Tarjan-SCC cycle detection),
  ``debt`` (severity over low-confidence/stale/unowned trust items), ``incident`` (impact
  + resolution), ``ownership`` (coverage, orphans, key-person load), plus a shared
  ``scoring`` helper. All pure/offline-testable; risk/severity banded by ``RiskBand``.
- ✅ **Orchestration** — ``IntelligenceService`` fetches bounded graph relationships/
  entities + the trust source list and delegates to the analyzers; ``overview`` runs all
  four and returns headline metrics. Everything is computed on read (nothing persisted).
- ✅ **APIs** — `GET /intelligence/overview`, `/dependencies`, `/debt`, `/incidents`,
  `/ownership` (api_catalog.md); VIEWER, tenant-scoped, read-only (no trigger).
- ✅ **UI** — Intelligence Dashboard (headline metrics + incidents + ownership coverage/
  orphans), Dependency Risk Dashboard (risk-ranked components + cycles), Technical Debt
  Dashboard (severity-ranked debt + reason breakdown, linked to the Trust Inspector).
  "Intelligence" enabled in nav.
- ✅ **Tests** — **160 passing** (+22: dependency/debt/incident/ownership analyzers,
  service over SQLite + in-memory graph, routes RBAC/shape/tenant); ruff · mypy strict
  (123 files) · pytest green; web lint/tsc/build green.

Deferred to later (tracked in implementation_status.md): learned/calibrated risk +
severity weights, a cached/materialized intelligence read model for large corpora,
multi-hop dependency reasoning and trend/time-series intelligence, and richer ownership
inputs (CODEOWNERS / team inheritance, carried from ADR-0018).

**🚦 Phase gate — awaiting approval to proceed to Phase 8.**

---

## Phase 8 — Agent Layer ⬜

Capabilities: incident agents, onboarding agents, architecture agents, knowledge
maintenance agents.
UI: Agent Workspace, Agent Execution Viewer, Agent Audit Trail.

**STOP — wait for approval.**

---

See [`implementation_status.md`](implementation_status.md) for the live state and
[`screen_inventory.md`](screen_inventory.md) for per-phase screens.
