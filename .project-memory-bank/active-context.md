# Active Context

> Compressed "save state" for resuming work fast. Pairs with
> [`implementation_status.md`](implementation_status.md) (full status). Update before
> ending any major feature.

**Last updated:** 2026-06-06

## Where we are

Phase 6 — Engineering Assistant is **complete and verified**, sitting at the **phase
gate** awaiting approval to start Phase 7. End-to-end runs: UI → API (JWT/RBAC,
tenant-scoped) → Sync → documents → Processing → chunks/enrichment → Graph build (Neo4j)
and Embedding (Qdrant) → hybrid Search → Trust scoring → **Assistant** (deterministic
Q&A that composes retrieval + graph + trust into evidence-backed answers and persists
conversations).

## What just happened (this increment)

Built the assistant layer: pure pieces in `app/assistant/` — `intent.py` (ordered
keyword classification into SERVICE/OWNERSHIP/INCIDENT/ARCHITECTURE/GENERAL),
`composer.py` (extractive, templated answer assembly; overall confidence = mean of cited
trust), `serialize.py` (answer→JSON snapshot); `assistant_service.py` orchestrates
classify → hybrid retrieve → attach Phase-5 trust per cited doc → enrich with one bounded
graph neighborhood → compose → persist. New persistence: `Conversation` + `Message`
(`app/models/conversation.py`) with a `ConversationRepository`; read-write APIs
(`routes/assistant.py`): `POST /assistant/ask` (VIEWER, audited), `GET
/assistant/conversations{,/{id}}`. Four screens: Assistant Workspace, conversation
thread, Conversation History, Evidence Viewer (+ reusable `assistant-answer.tsx`). TS
contracts (`assistant.ts`). Added ADR-0019. **No new datastore** (conversations live in
PostgreSQL); **no model provider** — answers are deterministic.

Gates: API `ruff` clean · `mypy app` clean (113 files) · `pytest` **138/138**. Web
`lint` · `typecheck` · `build` all green (routes incl. /assistant, /assistant/[id],
/assistant/[id]/evidence, /assistant/history).

## How to run it

```bash
docker compose -f infra/docker-compose.yml up -d          # PG + Neo4j + Qdrant
cd apps/api && uvicorn app.main:app --reload              # API on :8000 (auto-creates PG schema in dev)
cd apps/web && npm run dev                                # Web on :3000
```

Flow to exercise: add a GitHub connector → Run sync → Run processing → Build graph →
Embed corpus → open **Assistant**, ask "How does <service> work?" / "Who owns <X>?" /
"What caused the incident?" → read the answer with per-citation trust → open **Evidence**
(all cited sources ranked by trust, each linking to the **Trust Inspector**) → revisit via
**Conversation History**. Dev auth: web client sends `X-Tenant-Id`/`X-Role` headers.

## Active decisions / constraints to remember

- The assistant is **deterministic and composed, not generative** (ADR-0019): no model
  provider. Intent is keyword-classified; answers are extractive/templated; overall
  confidence is the **mean of the cited documents' Phase-5 trust** (every answer carries
  trust). Intent/composer are seams for a later LLM-backed upgrade.
- **Conversations are persisted** (PostgreSQL `Conversation`/`Message`); an assistant
  message stores a JSON `answer_json` snapshot so history is faithful even as the corpus
  changes. The Evidence Viewer links citations to the live Trust Inspector.
- Graph enrichment is **bounded to one neighborhood** (the top matched entity) — no
  multi-hop reasoning yet. Trust profiles are fetched once per unique cited document.
- `ask` is VIEWER-gated (reading knowledge) and audited; it runs synchronously in-request.
- Keep files < 300 lines; one concern per file. Python schemas authoritative; TS
  `packages/contracts` mirror them.

## Next step (after gate approval)

Phase 7 — Engineering Intelligence: dependency intelligence, technical-debt intelligence,
incident intelligence, ownership intelligence over the graph + trust + assistant layers.
Screens: Intelligence Dashboard, Technical Debt Dashboard, Dependency Risk Dashboard. See
[`roadmap.md`](roadmap.md) Phase 7.
