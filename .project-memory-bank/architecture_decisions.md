# Architecture Decision Records (ADRs)

ADRs capture every significant decision. Format: **Context · Options · Decision ·
Consequences**. ADRs are immutable once accepted; supersede rather than rewrite.

Status values: Proposed · Accepted · Superseded · Deprecated.

---

## ADR-0001 — Memory-Bank-First with a docs-only Phase 0 increment

**Status:** Accepted · 2026-06-06

**Context.** Greenfield repo. The project mandates a Memory Bank as the primary
source of truth and a strict phased roadmap. We must establish shared understanding
before writing code.

**Options.**
1. Start coding the foundation immediately.
2. Establish the memory bank + ADRs first, defer code to a follow-up increment.
3. Memory bank + a full code walking-skeleton in one increment.

**Decision.** Option 2. Phase 0 is split: a docs-only increment (this one) that
establishes `.project-memory-bank/` and the foundational ADRs, then a code
walking-skeleton increment after approval.

**Consequences.** Fast, low-risk first increment that locks decisions and makes the
code increment unambiguous. No runnable software yet — acceptable and intentional.

---

## ADR-0002 — Backend: Python + FastAPI

**Status:** Accepted · 2026-06-06

**Context.** EKIP is AI-native (RAG, embeddings, graph + vector retrieval, agents).
The backend must integrate tightly with the Python ML/AI ecosystem while remaining
maintainable and well-typed.

**Options.** Python + FastAPI · Node + NestJS (TS) · Go.

**Decision.** Python + FastAPI. Native access to the AI/RAG ecosystem
(LangChain/LlamaIndex, embedding clients), async I/O, typed contracts via Pydantic,
strong DX.

**Consequences.** Best AI ergonomics; two languages across the stack (Python +
TypeScript). Performance-critical connectors can be optimized or offloaded later if
needed. ASGI server (uvicorn) for async workloads.

---

## ADR-0003 — Frontend: Next.js + React + TypeScript

**Status:** Accepted · 2026-06-06

**Context.** UI is a first-class capability — premium, enterprise-grade,
dark-mode-first, accessible, trust-forward. Need SSR/RSC, mature ecosystem, and a
component system that supports a polished design language.

**Options.** Next.js (App Router) · Vite SPA · Remix/TanStack Start.

**Decision.** Next.js + React + TypeScript with **Tailwind CSS + shadcn/ui** for the
design system.

**Consequences.** Server rendering, routing conventions, and a large ecosystem.
shadcn/ui gives owned, themeable components for trust-UX patterns. See
[`ui_design_system.md`](ui_design_system.md).

---

## ADR-0004 — Data layer: PostgreSQL + Neo4j + Qdrant

**Status:** Accepted · 2026-06-06

**Context.** EKIP needs relational integrity (tenants, users, connectors, jobs), a
true knowledge graph (entities + relationships in Phase 3), and high-quality vector
retrieval (Phase 4).

**Options.** Postgres + pgvector · Postgres + Qdrant · Postgres + Neo4j + Qdrant.

**Decision.** Use all three, each for its strength:
- **PostgreSQL** — system-of-record relational data, jobs, audit, RBAC.
- **Neo4j** — knowledge graph: entities and relationships, traversal/graph retrieval.
- **Qdrant** — vector embeddings and semantic/vector retrieval.

**Consequences.** Most capable foundation for the graph + hybrid-retrieval phases;
**higher operational complexity from day one** (three stores to run, back up, and
secure). Mitigation: docker-compose for local dev, clear store ownership per layer
(see [`system_architecture.md`](system_architecture.md)), and abstraction at the
repository/client layer. Recorded as accepted technical-risk in
[`implementation_status.md`](implementation_status.md).

---

## ADR-0005 — Monorepo layout

**Status:** Accepted · 2026-06-06

**Context.** Backend, frontend, shared types, and infra evolve together across
phases and need atomic cross-cutting changes.

**Options.** Polyrepo · Monorepo.

**Decision.** Single monorepo: `apps/api`, `apps/web`, `packages/` (shared
types/clients/design tokens), `infra/`, `.project-memory-bank/`.

**Consequences.** Atomic changes, shared contracts, simpler onboarding. Requires
discipline on build boundaries; tooling (e.g. turbo/uv workspaces) decided in the
code increment.

---

## ADR-0006 — Security baseline & tenancy posture

**Status:** Accepted · 2026-06-06

**Context.** EKIP ingests sensitive engineering knowledge across organizations.
Security and multi-tenancy cannot be retrofitted.

**Options.** Defer security · Build RBAC + tenant isolation from the foundation with
an ABAC-ready design.

**Decision.** From the foundation: **RBAC now, ABAC-ready** architecture; OAuth/SSO;
audit logging; encryption at rest and in transit; tenant isolation; secrets
management. Details in [`security_requirements.md`](security_requirements.md).

**Consequences.** Slightly more upfront design; avoids costly rework and earns trust.
Enforced as acceptance criteria in every code increment.

---

## ADR-0007 — Monorepo tooling & dependency management

**Status:** Accepted · 2026-06-06

**Context.** ADR-0005 chose a monorepo but deferred tooling. The Phase 0 code
walking-skeleton needs a concrete, low-ceremony toolchain that does not over-engineer
a two-app repo.

**Options.** Heavy orchestrator (Nx/Turborepo + workspaces) now · Per-app native
tooling (pip/PEP 621 for Python, npm for web) with a thin shared types package · Defer
again.

**Decision.** Per-app native tooling for now:
- **API:** PEP 621 `pyproject.toml` (hatchling), installable via `pip`/`uv`; `ruff`,
  `mypy`, `pytest`.
- **Web:** `npm` + Next.js scripts; ESLint, `tsc`, `next build`.
- **Shared contracts:** `packages/contracts` is a **type-only** TS package consumed via
  a tsconfig path alias + `transpilePackages` — no build step, no workspace installer
  required. Python schemas are the authoritative source; TS types mirror them.
- CI runs each app's gates independently ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)).

**Consequences.** Minimal moving parts and fast onboarding (simplicity first). No
cross-app task caching/orchestration yet; if build coordination becomes painful we
revisit with Turborepo/uv workspaces (superseding ADR). Contract parity between Python
and TS is maintained by convention + review until a generator is introduced.
