export type IntentLabel = "trend" | "sentiment" | "competitor" | "unknown";

export interface SessionEvent {
  type: "session";
  session_id: string;
}

export interface StepEvent {
  type: "step";
  node: string;
  status: "started" | "completed";
  used_demo?: boolean;
  summary?: string;
}

export interface KeyStats {
  post_count: number;
  avg_sentiment: number;
  positive_pct: number;
  negative_pct: number;
}

export interface SourceCitation {
  title: string;
  url: string;
  sentiment: "positive" | "negative" | "neutral";
}

export interface PostSentiment {
  title: string;
  compound: number;
  score: number;
  num_comments: number;
  weight: number;
  url: string;
}

export interface SentimentResult {
  raw_scores: number[];
  weighted_avg: number;
  label: "positive" | "negative" | "neutral";
  post_count: number;
  positive_pct: number;
  negative_pct: number;
  top_posts: PostSentiment[];
}

export interface SynthesisPayload {
  headline: string;
  summary: string;
  sentiment_label: "positive" | "negative" | "mixed" | "neutral";
  key_stats: KeyStats;
  recommendations: string[];
  sources: SourceCitation[];
  sentiment: SentimentResult;
}

export interface CompanyPayload {
  name: string;
  description: string | null;
  employees: number | null;
  estimated_revenue: string | null;
  total_funding: string | null;
  source: string;
}

export interface ClarifyPayload {
  message: string;
}

export type ResultPayload = SynthesisPayload | CompanyPayload | ClarifyPayload;

export interface ResultEvent {
  type: "result";
  intent: IntentLabel;
  payload: ResultPayload;
  demo_flags: Record<string, boolean>;
}

export interface ErrorEvent {
  type: "error";
  node: string;
  message: string;
}

export interface DoneEvent {
  type: "done";
}

export type ChatStreamEvent = SessionEvent | StepEvent | ResultEvent | ErrorEvent | DoneEvent;

export interface ChatMessageOut {
  role: "user" | "assistant";
  content: string;
  intent: string | null;
  used_demo_data: boolean;
  created_at: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  messages: ChatMessageOut[];
}

export interface StepState {
  node: string;
  status: "pending" | "started" | "completed";
  used_demo: boolean;
  summary: string;
}

export interface ConversationTurn {
  id: string;
  userMessage: string;
  steps: StepState[];
  result: ResultEvent | null;
  errors: ErrorEvent[];
  status: "streaming" | "done" | "error";
  errorMessage?: string;
}

export type ServiceStatus = "configured" | "demo" | "disabled";

export interface HealthResponse {
  status: string;
  services: Record<string, ServiceStatus>;
}

export function isSynthesisPayload(payload: ResultPayload): payload is SynthesisPayload {
  return "headline" in payload;
}

export function isCompanyPayload(payload: ResultPayload): payload is CompanyPayload {
  return "name" in payload && "source" in payload;
}
