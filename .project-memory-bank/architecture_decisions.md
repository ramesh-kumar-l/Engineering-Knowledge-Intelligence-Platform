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

---

## ADR-0008 — Authentication (JWT bearer) & secret encryption at rest

**Status:** Accepted · 2026-06-06 (Phase 1)

**Context.** Phase 0 shipped a DEV-only header principal resolver, explicitly not a
security boundary. Phase 1 exposes tenant data through real APIs, so it needs an
enforceable auth boundary (security_requirements.md: OAuth/SSO at Phase 1) and
encrypted connector credentials.

**Options.**
1. Full OAuth/OIDC server + session management built in-house now.
2. Verify signed **JWT bearer tokens** issued by any OAuth/OIDC IdP; keep a dev
   header fallback gated to non-production.
3. Defer auth again.

**Decision.** Option 2. ``get_principal`` verifies a ``Bearer`` JWT (PyJWT) and
derives the tenant-scoped ``Principal`` from claims (``sub``, ``tenant_id``,
``role``); signature/audience/issuer/expiry are validated. The dev header fallback is
honored only when ``header_auth_allowed`` (``dev_auth_enabled and not production``).
Connector credentials are encrypted at rest with Fernet (``SecretBox``), key derived
from ``EKIP_SECRET_KEY``; secrets are write-only over the API.

**Consequences.** A real, IdP-agnostic security boundary in production without
building an IdP; any provider issuing JWTs integrates. JWKS/RS256 rotation and a
full login UI are natural extensions. Default dev secrets must be overridden via env
in staging/production (documented as acceptance criteria + tech debt).

---

## ADR-0009 — Synchronous in-request sync execution (no job queue yet)

**Status:** Accepted · 2026-06-06 (Phase 1)

**Context.** Ingestion syncs call external APIs and write many rows. A durable
background worker/queue is the eventual target, but adding one now (broker, workers,
deployment) is significant infrastructure.

**Options.** Background worker/queue (Celery/RQ/Arq) now · Run the sync synchronously
inside the trigger request, behind a service seam · Fire-and-forget asyncio task.

**Decision.** Run ``SyncService`` synchronously within ``POST /connectors/{id}/sync``.
A single GitHub sync is bounded (``_MAX_PAGES``) and the cursor resumes the rest. The
service is queue-agnostic, so a worker can later invoke the exact same code path.

**Consequences.** Simplest correct option; fully testable without infrastructure.
Long syncs are bounded per request; large backfills need the worker (deferred,
tracked in implementation_status.md). No re-split of the modular monolith required.

---

## ADR-0010 — Deterministic, pluggable processing pipeline (no LLM yet)

**Status:** Accepted · 2026-06-06 (Phase 2)

**Context.** The processing layer must parse, chunk, classify, enrich and summarize
ingested documents. LLM-based implementations are powerful but add an external
provider dependency, non-determinism, cost, and tests that need network/keys —
working against a "production-stable, testable" first increment.

**Options.**
1. LLM-backed classification/summarization now (provider + keys + prompts).
2. Deterministic, dependency-light steps (regex parsing, frequency-based keywords/
   summary, heuristic classification) behind small per-step modules.
3. Defer the layer.

**Decision.** Option 2. Each step is a pure function in its own module under
``app/processing/`` (``parser``, ``chunker``, ``classifier``, ``enricher``,
``summarizer``), composed by ``pipeline.process``. No I/O, no external models, fully
deterministic — so every step is unit-testable and runs offline. The module
boundaries are the seam: an LLM-backed implementation can replace any single step
without touching the service or the rest of the pipeline.

**Consequences.** Stable, fast, free, reproducible output now; quality is heuristic,
not semantic. Swapping in model-backed steps later is isolated and low-risk. Tracked
as a deliberate upgrade path, not debt.

---

## ADR-0011 — Persist chunks in PostgreSQL; defer vectorization to Retrieval

**Status:** Accepted · 2026-06-06 (Phase 2)

**Context.** Chunks are the unit later embedded into Qdrant for vector retrieval.
Embedding now requires choosing a model/provider and standing up Qdrant write paths,
neither of which retrieval (Phase 4) has specified yet.

**Decision.** Store chunks (text + counts + content hash) in PostgreSQL as the system
of record. ``Chunk`` carries everything an embedding step will need; chunks for a
document are replaced wholesale on reprocessing. Embedding into Qdrant is owned by the
Retrieval phase.

**Consequences.** Phase 2 stays single-datastore (PostgreSQL), matching R1 mitigation
(Neo4j/Qdrant unused until later phases). Re-embedding is a clean downstream pass over
stored chunks. The chunk schema is stable for the embedding step to build on.

---

## ADR-0012 — Graph store abstraction (Neo4j + in-memory implementations)

**Status:** Accepted · 2026-06-06 (Phase 3)

