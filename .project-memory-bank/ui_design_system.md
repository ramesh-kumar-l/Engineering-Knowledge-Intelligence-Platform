# UI Design System

UI is a **first-class capability**. Every phase ships usable UI — never "backend
first, UI later".

## Design principles

- **Premium & enterprise-grade** — polished, credible, trustworthy.
- **Minimal cognitive load** — information-dense but never cluttered.
- **Dark-mode first** — light mode supported.
- **Accessible** — WCAG-compliant: contrast, keyboard nav, focus states, ARIA.
- **Mobile responsive** — usable across breakpoints.
- **Fast navigation** — keyboard-friendly, command palette later.

## Inspiration tier

Linear · GitHub · Datadog · Stripe · Vercel · Notion.

## Avoid

Dashboard clutter · excessive animation · decorative visuals · information overload ·
vanity metrics · generic dashboards.

## Optimize for

Trust · productivity · explainability · discoverability.

## Implementation (ADR-0003)

- **Framework:** Next.js (App Router) + React + TypeScript.
- **Styling:** Tailwind CSS with a tokenized theme (color, spacing, typography,
  radius) — dark mode as the default token set.
- **Components:** shadcn/ui (owned, themeable primitives) extended with EKIP
  trust-UX components.
- **Shared design tokens** live in `packages/` so backend-driven and frontend
  rendering stay consistent.

## Trust-UX components (first-class)

Per [`trust_framework.md`](trust_framework.md), recurring components must exist for:

- **Source chips / citations** — clickable provenance on any answer.
- **Confidence indicator** — honest, non-deceptive (no fake certainty).
- **Freshness badge** — "synced N ago" / staleness warning.
- **Ownership badge** — owning team/engineer from the graph.
- **Evidence panel** — supporting excerpts behind a claim.

These are exercised by Trust Inspector, Source Explorer, and Evidence Viewer
([`screen_inventory.md`](screen_inventory.md)).

## Governance

Update this file, [`user_journeys.md`](user_journeys.md), and
[`screen_inventory.md`](screen_inventory.md) for every significant UI change.
