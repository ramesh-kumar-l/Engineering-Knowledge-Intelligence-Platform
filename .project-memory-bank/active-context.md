# Active Context

> Compressed "save state" for resuming work fast. Pairs with
> [`implementation_status.md`](implementation_status.md) (full status). Update before
> ending any major feature.

**Last updated:** 2026-06-06

## Where we are

Phase 5 — Trust is **complete and verified**, sitting at the **phase gate** awaiting
approval to start Phase 6. End-to-end runs: UI → API (JWT/RBAC, tenant-scoped) → Sync →
documents → Processing → chunks/enrichment → Graph build (Neo4j) and Embedding (Qdrant)
→ hybrid Search → **Trust** scoring (confidence/freshness/ownership/attribution computed
on read over all three datastores).

## What just happened (this increment)

Built the trust layer: pure deterministic scoring (`app/trust/scoring.py` — freshness
decay + band, five-signal weighted confidence with a per-signal breakdown, bands;
ADR-0017); trust primitives (`app/trust/base.py`); a `TrustRepository` joining document +
enrichment + embedding state in one query; a `TrustService` (`profile`, `sources`,
`freshness`) that attributes ownership from the graph's `modified` edges (ADR-0018);
read-only trust APIs (`routes/trust.py`); three screens (Trust Inspector, Source
Explorer, Freshness Dashboard); TS contracts (`trust.ts`). Added ADR-0017/0018. **No new
datastore and no new persistence** — trust is computed on read.

Gates: API `ruff` clean · `mypy app` clean (103 files) · `pytest` **114/114**. Web
`lint` · `typecheck` · `build` all green (routes incl. /trust, /trust/documents/[id],
/trust/freshness).

## How to run it

```bash
docker compose -f infra/docker-compose.yml up -d          # PG + Neo4j + Qdrant
cd apps/api && uvicorn app.main:app --reload              # API on :8000 (auto-creates PG schema in dev)
cd apps/web && npm run dev                                # Web on :3000
```

Flow to exercise: add a GitHub connector → Run sync → Run processing → Build graph →
Embed corpus → then **Trust → Source Explorer** (each doc's confidence/freshness/owner)
→ open a document's **Trust Inspector** (why-this-score breakdown + provenance + owners +
evidence) → **Freshness Dashboard** (corpus distribution + stale docs). Dev auth: web
client sends `X-Tenant-Id`/`X-Role` headers.

## Active decisions / constraints to remember

- Trust is **deterministic and computed on read** (ADR-0017) — nothing persisted, so a
  profile always reflects current state; no run/trigger UI. Confidence = weighted blend
  of freshness/ownership/processed/embedded/richness (fixed heuristic weights, tunable in
  `scoring.py`); contributions sum to the score for the inspector.
- **Ownership comes from the graph** (ADR-0018): engineers with a `modified` edge into a
  `document:<id>` node. No edge ⇒ *ownership unknown* (never guessed). Needs a graph
  build to populate.
- Trust read model is a single join (`TrustRepository`: document + enrichment + embedding
  state); outer joins keep unprocessed/unembedded docs visible at lower confidence.
- Corpus-wide views recompute per request — a cached/materialized read model is the scale
  upgrade behind the `TrustService` seam.
- Keep files < 300 lines; one concern per file. Python schemas authoritative; TS
  `packages/contracts` mirror them.

## Next step (after gate approval)

Phase 6 — Engineering Assistant: service understanding, ownership discovery, incident
exploration, architecture explanations over retrieval + graph + trust; every answer
carries trust (Phase 5 signals). Screens: Assistant Workspace, Conversation History,
Evidence Viewer. See [`roadmap.md`](roadmap.md) Phase 6.
