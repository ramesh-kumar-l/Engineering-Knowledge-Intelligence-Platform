# packages/

Shared libraries used across `apps/` (ADR-0005).

| Package | Purpose |
|---|---|
| `contracts` | TypeScript API contract types mirroring the backend Pydantic schemas. Single source of truth that prevents Python/TS drift (risk R2). |

Future: shared API client and design tokens (see `ui_design_system.md`).

Type-only packages are consumed via TypeScript path aliases (no build step); the types
are erased at compile time.
