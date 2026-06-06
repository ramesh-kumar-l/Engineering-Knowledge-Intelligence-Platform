# User Journeys

Documented journeys that screens must support. Each references personas from
[`user_personas.md`](user_personas.md). Each journey ends with **visible trust**
(sources, confidence, freshness, ownership — see
[`trust_framework.md`](trust_framework.md)).

---

## J1 — Understand a service

**Personas:** P1, P2, P4
**Flow:** Search/open a service → see what it does, its APIs, dependencies, and owner →
inspect supporting evidence and freshness.
**Realized by:** Global Search, Service Explorer, Knowledge Explorer, Assistant.

## J2 — Find an owner

**Personas:** P1, P3, P4
**Flow:** Identify a service/repo/API → see owning team/engineer with evidence →
contact path.
**Realized by:** Service Explorer, Team Explorer, Assistant.

## J3 — Investigate an incident

**Personas:** P4, P2
**Flow:** Open an incident → see impacted services (blast radius), dependencies, and
prior similar incidents/resolutions.
**Realized by:** Dependency Graph, Knowledge Explorer, Incident Intelligence, Assistant.

## J4 — Explain an architecture decision

**Personas:** P2, P5, P1
**Flow:** Ask "why was X chosen?" → get an explanation grounded in ADRs/docs with
sources and confidence.
**Realized by:** Assistant Workspace, Evidence Viewer, Source Explorer.

## J5 — Assess dependency / debt risk

**Personas:** P5, P3
**Flow:** Open a service/area → see dependency risk and technical debt signals over
time.
**Realized by:** Dependency Risk Dashboard, Technical Debt Dashboard, Intelligence
Dashboard.

## J6 — Onboard to a team/area

**Personas:** P1, P3
**Flow:** Pick a team/area → guided overview of its services, owners, key docs, and
recent incidents.
**Realized by:** Team Explorer, Knowledge Explorer, Assistant.

## J7 — Connect & sync a knowledge source

**Personas:** P3, P5 (admin)
**Flow:** Choose a connector → configure → run incremental sync → monitor logs/health.
**Realized by:** Connector Catalog, Connector Details, Sync Dashboard, Sync Logs.

See [`screen_inventory.md`](screen_inventory.md) for the screen-to-journey mapping.
