/** Agent Layer contracts — mirror apps/api/app/domain/agents.py. */
import type { SourceType } from "./connectors";
import type { ConfidenceBand, FreshnessBand } from "./trust";
import type { RiskBand } from "./intelligence";
import type { SyncStatus } from "./sync";

export type AgentType = "incident" | "onboarding" | "architecture" | "maintenance";

export type AgentStepStatus = "ok" | "empty" | "failed";

export interface AgentTypeInfo {
  type: AgentType;
  label: string;
  description: string;
  needs_target: boolean;
  target_hint: string;
}

export interface AgentCatalogResponse {
  agents: AgentTypeInfo[];
}

export interface RunAgentRequest {
  agent_type: AgentType;
  target?: string | null;
}

export interface AgentEvidence {
  document_id: string;
  title: string;
  source_type: SourceType;
  url: string | null;
  snippet: string;
  confidence: number;
  confidence_band: ConfidenceBand;
  freshness_band: FreshnessBand;
  age_days: number | null;
  owners: string[];
  ownership_known: boolean;
}

export interface AgentFinding {
  label: string;
  detail: string;
  severity: RiskBand | null;
  refs: string[];
}

export interface AgentAction {
  action: string;
  priority: RiskBand;
  rationale: string;
}

export interface ResultBody {
  headline: string;
  confidence: number;
  confidence_band: ConfidenceBand;
  findings: AgentFinding[];
  actions: AgentAction[];
  evidence: AgentEvidence[];
}

export interface AgentStep {
  ordinal: number;
  name: string;
  status: AgentStepStatus;
  summary: string;
  detail: Record<string, unknown> | null;
}

export interface AgentRunSummary {
  id: string;
  agent_type: AgentType;
  target: string | null;
  title: string;
  status: SyncStatus;
  confidence: number | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  step_count: number;
}

export interface AgentRunListResponse {
  runs: AgentRunSummary[];
}

export interface AgentRunDetailResponse {
  run: AgentRunSummary;
  result: ResultBody | null;
  steps: AgentStep[];
}
