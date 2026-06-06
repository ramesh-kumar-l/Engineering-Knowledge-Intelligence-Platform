# Implementation Status

> **Read this first.** Live state of the project. Updated after every task.

**Last updated:** 2026-06-06 (Phase 7)

## Current phase

**Phase 7 — Engineering Intelligence.** Complete and verified; **at the phase gate**
awaiting approval to start Phase 8. Phases 0–6 are done.

## Completed work

### Phase 0 — Project Foundation ✅
Memory bank + ADRs (0001–0007); code walking-skeleton (FastAPI health/readiness over
PG/Neo4j/Qdrant, Next.js dark App Shell + Overview, shared contracts, docker-compose,
CI, security scaffolding). All gates green.

### Phase 1 — Knowledge Ingestion Layer ✅
Connectors + catalog/registry (GitHub implemented; 5 planned), incremental sync with
content-hash change tracking, connector/sync/document APIs, JWT auth + Fernet secret
encryption + persisted audit (ADR-0008/0009), and the four ingestion screens.

### Phase 2 — Knowledge Processing Layer ✅

- **Processing pipeline (`app/processing/`):** pure, deterministic steps — `parser`
  (markdown/HTML → clean text + links), `chunker` (overlapping word-boundary windows
  + token estimates), `classifier` (label/keyword heuristic → category), `enricher`
  (keywords, counts, coarse language), `summarizer` (frequency-based extractive) — and
  `pipeline.process` composing them. No I/O, no external models (ADR-0010); each step
  is a replaceable seam for an LLM-backed upgrade. Shared `text` primitives.
- **Persistence:** `ProcessingRun` + `ProcessingEvent` (`app/models/processing.py`),
  1:1 `DocumentEnrichment` (`app/models/enrichment.py`), and `Chunk`
  (`app/models/chunk.py`). Chunks live in PostgreSQL; Qdrant vectorization is deferred
  to Retrieval (ADR-0011). `source_content_hash` drives staleness/reprocessing.
- **Repositories:** `ProcessingRepository`, `EnrichmentRepository` (incl. aggregates
  + joined explorer list), `ChunkRepository` (replace-for-document, stats);
  `DocumentRepository.list_pending_processing` (left-join: new/stale/failed) and
  `get`.
- **Processing engine (`app/services/processing_service.py`):** selects documents
  needing (re)processing, runs the pipeline per document, replaces chunks, upserts
  enrichment, counts processed/chunks/failed + log events. Per-document failures are
  isolated (status=failed, retried next run); run failures captured (ADR-0009).
- **APIs (`app/api/routes/processing.py`):** trigger/list/get runs, run events, chunk
  stats, processed-document list, per-document processing detail — RBAC + tenant-scoped
  (api_catalog.md). Trigger writes an `AuditEvent`.
- **Web (`apps/web/app/processing`):** Processing Dashboard (stats + run action +
  recent jobs), Processing Jobs (run detail + logs), Chunk Statistics (totals +
  category distribution), Parsing Explorer (list + per-document parsed/chunked detail).
  "Processing" enabled in the sidebar.
- **Contracts (`packages/contracts`):** TS mirrors `processing.ts` + `chunks.ts`.
- **Tests:** 50 passing — pipeline units, service idempotency/reprocessing/skip-deleted
  (SQLite), processing routes (RBAC, stats, events, 404s, tenant isolation).

### Phase 3 — Knowledge Graph Layer ✅

- **Graph store (`app/graph/`):** `GraphStore` protocol (`store.py`) with an
  `InMemoryGraphStore` for offline tests and a Cypher-backed `Neo4jGraphStore`
  (`neo4j_store.py`) — single `:Entity` label + typed relationships, tenant-scoped
  uniqueness constraint (ADR-0012). `Neo4jStore` now exposes its driver.
- **Projection (`builder.py`):** pure, deterministic mapping of connectors + documents +
  enrichment → Repository/Team/Engineer/Document/Incident/ADR entities and owns/modified/
  impacts/resolved edges; idempotent upserts (ADR-0013).
