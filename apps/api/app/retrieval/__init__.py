"""Retrieval layer (Phase 4).

Embeds processed chunks into a vector store and answers queries with hybrid
retrieval — keyword + vector over chunks, fused by reciprocal rank, plus a graph
facet of related entities. Embeddings are deterministic (ADR-0014) and the vector
store is abstracted behind a protocol (ADR-0015), so the whole layer runs offline in
tests, exactly as processing (ADR-0010) and the graph (ADR-0012) do.
"""
