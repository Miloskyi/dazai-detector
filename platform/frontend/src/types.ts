// Mirrors platform/backend/schemas/models.py — keep both in sync.

export interface Alert {
  id: string;
  timestamp: string;
  amount: number;
  risk_score: number;
  risk_tier: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  dbscan_score: number;
  classifier_score: number;
}

export interface ShapFeature {
  feature: string;
  value: number;
  shap_value: number;
  direction: "increases" | "decreases";
}

export interface SignalComponent {
  score: number;
  weight: number;
  contribution: number;
}

export interface SignalBreakdown {
  classifier: SignalComponent;
  dbscan: SignalComponent;
  risk_score: number;
}

export interface AlertDetail extends Alert {
  features: Record<string, number>;
  shap_explanation: ShapFeature[];
  narrative: string;
  signal_breakdown: SignalBreakdown;
}

export interface AlertPage {
  items: Alert[];
  total: number;
  limit: number;
  offset: number;
}

export interface StatsSummary {
  total_alerts: number;
  total_flagged_amount: number;
  tier_distribution: Record<string, number>;
  by_hour: Record<string, number>;
  by_amount_bucket: Record<string, number>;
}

export interface TopAlert {
  id: string;
  amount: number;
  risk_score: number;
  risk_tier: string;
  narrative: string;
}

export interface Report {
  generated_at: string;
  tier_counts: Record<string, number>;
  total_flagged_amount: number;
  top_alerts: TopAlert[];
  patterns: {
    by_hour?: Record<string, number>;
    by_amount_bucket?: Record<string, number>;
  };
}

export interface ChatResponse {
  answer: string;
  intent: string;
  agent: string;
  sources: string[];
  ok: boolean;
}

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  sources?: string[];
  intent?: string;
  agent?: string;
  ok?: boolean;
  failed?: boolean;
}
