# Coding Standards

Standards apply once the code increment begins. They encode the project's engineering
principles: **simplicity first, surgical changes, goal-driven execution.**

## Python (backend — ADR-0002)

- **Formatting/linting:** `ruff` (lint) + `black`/`ruff format`. Zero lint errors in CI.
- **Typing:** full type hints; `mypy` (or pyright) clean. Public functions typed.
- **Models:** Pydantic for request/response and config; no untyped dicts at boundaries.
- **Style:** async I/O for network/DB; small focused functions; explicit over clever.
- **Structure:** modules per layer (see [`system_architecture.md`](system_architecture.md)).

## TypeScript / Frontend (ADR-0003)

- **Strict mode** TS; no `any` without justification.
- **Lint/format:** ESLint + Prettier; zero errors in CI.
- **Components:** functional, typed props; reuse shadcn/ui primitives; no duplicate
  trust-UX components ([`ui_design_system.md`](ui_design_system.md)).
- **Accessibility:** keyboard + ARIA required for interactive components.

## Engineering principles (all code)

1. **Simplicity first** — minimum code that solves the problem; no speculative
   abstraction, config, or error handling for impossible cases.
2. **Surgical changes** — touch only what the task requires; match existing style;
   don't refactor working code without justification.
3. **No silent tech debt** — document any debt in
   [`implementation_status.md`](implementation_status.md).
4. **Never break existing functionality** — build incrementally.

## Commits & PRs

- Conventional-style messages (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`).
- Small, reviewable PRs scoped to one concern.
- Every PR: tests pass, lint clean, memory bank updated if behavior/architecture
  changed.

## ADR rule

Every significant decision adds an ADR to
[`architecture_decisions.md`](architecture_decisions.md) (Context · Options · Decision
· Consequences).