- **Persistence:** `GraphBuildRun` + `GraphBuildEvent` (`app/models/graph.py`, reuse
  SyncStatus/SyncEventLevel); the graph itself lives in Neo4j.
- **Engine (`app/services/graph_service.py`):** `build` projects synchronously and records
  counters/events (ADR-0009); `create_entity`/`create_relationship` curate Services + APIs
  + `depends_on` (auto-creating endpoints). Read methods back the explorers.
- **APIs (`routes/graph.py` + `routes/graph_entities.py`):** build/stats/runs/events +
  entities/entity-neighborhood/relationships + curation — RBAC + tenant-scoped; builds and
  curation write `AuditEvent`s.
- **Web (`apps/web/app/graph`):** Knowledge Explorer, Entity Detail, Service Explorer,
  Team Explorer, Dependency Graph (+ add form), Graph Build Jobs. "Knowledge Graph" in nav.
- **Contracts:** TS mirror `graph.ts`.
- **Tests:** **71 passing** (+21 graph): builder projection, in-memory store, build/
  idempotency/curation service (SQLite + in-memory store), routes (RBAC, stats, curation,
  neighborhood, 404s, tenant isolation). Gates green: **ruff · mypy strict (81 files) ·
  pytest 71/71**; web **lint · tsc · build**.

### Phase 4 — Retrieval Layer ✅

- **Embeddings (`app/retrieval/embedder.py`):** `Embedder` protocol + deterministic
  `HashingEmbedder` (signed feature hashing into 256-dim unit vectors; no provider,
  offline; ADR-0014). Process-wide singleton.
- **Vector store (`app/retrieval/`):** `VectorStore` protocol (`vector_store.py`) with an
  `InMemoryVectorStore` for offline tests and a `QdrantVectorStore` (`qdrant_store.py`) —
  one `ekip_chunks` collection, mandatory `tenant_id` payload filter (ADR-0015). Qdrant is
  now in use; `QdrantStore` now exposes its client.
- **Pure retrieval modules:** `fusion.py` (reciprocal rank fusion), `keyword.py`
  (deterministic term scoring), `base.py` (frozen primitives).
- **Persistence:** `EmbeddingRun` + `EmbeddingEvent` + `DocumentEmbeddingState`
  (`app/models/embedding.py`, reuse SyncStatus/SyncEventLevel); vectors live in Qdrant.
- **Engines:** `EmbeddingService` embeds processed chunks synchronously, staleness-skips
  unchanged docs (ADR-0009/0016); `SearchService` runs keyword+vector+graph and fuses.
- **APIs (`routes/embeddings.py` + `routes/search.py`):** embedding run/stats/runs/events
  + `GET /search?q&mode&limit` — RBAC + tenant-scoped; embedding runs audited.
- **Web (`apps/web/app/search`):** Global Search, Advanced Search (mode toggle), Search
  Explorer (index stats + embed action + recent runs), Embedding Jobs. "Search" in nav.
- **Contracts:** TS mirrors `search.ts` + `embedding.ts`.
- **Tests:** **98 passing** (+27 retrieval): embedder, fusion, keyword, in-memory vector
  store, embedding service (index/staleness/force), hybrid search, search/embedding routes
  (RBAC, stats, 404, tenant). Gates green: ruff, mypy strict (96 files), pytest 98/98; web
  lint/tsc/build.

### Phase 5 — Trust Layer ✅

- **Deterministic scoring (`app/trust/scoring.py`):** pure functions — age-based
  freshness (score + band), a five-signal weighted confidence (freshness, ownership,
  processed, embedded, richness) returning a per-signal contribution breakdown, and
  confidence bands. No models; computed **on read**, nothing persisted (ADR-0017).
- **Primitives (`app/trust/base.py`):** frozen `TrustSignals`/`SourceInfo`/`OwnerRef`/
  `EvidenceItem`/`TrustProfile`/`SourceItem`/`FreshnessSummary` (store- and
  schema-agnostic, same layering as retrieval/graph).