**Context.** The knowledge graph lives in Neo4j (ADR-0004). Unlike PostgreSQL — where
SQLite stands in for fast, offline tests — Neo4j has no embeddable test engine, yet the
test suite must run without live datastores (conftest discipline).

**Options.**
1. Require a live/embedded Neo4j (or testcontainers) for any graph test.
2. Mock the driver per test.
3. Define a ``GraphStore`` protocol with a Neo4j implementation (production) and an
   in-memory implementation (tests + Neo4j-free local runs).

**Decision.** Option 3. ``app/graph/store.py`` declares the ``GraphStore`` protocol and
an ``InMemoryGraphStore``; ``app/graph/neo4j_store.py`` is the Cypher-backed
``Neo4jGraphStore`` wired via ``get_graph_store``. Nodes share the ``:Entity`` label
with a ``kind`` property (one uniqueness constraint on ``(tenant_id, key)``);
relationships are typed edges whose type comes from the ``RelationshipType`` enum member
name (enum-controlled, so safe to interpolate). Every operation is tenant-scoped.

**Consequences.** The service is free of driver details and fully unit/integration
tested offline against the in-memory store — the same seam SQLite provides for
PostgreSQL. The thin Cypher store is exercised by manual/integration runs, not unit
tests (as the real ``PostgresStore`` is). Production requires Neo4j to be reachable
(docker-compose provides it); there is no silent runtime fallback that would mask a
misconfiguration.

---

## ADR-0013 — Deterministic graph projection + editor curation (no LLM/NER)

**Status:** Accepted · 2026-06-06 (Phase 3)

**Context.** The graph needs entities (Engineer/Team/Repository/Service/API/Incident/
ADR/Document) and relationships (owns/depends_on/modified/impacts/resolved). Full
NER/LLM extraction is non-deterministic, adds a provider dependency, and is untestable
offline — the same tension ADR-0010 resolved for processing.

**Decision.** Two complementary, deterministic sources:
1. **Projection (``app/graph/builder.py``):** a pure function maps already-ingested data
   to the graph — connectors → Repository (+ owning Team), documents → Document nodes,
   ``author`` metadata → Engineer (``modified`` Document/Repository), INCIDENT-category
   documents → Incident (``impacts`` Repository; ``resolved`` by the author when closed),
   ADR-titled documents → ADR. Idempotent upserts converge on re-runs. A
   ``GraphBuildRun``/``Event`` (PostgreSQL) records each build (ADR-0009 synchronous).
2. **Curation:** ``POST /graph/entities`` and ``POST /graph/relationships`` (editor,
   audited) let architects declare what cannot be derived honestly — Services, APIs and
   ``depends_on`` edges — auto-creating endpoints.

**Consequences.** A genuinely useful graph from real data on day one, plus a first-class
path for curated architecture, with zero model dependency. Projection quality is
heuristic; an LLM-backed extractor can later add edges behind the same builder seam.
``depends_on``/Services are curation-driven until such an extractor exists (documented as
debt, not a gap).

---

## ADR-0014 — Deterministic embeddings behind an ``Embedder`` seam (no model provider)

**Status:** Accepted · 2026-06-06 (Phase 4)

**Context.** Retrieval needs chunk embeddings. A hosted/model embedder (OpenAI,
sentence-transformers) adds an external provider, API keys, cost and non-determinism,
and makes tests need network — the same tension ADR-0010/0013 resolved for processing
and graph projection.

**Options.**
1. Model-backed embeddings now (provider + keys).
2. A deterministic, dependency-free embedder behind a protocol.
3. Defer retrieval.

**Decision.** Option 2. ``app/retrieval/embedder.py`` defines the ``Embedder`` protocol
and a ``HashingEmbedder`` — signed feature hashing of tokens into a fixed-dimension
(256) L2-normalized vector. It is pure, reproducible and offline; cosine similarity of
two such vectors approximates weighted token overlap. The protocol is the seam: a
model-backed embedder can replace it without touching the stores or services. The
embedder is a stateless process-wide singleton (``deps._EMBEDDER``).

**Consequences.** Useful semantic-ish recall on day one with zero provider dependency
and fully offline tests; recall quality is heuristic, not learned. Swapping in a real
model later is isolated; re-embedding is a clean pass over stored chunks. A model
upgrade changes vector dimensions, so the collection is recreated on first run with the
new ``dimension`` — acceptable because chunks (PostgreSQL) are the system of record.

---

## ADR-0015 — Vector store abstraction (Qdrant + in-memory implementations)

**Status:** Accepted · 2026-06-06 (Phase 4)

**Context.** Embeddings live in Qdrant (ADR-0004). Like Neo4j (ADR-0012), Qdrant has no
embeddable test engine, yet the suite must run without live datastores.

