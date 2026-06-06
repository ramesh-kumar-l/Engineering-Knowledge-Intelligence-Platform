"""Knowledge processing pipeline (Phase 2).

Pure, deterministic, dependency-light steps — parse, chunk, classify, enrich,
summarize — composed by :func:`app.processing.pipeline.process`. Determinism keeps
the layer testable without external model providers; each step is a small module so
an LLM-backed implementation can replace it later behind the same interface.
"""
