# Active Context

> Compressed "save state" for resuming work fast. Pairs with
> [`implementation_status.md`](implementation_status.md) (full status). Update before
> ending any major feature.

**Last updated:** 2026-06-06 (Phase 7)

## Where we are

Phase 7 — Engineering Intelligence is **complete and verified**, sitting at the **phase
gate** awaiting approval to start Phase 8. End-to-end runs: UI → API (JWT/RBAC,
tenant-scoped) → Sync → documents → Processing → chunks/enrichment → Graph build (Neo4j)
and Embedding (Qdrant) → hybrid Search → Trust scoring → Assistant (deterministic Q&A)
→ **Intelligence** (deterministic dependency-risk / technical-debt / incident / ownership
reports read on demand from the graph + trust).

## What just happened (this increment)

Built the intelligence layer: pure pieces in `app/intelligence/` — `dependency.py`
(fan-in/out, blast-radius risk score, Tarjan-SCC cycle detection over `depends_on`),
`debt.py` (severity from low-confidence/stale/unowned trust items), `incident.py` (impact
+ resolution over `impacts`/`resolved`), `ownership.py` (coverage, orphans, key-person
load over `owns`/`modified`), a shared `scoring.py` (saturate/clamp/band) and frozen
value objects in `base.py`. `intelligence_service.py` fetches bounded graph + trust inputs
and delegates; `overview` aggregates headline metrics. New `RiskBand` enum. Read-write
APIs are read-only (`routes/intelligence.py`): `GET /intelligence/overview`,
`/dependencies`, `/debt`, `/incidents`, `/ownership` (VIEWER, tenant-scoped). Three
screens: Intelligence Dashboard, Dependency Risk Dashboard, Technical Debt Dashboard. TS
contracts (`intelligence.ts`). Added ADR-0020. **No new datastore, no model provider** —
everything is computed on read, nothing persisted (same posture as Trust, ADR-0017).

Gates: API `ruff` clean · `mypy app` clean (123 files) · `pytest` **160/160**. Web
`lint` · `typecheck` · `build` all green (routes incl. /intelligence, /intelligence/debt,
/intelligence/dependencies).

## How to run it

```bash
docker compose -f infra/docker-compose.yml up -d          # PG + Neo4j + Qdrant
cd apps/api && uvicorn app.main:app --reload              # API on :8000 (auto-creates PG schema in dev)
cd apps/web && npm run dev                                # Web on :3000
```

Flow to exercise: add a GitHub connector → Run sync → Run processing → Build graph →
(curate `depends_on` edges between services in the Knowledge Graph) → open
**Intelligence** → see dependency risk + cycles, technical-debt severity (linked to the
**Trust Inspector**), incidents and ownership coverage/orphans. Dev auth: web client
sends `X-Tenant-Id`/`X-Role` headers.

## Active decisions / constraints to remember

- Intelligence is **read-only, deterministic and composed** (ADR-0020): no model
  provider, no new datastore — it reads the graph (Phase 3) + trust (Phase 5) on demand.
  Risk/severity use **fixed heuristic weights** banded by `RiskBand`; the analyzers are
  pure and offline-testable; the weights are seams for later calibration.
- Coverage is honest: unowned/orphaned components and missing `depends_on` curation are
  **surfaced as gaps**, never fabricated. Dependency + ownership views are only as complete
  as graph curation.
- Reports are **computed on read with no caching** — a cached/materialized read model is
  the scale upgrade behind the service seam. Dependency reasoning is single-edge (fan-in/
  out + cycles), not multi-hop transitive impact; no trend/time-series yet.
- Keep files < 300 lines; one concern per file. Python schemas authoritative; TS
  `packages/contracts` mirror them.

## Next step (after gate approval)

Phase 8 — Agent Layer: incident agents, onboarding agents, architecture agents,
knowledge-maintenance agents over the intelligence + assistant + graph + trust layers.
Screens: Agent Workspace, Agent Execution Viewer, Agent Audit Trail. See
[`roadmap.md`](roadmap.md) Phase 8.
