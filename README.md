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
| **Current phase** | Phase 0 — Project Foundation |
| **Current increment** | Documentation only (memory bank) — **no application code yet** |
| **Next increment** | Phase 0 code walking-skeleton (awaiting approval) |

The authoritative, always-current status lives in
[`.project-memory-bank/implementation_status.md`](.project-memory-bank/implementation_status.md).

## Source of truth — read this first

This project follows a **Memory Bank First** discipline. The
[`.project-memory-bank/`](.project-memory-bank/) directory is the primary source of
truth. Before any work, read in order:

1. [`implementation_status.md`](.project-memory-bank/implementation_status.md)
2. [`roadmap.md`](.project-memory-bank/roadmap.md)
3. [`architecture_decisions.md`](.project-memory-bank/architecture_decisions.md)

## Technology stack (decided)

| Layer | Choice | ADR |
|---|---|---|
| Backend | Python + FastAPI | ADR-0002 |
| Frontend | Next.js + React + TypeScript (shadcn/ui + Tailwind, dark-mode-first) | ADR-0003 |
| Relational store | PostgreSQL | ADR-0004 |
| Knowledge graph | Neo4j | ADR-0004 |
| Vector store | Qdrant | ADR-0004 |

## Intended repository layout

> Documented now; created in the upcoming code increment.

```
.
├── apps/
│   ├── api/                 # FastAPI backend services
│   └── web/                 # Next.js frontend
├── packages/                # Shared libraries (types, clients, design tokens)
├── infra/                   # IaC, docker-compose, CI/CD config
├── .project-memory-bank/    # Source of truth (docs)
└── README.md
```

## License

GPL-3.0 — see [LICENSE](LICENSE).
