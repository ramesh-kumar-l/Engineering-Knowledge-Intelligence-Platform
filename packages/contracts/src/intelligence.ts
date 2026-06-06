/** Engineering Intelligence contracts — mirror apps/api/app/domain/intelligence.py. */
import type { SourceType } from "./connectors";
import type { EntityKind } from "./graph";
import type { ConfidenceBand, FreshnessBand } from "./trust";

export type RiskBand = "high" | "medium" | "low";

export interface NodeRef {
  key: string;
  name: string;
  kind: EntityKind;
}

// --- Dependencies ---

export interface DependencyNode {
  key: string;
  name: string;
  kind: EntityKind;
  fan_in: number;
  fan_out: number;
  in_cycle: boolean;
  risk_score: number;
  risk_band: RiskBand;
}

export interface DependencyCycle {
  members: NodeRef[];
}

export interface DependencyReportResponse {
  total_nodes: number;
  total_dependencies: number;
  cycle_count: number;
  by_risk: Record<string, number>;
  nodes: DependencyNode[];
  cycles: DependencyCycle[];
}

// --- Technical debt ---

export interface DebtItem {
  document_id: string;
  title: string;
  source_type: SourceType;
  url: string | null;
  confidence: number;
  confidence_band: ConfidenceBand;
  freshness_band: FreshnessBand;
  age_days: number | null;
  has_owner: boolean;
  severity_score: number;
  severity_band: RiskBand;
  reasons: string[];
}

export interface DebtReportResponse {
  total_documents: number;
  debt_count: number;
  by_reason: Record<string, number>;
  by_band: Record<string, number>;
  items: DebtItem[];
}

// --- Incidents ---

export interface IncidentInsight {
  key: string;
  name: string;
  url: string | null;
  resolved: boolean;
  impacted_count: number;
  impacted: NodeRef[];
}

export interface ImpactedComponent {
  key: string;
  name: string;
  kind: EntityKind;
  incident_count: number;
}

export interface IncidentReportResponse {
  total_incidents: number;
  resolved_count: number;
  unresolved_count: number;
  incidents: IncidentInsight[];
  impacted_components: ImpactedComponent[];
}

// --- Ownership ---

export interface OwnershipCoverage {
  kind: EntityKind;
  total: number;
  owned: number;
  unowned: number;
  coverage: number;
}

export interface OwnerLoad {
  key: string;
  name: string;
  kind: EntityKind;
  owned_count: number;
}

export interface OwnershipReportResponse {
  overall_total: number;
  overall_owned: number;
  overall_coverage: number;
  coverages: OwnershipCoverage[];
  orphans: NodeRef[];
  top_owners: OwnerLoad[];
}

// --- Overview ---

export interface OverviewResponse {
  dependency_high_risk: number;
  dependency_cycles: number;
  debt_count: number;
  debt_high: number;
  incidents_total: number;
  incidents_unresolved: number;
  ownership_coverage: number;
}
