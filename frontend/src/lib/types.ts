// Mirrors backend/schemas.py. Field names come from the council itself.

export type AgentName = "valuation" | "risk" | "momentum";

export interface AgentFailure {
  category: string;
  message: string;
}

export interface BaseAssessment {
  ticker: string;
  evidence: string[];
  assumptions: string[];
  limitations: string[];
  reasoning: string;
}

export interface ValuationAssessment extends BaseAssessment {
  stance: string; // positive | neutral | negative | insufficient_evidence
}

export interface RiskAssessment extends BaseAssessment {
  risk_level: string; // low | moderate | high | insufficient_evidence
}

export interface MomentumAssessment extends BaseAssessment {
  stance: string;
}

export interface AgentResult<A> {
  agent: AgentName;
  status: "succeeded" | "failed";
  assessment: A | null;
  failure: AgentFailure | null;
}

export interface DisagreementReport {
  classification: string; // conflict | agent_failure | evidence_gap | no_conflict
  conflicting_agents: string[];
  failed_agents: string[];
  evidence_gaps: string[];
  explanation: string;
}

export interface EvidenceQualityReport {
  level: string; // complete | partial | poor
  usable_dimensions: string[];
  insufficient_dimensions: string[];
  failed_dimensions: string[];
  explanation: string;
}

export interface AgreementReport {
  classification: string; // aligned | conflicting | limited | unestablished
  directional_agents: string[];
  positive_agents: string[];
  negative_agents: string[];
  explanation: string;
}

export interface ExecutionReport {
  successful_agents: string[];
  failed_agents: string[];
  success_count: number;
  total_agents: number;
  reliability: string; // complete | partial | failed
  explanation: string;
}

export interface FinalOutlook {
  ticker: string;
  dimensions: Record<AgentName, string>;
  overall_outlook: string; // positive | negative | mixed | partial_directional | insufficient_evidence
  interpretation: string;
  evidence_quality: EvidenceQualityReport;
  analytical_agreement: AgreementReport;
  execution_reliability: ExecutionReport;
  disagreement: string;
  failed_agents: string[];
  evidence_gaps: string[];
}

export interface OHLCV {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
}

export interface MarketEvidence {
  ticker: string;
  company_name: string | null;
  sector: string | null;
  industry: string | null;
  currency: string | null;
  current_price: number | null;
  market_cap: number | null;
  trailing_pe: number | null;
  price_to_book: number | null;
  enterprise_to_ebitda: number | null;
  beta: number | null;
  debt_to_equity: number | null;
  history: OHLCV[];
  missing_fields: string[];
  fetched_at: string;
}

export interface MomentumIndicators {
  current_close: number | null;
  ma_20: number | null;
  ma_50: number | null;
  ma_200: number | null;
  price_change_20d_pct: number | null;
  price_change_50d_pct: number | null;
  average_volume_20d: number | null;
  latest_volume: number | null;
}

export interface AnalysisResponse {
  ticker: string;
  analyzed_at: string;
  duration_seconds: number;
  status: "complete" | "partial";
  model: string | null;
  final_outlook: FinalOutlook;
  agents: {
    valuation: AgentResult<ValuationAssessment>;
    risk: AgentResult<RiskAssessment>;
    momentum: AgentResult<MomentumAssessment>;
  };
  disagreement: DisagreementReport;
  evidence_quality: EvidenceQualityReport;
  analytical_agreement: AgreementReport;
  execution_reliability: ExecutionReport;
  market_evidence: MarketEvidence;
  momentum_indicators: MomentumIndicators | null;
  momentum_indicators_unavailable_reason: string | null;
  disclaimer: string;
}

export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  council_configured: boolean;
  model: string | null;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: {
    agent_failures?: Record<string, AgentFailure>;
    retry_after?: number;
    problems?: { field: string; message: string }[];
  };
}
