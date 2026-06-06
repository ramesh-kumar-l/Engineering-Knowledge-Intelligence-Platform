"""Engineering Assistant (Phase 6).

A deterministic question-answering layer that composes the existing capabilities —
hybrid retrieval (Phase 4) for evidence, the knowledge graph (Phase 3) for related
facts, and the trust layer (Phase 5) so every cited source carries confidence,
freshness and ownership. No external model provider (ADR-0019): intent is classified
and answers are assembled from retrieved material, never generated.
"""