**Decision.** ``app/retrieval/vector_store.py`` declares the ``VectorStore`` protocol and
an ``InMemoryVectorStore`` (cosine over a dict); ``app/retrieval/qdrant_store.py`` is the
``QdrantVectorStore`` wired via ``get_vector_store``. One shared collection
(``ekip_chunks``) holds every tenant's vectors; isolation is a mandatory ``tenant_id``
payload filter on every search/delete. Point ids are chunk UUIDs (re-embedding
overwrites); a document's points are deleted before re-upsert, matching wholesale chunk
replacement on reprocessing.

**Consequences.** Services are free of driver details and unit/integration tested offline
against the in-memory store — the same seam SQLite and ``InMemoryGraphStore`` provide. The
thin Qdrant adapter is exercised by integration runs, not unit tests. Production requires
Qdrant reachable (docker-compose provides it); no silent runtime fallback.

---

## ADR-0016 — Hybrid retrieval via reciprocal rank fusion (synchronous embedding)

**Status:** Accepted · 2026-06-06 (Phase 4)

**Context.** Search must combine keyword precision, vector recall, and graph structure.
Scores from a ``LIKE``-based keyword ranker and cosine vector search are not directly
comparable, and embedding the corpus is a batch job like sync/processing (ADR-0009).

**Decision.** Two retrievers over chunks — keyword (portable ``LIKE`` candidates ranked
deterministically in ``retrieval.keyword``) and vector (query embedded, matched in the
vector store) — are blended by **reciprocal rank fusion** (``retrieval.fusion``, a pure
function). ``mode`` selects ``keyword``/``vector``/``hybrid``. A knowledge-graph entity
match is always returned as a complementary facet. Embedding runs **synchronously**
in-request (``EmbeddingService``), recording an ``EmbeddingRun``/``Event`` and a
per-document staleness ledger (``DocumentEmbeddingState``) so re-runs embed only changed
documents.

**Consequences.** Robust ranking without score calibration, fully unit-testable; graph
context enriches every search. Keyword candidate retrieval uses ``LIKE`` for prod/test
parity — a PostgreSQL full-text (``tsvector``/GIN) upgrade slots in behind the repository
seam. Embedding is bounded per request; a background worker is the eventual target
(deferred, tracked in implementation_status.md).

---

## ADR-0017 — Trust scoring is deterministic and computed on read

**Status:** Accepted · 2026-06-06 (Phase 5)

**Context.** The trust layer must surface confidence, freshness, source attribution and
ownership for ingested knowledge (``trust_framework.md``). Two questions: how to score,
and whether to persist scores. Trust signals derive entirely from current state —
document provenance/timestamps, processing + embedding state, and graph ownership — all
of which already change through their own staleness paths (sync, processing, embedding).

**Decision.** Trust is a pure, deterministic function of existing signals, computed at
request time; **nothing is persisted**. ``app/trust/scoring.py`` holds the pure scorers
(freshness decay + band, a five-signal weighted confidence with a per-signal
contribution breakdown, confidence band), mirroring ``retrieval.fusion``/``keyword``.
``TrustService`` assembles a profile from a single ``TrustRepository`` join (document +
enrichment + embedding state) plus chunk excerpts and graph ownership. No model
providers (consistent with ADR-0010/0013/0014).

**Consequences.** A profile always reflects current state — there is no trust ledger to
recompute or invalidate, and no trigger/run UI is needed (unlike processing/embedding).
Confidence weights and freshness thresholds are fixed heuristics tunable in one place
(documented as tech debt). Corpus-wide views (Source Explorer, Freshness Dashboard)
recompute per request; for large corpora this moves behind a cached/materialized read
model later, behind the same service seam.

---

## ADR-0018 — Ownership attributed from the knowledge graph

**Status:** Accepted · 2026-06-06 (Phase 5)

**Context.** "Who owns this?" must be answered from evidence, not guessed
(``trust_framework.md``: *attribute ownership from the knowledge graph*). The Phase 3
projection already derives ``(engineer) -[modified]-> (document)`` edges from document
authorship.

**Decision.** A document's owners are the engineers with a ``modified`` edge into its
``document:<id>`` node, read from the ``GraphStore``. The Trust Inspector reads the
document's neighborhood; list/aggregate views fetch ``modified`` relationships once and
match by the ``document:`` key prefix (robust to whether a store populates edge endpoint
metadata), avoiding a per-document lookup. Absence of an edge is reported as
**ownership unknown** rather than fabricated.

**Consequences.** Ownership is evidence-backed and tenant-scoped, and contributes a
signal to confidence (ADR-0017). It is only as complete as the graph: documents without
an author, or before a graph build, show as unowned — a true coverage signal. Richer
ownership (CODEOWNERS, team-of-repo inheritance) is a later projection upgrade behind
the same graph seam.
