"""Trust layer (Phase 5).

Deterministic, read-time trust scoring over signals already in the system —
provenance (documents), processing/embedding state, and graph ownership. Confidence
and freshness are computed on read (no trust persistence), so a profile always
reflects current state. See ADR-0017/0018 and ``trust_framework.md``.
"""
