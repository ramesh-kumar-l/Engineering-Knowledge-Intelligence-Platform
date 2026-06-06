"""Engineering Intelligence (Phase 7, ADR-0020).

Read-only, deterministic analysis composed over the knowledge graph (Phase 3) and the
trust layer (Phase 5) — no new datastore and no model provider, the same posture as
``app/trust``. Four concerns, one pure module each:

- ``dependency`` — fan-in/out, blast-radius risk and cycles over ``depends_on`` edges;
- ``debt`` — technical-debt severity from low-confidence / stale / unowned documents;
- ``incident`` — incident impact and resolution over ``impacts``/``resolved`` edges;
- ``ownership`` — ownership coverage, orphaned components and owner concentration.

``IntelligenceService`` fetches the bounded inputs and delegates to these analyzers;
everything is computed on read, so there is nothing to persist or to go stale.
"""
