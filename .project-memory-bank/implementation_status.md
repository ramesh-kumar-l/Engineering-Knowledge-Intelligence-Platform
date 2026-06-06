# Implementation Status

> **Read this first.** Live state of the project. Updated after every task.

**Last updated:** 2026-06-06

## Current phase

**Phase 2 — Knowledge Processing Layer.** Complete and verified; **at the phase gate**
awaiting approval to start Phase 3. Phases 0 and 1 are done.

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
  (SQLite), processing routes (RBAC, stats, events, 404s, tenant isolation). Gates
  green: **ruff · mypy strict (69 files) · pytest 50/50**; web **lint · tsc · build**.

## Current architecture state

End-to-end now spans ingestion → processing: UI → API (JWT/RBAC, tenant-scoped) →
SyncService → documents; then ProcessingService → chunks + enrichment + processing
runs/events + audit. Still a modular monolith on PostgreSQL only; the processing path
is queue-agnostic for a future worker.

## Risks

- **R1 — Operational complexity (3 datastores):** mitigated; Phases 1–2 use PostgreSQL
  only. Neo4j unused until Phase 3; Qdrant until Retrieval (ADR-0011).
- **R2 — Two-language stack:** mitigated (shared `packages/contracts`; parity by review).

## Technical debt

- **Heuristic processing (ADR-0010).** Classification/keywords/summary are
  deterministic heuristics, not semantic. LLM-backed steps are a planned upgrade behind
  the same module seams.
- **Chunks not embedded yet (ADR-0011).** Stored in PostgreSQL; embedding into Qdrant
  is owned by the Retrieval phase.
- **Synchronous processing execution (ADR-0009).** Runs in-request, bounded by `limit`;
  no durable background worker/queue yet.
- **Coarse language detection.** `enricher` returns `en`/`unknown` via stopword overlap.
- Carried from Phase 1: single implemented connector (GitHub); no Alembic migrations
  (dev `create_all`, tests SQLite); auth is HS256 shared-secret (JWKS/SSO login UI
  pending); default dev secrets MUST be overridden in prod.

## Pending decisions

- Embedding model + provider for Qdrant (Retrieval phase).
- Whether/when to introduce LLM-backed processing steps (cost vs quality).
- Background job runner (Celery/Arq/RQ) when sync/processing volume warrants.
- OAuth/OIDC provider for production token issuance + login UI (Phase 1 follow-up).

## Recommended next action

Obtain phase-gate approval, then begin **Phase 3 — Knowledge Graph Layer** (entities:
Engineer/Team/Repository/Service/API/Incident/ADR/Document; relationships: owns/
depends_on/modified/impacts/resolved) over the processed documents, introducing Neo4j,
with Knowledge/Service/Team Explorer + Dependency Graph screens.

> **Phase gate:** Phase 2 is complete and verified; **STOP for approval** before
> Phase 3.