- **Trust read model (`app/repositories/trust.py`):** `TrustRepository` joins each
  document to its `DocumentEnrichment` + `DocumentEmbeddingState` in one tenant-scoped
  query (outer joins keep unprocessed/unembedded docs visible at lower confidence);
  portable recency ordering via `coalesce` (no `NULLS LAST`).
- **Ownership from the graph (ADR-0018):** owners are engineers with a `modified` edge
  into a `document:<id>` node, read from the `GraphStore`; list views fetch `modified`
  edges once and match by key prefix. Absence ⇒ *ownership unknown*, never guessed.
- **Trust engine (`app/trust/trust_service.py`):** `profile` (per-document, with
  excerpts + owners), `sources` (provenance list), `freshness` (corpus distribution +
  the documents most needing attention).
- **APIs (`routes/trust.py`):** `GET /trust/documents/{id}`, `/trust/sources`,
  `/trust/freshness` — RBAC + tenant-scoped, read-only (no trigger).
- **Web (`apps/web/app/trust`):** Trust Inspector (why-this-score breakdown, source,
  owners, evidence), Source Explorer (provenance + trust bands), Freshness Dashboard
  (band distribution + needs-attention). "Trust" enabled in nav.
- **Contracts:** TS mirror `trust.ts`.
- **Tests:** **114 passing** (+16): pure scoring, service profile/sources/freshness +
  tenant isolation, routes RBAC/404/422. Gates green: ruff · mypy strict (103 files) ·
  pytest 114/114; web lint/tsc/build.

### Phase 6 — Engineering Assistant ✅

- **Deterministic engine (`app/assistant/`):** pure pieces — `intent.py` (ordered
  keyword classification → SERVICE/OWNERSHIP/INCIDENT/ARCHITECTURE/GENERAL),
  `composer.py` (extractive, templated answer assembly; overall confidence = mean of
  cited trust), `serialize.py` (answer→JSON snapshot). No model provider (ADR-0019);
  same layering as retrieval/graph/trust.
- **Orchestration (`app/assistant/assistant_service.py`):** classify → hybrid retrieve
  (Phase 4 `SearchService`) → attach Phase-5 trust to each cited document (one
  `TrustService.profile` per unique doc) → enrich with one bounded graph neighborhood
  (Phase 3) → compose → persist the exchange. So **every answer carries trust**.
- **Persistence:** `Conversation` + `Message` (`app/models/conversation.py`, PostgreSQL);
  an assistant message stores `intent`, `confidence` and a JSON `answer_json` snapshot
  (summary, citations-with-trust, related facts) faithful to generation time.
  `ConversationRepository` (create/add_message/touch/get/list_recent/list_messages),
  tenant-scoped.
- **APIs (`routes/assistant.py`):** `POST /assistant/ask` (VIEWER, audited),
  `GET /assistant/conversations`, `GET /assistant/conversations/{id}` — tenant-scoped.
- **Web (`apps/web/app/assistant`):** Assistant Workspace (ask + examples + recent),
  conversation thread (answers with trust + follow-up form), Conversation History,
  Evidence Viewer (cited sources ranked by trust, linked to the Trust Inspector).
  Reusable `assistant-answer.tsx`. "Assistant" enabled in nav.
- **Contracts:** TS mirror `assistant.ts`.
- **Tests:** **138 passing** (+24): intent classification, composer (confidence
  aggregate, empty/owners/relations), service ask/continue/list/tenant isolation,
  routes RBAC/round-trip/404/422. Gates: ruff · mypy strict (113 files) · pytest
  138/138; web lint/tsc/build green.

### Phase 7 — Engineering Intelligence ✅

