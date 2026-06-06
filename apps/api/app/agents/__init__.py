"""Agent layer (Phase 8, ADR-0021).

Deterministic, multi-step agents that compose the existing layers — retrieval
(Phase 4), the knowledge graph (Phase 3), trust (Phase 5) and intelligence (Phase 7)
— to accomplish a goal (triage an incident, onboard onto a component, review an
architecture, surface knowledge debt). No model provider: every agent is a fixed,
auditable plan whose steps and conclusions are persisted for the Execution Viewer and
Audit Trail. One pure planner per agent; ``agent_service`` orchestrates and persists.
"""
