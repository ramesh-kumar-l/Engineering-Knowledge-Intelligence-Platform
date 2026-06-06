"""Knowledge graph layer (Phase 3).

Entities and relationships derived from ingested data (``builder``) and curated by
editors, persisted behind a store abstraction (``store`` protocol) with a Neo4j
implementation (``neo4j_store``) and an in-memory implementation for offline tests.
"""