- **Deterministic engine (`app/intelligence/`):** read-only composition of the graph
  (Phase 3) + trust (Phase 5), no model provider and **no new datastore** (ADR-0020) —
  one pure module per concern: `dependency.py` (fan-in/out, blast-radius risk score,
  Tarjan-SCC cycle detection over `depends_on`), `debt.py` (severity from low-confidence
  / stale / unowned trust items), `incident.py` (impact + resolution over `impacts`/
  `resolved`), `ownership.py` (coverage, orphaned components, key-person load over
  `owns`/`modified`), plus a shared `scoring.py` (saturation/clamp/banding). Frozen
  value objects in `base.py`; risk/severity banded by `RiskBand` (enums).
- **Orchestration (`app/intelligence/intelligence_service.py`):** fetches bounded graph
  relationships/entities + the trust source list and delegates to the analyzers;
  `overview` runs all four for the dashboard headline metrics. Computed on read — nothing
  persisted, no run path.
- **APIs (`routes/intelligence.py`):** `GET /intelligence/overview`, `/dependencies`,
  `/debt`, `/incidents`, `/ownership` — VIEWER, tenant-scoped, read-only.
- **Web (`apps/web/app/intelligence`):** Intelligence Dashboard (headline metrics +
  incidents + ownership coverage/orphans), Dependency Risk Dashboard (risk-ranked
  components + cycles), Technical Debt Dashboard (severity-ranked debt + reason
  breakdown, linked to the Trust Inspector). "Intelligence" enabled in nav.
- **Contracts:** TS mirror `intelligence.ts`.
- **Tests:** **160 passing** (+22): dependency/debt/incident/ownership analyzers, service
  over SQLite + in-memory graph, routes RBAC/shape/tenant. Gates: ruff · mypy strict
  (123 files) · pytest 160/160; web lint/tsc/build green.

## Current architecture state

End-to-end now spans ingestion → processing → knowledge graph: UI → API (JWT/RBAC,
tenant-scoped) → Sync/Processing (PostgreSQL); then GraphService projects PostgreSQL
rows into Neo4j and serves the explorers, with curation for architecture; then
EmbeddingService embeds chunks into Qdrant and SearchService answers queries with hybrid
(keyword+vector) ranking plus a graph facet; the **Trust layer** then scores those
signals on read (confidence/freshness/ownership/attribution) across all three stores.
Modular monolith now spanning **all three datastores in use** (PostgreSQL + Neo4j +
Qdrant). Sync/processing/build/embedding paths are all queue-agnostic for a worker; trust
is stateless/read-time (no run path). The **Engineering Assistant** sits on top,
composing retrieval + graph + trust deterministically into evidence-backed answers and
persisting conversations (PostgreSQL) for history + evidence review. The **Engineering
Intelligence** layer then reads the graph + trust on demand to produce dependency-risk,
technical-debt, incident and ownership reports (deterministic, nothing persisted) behind
the Intelligence / Technical Debt / Dependency Risk dashboards.

## Risks

- **R1 — Operational complexity (3 datastores):** PostgreSQL + Neo4j + Qdrant are now all
  in use (Phases 1–4). The `GraphStore` (ADR-0012) and `VectorStore` (ADR-0015)
  abstractions keep both swappable/testable and contain the added complexity.
- **R2 — Two-language stack:** mitigated (shared `packages/contracts`; parity by review).

## Technical debt

- **Heuristic processing (ADR-0010).** Classification/keywords/summary are
  deterministic heuristics, not semantic. LLM-backed steps are a planned upgrade behind
  the same module seams.
- **Synchronous processing execution (ADR-0009).** Runs in-request, bounded by `limit`;
  no durable background worker/queue yet.
- **Deterministic embeddings (ADR-0014).** `HashingEmbedder` is feature-hashing, not a
  learned model — recall is heuristic; a model-backed embedder slots in behind the seam.
  A model swap changes vector dimensions and recreates the collection (chunks in
  PostgreSQL are the source of record).
- **Keyword recall via `LIKE` (ADR-0016).** Portable for prod/test parity but not scalable;
  a PostgreSQL full-text (`tsvector`/GIN) upgrade slots in behind the repository seam. No
  re-ranking; hybrid weights are fixed (RRF).
