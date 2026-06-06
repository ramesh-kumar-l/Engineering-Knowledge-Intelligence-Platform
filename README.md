# EKIP — Engineering Knowledge Intelligence Platform

> The trusted engineering memory and intelligence layer for software organizations.

EKIP helps engineering organizations defeat knowledge fragmentation, knowledge loss,
slow onboarding, architectural drift, and repeated incidents. It evolves through three
stages:

**Engineering Memory → Engineering Intelligence → Engineering Cognition**

It is designed to eventually answer, with visible trust:

- How does this service work?
- Why was this architecture chosen?
- Who owns this component?
- What dependencies matter?
- What caused this incident?
- What risks exist?
- What should we do next?

---

## Project status

| | |
|---|---|
| **Current phase** | Phase 8 — Agent Layer (complete) — **all roadmap phases (0–8) delivered** |
| **Delivered** | Phases 0–7 **and** Phase 8 agents: deterministic, fixed-plan incident / onboarding / architecture / knowledge-maintenance agents that compose retrieval + graph + trust + intelligence (no model provider, no new datastore) and persist an auditable run + step trace + trust-carrying result; agent APIs + Agent Workspace / Execution Viewer / Audit Trail |
| **Next** | Production-hardening (tracked as debt): remaining connectors, Alembic, OAuth/SSO login UI, background worker, LLM-backed upgrades behind existing seams |

The authoritative, always-current status lives in
[`.project-memory-bank/implementation_status.md`](.project-memory-bank/implementation_status.md).

## Source of truth — read this first

This project follows a **Memory Bank First** discipline. The
[`.project-memory-bank/`](.project-memory-bank/) directory is the primary source of
truth. Before any work, read in order:

1. [`implementation_status.md`](.project-memory-bank/implementation_status.md)
2. [`active-context.md`](.project-memory-bank/active-context.md)
3. [`roadmap.md`](.project-memory-bank/roadmap.md)
4. [`architecture_decisions.md`](.project-memory-bank/architecture_decisions.md)

## Technology stack (decided)

| Layer | Choice | ADR |
|---|---|---|
| Backend | Python + FastAPI | ADR-0002 |
| Frontend | Next.js + React + TypeScript (shadcn/ui + Tailwind, dark-mode-first) | ADR-0003 |
| Relational store | PostgreSQL | ADR-0004 |
| Knowledge graph | Neo4j | ADR-0004 |
| Vector store | Qdrant | ADR-0004 |

## Repository layout

```
.
├── apps/
│   ├── api/                 # FastAPI backend (health, connectors, sync, documents,
│   │                        #   processing, graph, embeddings, search, trust, assistant,
│   │                        #   intelligence, agents; models/repositories/processing/graph/
│   │                        #   retrieval/trust/assistant/intelligence/agents/services;
│   │                        #   PG + Neo4j + Qdrant; JWT + audit)
│   └── web/                 # Next.js frontend (Overview + Connectors/Sync/Processing/
│                            #   Knowledge Graph/Search/Trust/Assistant/Intelligence/Agents UI)
├── packages/
│   └── contracts/           # Shared TS API contract types (mirror Pydantic schemas)
├── infra/                   # docker-compose: PostgreSQL + Neo4j + Qdrant
├── .github/workflows/       # CI: api · web · security scanning
├── .project-memory-bank/    # Source of truth (docs)
└── README.md
```

## Run locally

```bash
docker compose -f infra/docker-compose.yml up -d   # datastores
cd apps/api && pip install -e ".[dev]" && uvicorn app.main:app --reload   # API :8000
cd apps/web && npm install && npm run dev                                 # Web :3000
```

## License

GPL-3.0 — see [LICENSE](LICENSE).
