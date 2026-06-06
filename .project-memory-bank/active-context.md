# Active Context

> Compressed "save state" for resuming work fast. Pairs with
> [`implementation_status.md`](implementation_status.md) (full status). Update before
> ending any major feature.

**Last updated:** 2026-06-06

## Where we are

Phase 2 — Knowledge Processing is **complete and verified**, sitting at the **phase
gate** awaiting approval to start Phase 3. End-to-end runs: UI → API (JWT/RBAC,
tenant-scoped) → SyncService → documents → ProcessingService → chunks + enrichment.

## What just happened (this increment)

Built the processing layer: deterministic pipeline (`app/processing/` — parser,
chunker, classifier, enricher, summarizer, pipeline) over a `text` primitives module;
models `ProcessingRun`/`ProcessingEvent`, 1:1 `DocumentEnrichment`, `Chunk`;
repositories + `ProcessingService` (select pending/stale/failed → process → replace
chunks + upsert enrichment); processing APIs (runs/events/stats/explorer); four
processing screens; TS contracts. Added ADR-0010 (deterministic pluggable pipeline)
and ADR-0011 (chunks in PG, embeddings deferred to Retrieval).

Gates: API `ruff` clean · `mypy app` clean (69 files) · `pytest` 50/50. Web
`lint` · `typecheck` · `build` all green (routes incl. /processing,
/processing/jobs/[runId], /processing/chunks, /processing/explorer{,/[id]}).

## How to run it

```bash
docker compose -f infra/docker-compose.yml up -d          # PG + Neo4j + Qdrant
cd apps/api && uvicorn app.main:app --reload              # API on :8000 (auto-creates schema in dev)
cd apps/web && npm run dev                                # Web on :3000
```

Flow to exercise: add a GitHub connector → Run sync (ingests documents) → Processing →
Run processing (parses/chunks/classifies/enriches/summarizes) → Chunk Statistics /
Parsing Explorer. Dev auth: web client sends `X-Tenant-Id`/`X-Role` (editor) headers.

## Active decisions / constraints to remember

- Processing steps are deterministic and dependency-light (ADR-0010); each module is
  the seam to swap in an LLM-backed step later. No external model providers yet.
- Chunks are stored in PostgreSQL; embedding into Qdrant is owned by the Retrieval
  phase (ADR-0011). Phases 1–2 are single-datastore (PostgreSQL).
- Reprocessing is driven by `DocumentEnrichment.source_content_hash` vs the document's
  `content_hash` (plus failed status); processing runs synchronously (ADR-0009).
- `ProcessingRun`/`ProcessingEvent` reuse `SyncStatus`/`SyncEventLevel` (generic job
  lifecycle / log levels).
- Keep files < 300 lines; one concern per file. Python schemas authoritative; TS
  `packages/contracts` mirror them.

## Next step (after gate approval)

Phase 3 — Knowledge Graph Layer: model entities + relationships over processed
documents, introduce Neo4j, deliver Knowledge/Service/Team Explorer + Dependency Graph.
See [`roadmap.md`](roadmap.md) Phase 3.