- **Synchronous embedding (ADR-0009).** Embedding runs in-request; no background worker.
  The `QdrantVectorStore` is covered by manual/integration runs, not unit tests (in-memory
  store stands in).
- **Coarse language detection.** `enricher` returns `en`/`unknown` via stopword overlap.
- **Heuristic graph projection (ADR-0013).** Entities/edges are rule-derived; no NER/LLM.
  Services/APIs and `depends_on` are curation-driven (not auto-derived). Neo4j schema is
  one key constraint (no extra indices/migrations yet); the Cypher `Neo4jGraphStore` is
  covered by manual/integration runs, not unit tests (in-memory store stands in).
- **Synchronous graph build (ADR-0009).** Runs in-request, bounded by `limit`; no worker.
- **Heuristic trust scoring (ADR-0017).** Confidence weights + freshness thresholds are
  fixed heuristics (not learned/calibrated); scores are computed on read with no caching,
  so corpus-wide Source/Freshness views recompute per request — a cached/materialized
  read model is the scale upgrade behind the service seam.
- **Ownership coverage (ADR-0018).** Owners come only from graph `modified` edges (needs
  a graph build; document authorship only); CODEOWNERS / team-of-repo inheritance is a
  later projection upgrade.
- **Heuristic assistant (ADR-0019).** Intent is keyword-classified and answers are
  extractive/templated (no LLM synthesis); graph enrichment is bounded to one
  neighborhood (no multi-hop reasoning); no answer-quality evaluation harness yet. All
  are seams for an LLM-backed upgrade. Conversations have no rename/delete and `ask` runs
  synchronously in-request.
- **Heuristic intelligence (ADR-0020).** Dependency-risk and debt-severity weights
  (saturation ceilings, blend coefficients, freshness penalties) are fixed heuristics, not
  learned/calibrated; reports are computed on read with no caching/materialization, so each
  request recomputes from the graph + trust — a cached read model is the scale upgrade
  behind the service seam. Dependency reasoning is single-edge (fan-in/out + cycles), not
  multi-hop transitive impact; there is no trend/time-series intelligence yet. Dependency
  and ownership coverage are only as complete as graph curation (`depends_on` + team
  ownership must be declared/projected).
- Carried from Phase 1: single implemented connector (GitHub); no Alembic migrations
  (dev `create_all`, tests SQLite); auth is HS256 shared-secret (JWKS/SSO login UI
  pending); default dev secrets MUST be overridden in prod.

## Pending decisions

- Model-backed embedder choice + provider (when recall quality warrants it).
- Whether/when to introduce LLM/NER-backed processing + graph extraction (cost vs quality).
- Background job runner (Celery/Arq/RQ) when sync/processing/build/embedding volume warrants.
- OAuth/OIDC provider for production token issuance + login UI (Phase 1 follow-up).
- Neo4j + Qdrant operational hardening (indices, backups, migrations) ahead of prod scale.
- Trust confidence calibration: when to move from fixed heuristic weights (ADR-0017) to
  learned/calibrated weights, and whether to materialize/cache the trust read model.
- Assistant upgrade path (ADR-0019): when to introduce LLM-backed answer synthesis +
  intent classification, multi-hop graph reasoning, and an answer-quality eval harness.
- Intelligence calibration (ADR-0020): when to move from fixed heuristic risk/severity
  weights to learned/calibrated scoring, whether to materialize/cache the intelligence
  read model, and when to add multi-hop dependency impact + trend (time-series) analysis.

## Recommended next action

Obtain phase-gate approval, then begin **Phase 8 — Agent Layer** (incident agents,
onboarding agents, architecture agents, knowledge-maintenance agents) over the
intelligence + assistant + graph + trust layers, with Agent Workspace / Agent Execution
Viewer / Agent Audit Trail screens.

> **Phase gate:** Phase 7 is complete and verified; **STOP for approval** before
> Phase 8.
