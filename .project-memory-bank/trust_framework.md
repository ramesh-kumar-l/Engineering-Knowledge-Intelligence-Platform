# Trust Framework

Trust is EKIP's defining property. **Trust must be visible.** The platform earns
adoption by being transparent about where knowledge comes from and how reliable it is.

> Prefer transparent uncertainty over false confidence.

## Trust dimensions

Every AI-generated answer (and, where applicable, every retrieved result) must surface:

| Dimension | Question it answers | Source |
|---|---|---|
| **Sources** | Where did this come from? | Provenance of each chunk/entity |
| **Confidence** | How reliable is this answer? | Retrieval + model scoring |
| **Freshness** | How current is the underlying knowledge? | Last-synced timestamps |
| **Ownership** | Who owns / is accountable for this? | Graph `owns` relationships |
| **Supporting evidence** | What backs this claim? | Linked excerpts/documents |

## Requirements on the UI

The user must be able to understand, for any answer:

- **Why** the answer exists (the question/intent it addresses).
- **Where** it came from (clickable sources).
- **How reliable** it is (confidence + freshness, shown honestly).

Trust-UX components are first-class in the design system
([`ui_design_system.md`](ui_design_system.md)) and are exercised by the Trust Layer
(Phase 5) and Assistant (Phase 6): Trust Inspector, Source Explorer, Evidence Viewer.

## Principles

- Never present a low-confidence answer as authoritative.
- Always make sources reachable in one click.
- Always show freshness when knowledge can go stale.
- Attribute ownership from the knowledge graph, not from guesses.

## Observability of trust

Track over time (see [`testing_strategy.md`](testing_strategy.md) quality metrics):
retrieval quality, hallucination rate, knowledge coverage, answer confidence
calibration.
