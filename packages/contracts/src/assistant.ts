/** Assistant contracts — mirror apps/api/app/domain/assistant.py. */
import type { SourceType } from "./connectors";
import type { EntityKind, RelationshipType } from "./graph";
import type { ConfidenceBand, FreshnessBand, OwnerRef } from "./trust";

export type AssistantIntent =
  | "service"
  | "ownership"
  | "incident"
  | "architecture"
  | "general";

export type MessageRole = "user" | "assistant";

export interface Citation {
  document_id: string;
  title: string;
  source_type: SourceType;
  url: string | null;
  chunk_id: string | null;
  ordinal: number | null;
  snippet: string;
  confidence: number;
  confidence_band: ConfidenceBand;
  freshness_band: FreshnessBand;
  age_days: number | null;
  owners: OwnerRef[];
  ownership_known: boolean;
}

export interface AnswerEntity {
  key: string;
  kind: EntityKind;
  name: string;
  summary: string | null;
}

export interface RelatedFact {
  relation: RelationshipType;
  direction: string;
  kind: EntityKind;
  name: string;
  key: string;
}

export interface AnswerBody {
  intent: AssistantIntent;
  summary: string;
  key_points: string[];
  confidence: number;
  confidence_band: ConfidenceBand;
  citations: Citation[];
  entities: AnswerEntity[];
  relations: RelatedFact[];
}

export interface AskRequest {
  question: string;
  conversation_id?: string | null;
}

export interface AskResponse {
  conversation_id: string;
  message_id: string;
  answer: AnswerBody;
}

export interface AssistantMessage {
  id: string;
  role: MessageRole;
  content: string;
  created_at: string;
  answer: AnswerBody | null;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ConversationListResponse {
  conversations: ConversationSummary[];
}

export interface ConversationDetailResponse {
  conversation: ConversationSummary;
  messages: AssistantMessage[];
}
