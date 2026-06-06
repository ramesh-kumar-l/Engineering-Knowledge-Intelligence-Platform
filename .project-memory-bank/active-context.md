# Active Context

> Compressed "save state" for resuming work fast. Pairs with
> [`implementation_status.md`](implementation_status.md) (full status). Update before
> ending any major feature.

**Last updated:** 2026-06-06

## Where we are

Phase 0 is **code-complete and verified**, sitting at the **phase gate** awaiting
approval to start Phase 1. The walking skeleton runs end-to-end: web Overview →
API `/health/ready` → PostgreSQL/Neo4j/Qdrant health probes.

## What just happened (this increment)

Built the Phase 0 code walking-skeleton: FastAPI backend (`apps/api`), Next.js
frontend (`apps/web`), shared type contracts (`packages/contracts`), docker-compose
(`infra/`), and CI (`.github/workflows/ci.yml`). Added ADR-0007 (tooling). All
quality gates pass locally:
- API: `ruff check .` clean · `mypy app` clean · `pytest` 9/9.
- Web: `npm run lint` clean · `npm run typecheck` clean · `npm run build` succeeds.

## How to run it

```bash
docker compose -f infra/docker-compose.yml up -d          # PG + Neo4j + Qdrant
cd apps/api && uvicorn app.main:app --reload              # API on :8000
cd apps/web && npm run dev                                # Web on :3000
```

## Active decisions / constraints to remember

- Per-app tooling, no monorepo orchestrator yet (ADR-0007).
- `get_principal` is a **DEV-only** header-based stub — replace with OAuth/SSO in
  Phase 1 (it is not a security boundary).
- Keep files < 300 lines; one concern per file (coding_standards + user directive).
- Python schemas are authoritative; `packages/contracts` TS types must mirror them.

## Next step (after gate approval)

Phase 1 — Knowledge Ingestion Layer: first connector + incremental sync + metadata,
PostgreSQL-backed audit events + real auth, with Connector Catalog / Sync Dashboard
UI. See [`roadmap.md`](roadmap.md) Phase 1.
