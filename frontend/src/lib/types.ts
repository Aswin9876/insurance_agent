// Shared TypeScript types for the platform
export interface CustomerForm {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  age: string;
  gender: string;
  location: string;
  occupation: string;
  annual_income: string;
  marital_status: string;
  health_conditions: string;
  smoker: string;
  insurance_needs: string; // comma separated
  budget: string;
  consent_given: boolean;
}

export interface AgentTrace {
  agent: string;
  status: "success" | "fallback" | "blocked" | "skipped";
  latency_ms: number;
  message: string;
  attempts: number;
}

export interface RiskResult {
  risk_score: number;
  category: "low" | "medium" | "high" | "critical";
  confidence: number;
  factors: { weights: Record<string, number>; subscores: Record<string, number> };
  explanation: string;
}

export interface Recommendation {
  ranking: number;
  product_id: string;
  policy_name: string;
  match_score: number;
  premium: number;
  coverage_summary: string;
  summary?: string;
  score_breakdown?: {
    needs_fit: number; risk_fit: number; budget_fit: number; eligibility: number;
  };
}

export interface Explanation {
  ranking: number;
  policy_name: string;
  explanation: string;
  risk_explanation: string;
  coverage_comparison: string;
  generated_by: string;
}

export interface ComplianceReport {
  gdpr: {
    consent_given: boolean; lawful_basis: string;
    data_retention_days: number; right_to_erasure_supported: boolean;
  };
  pii_checks: { masking_applied_for_llm: boolean; warnings: string[] };
  violations: string[];
  status: "passed" | "blocked";
}

export interface CrmInfo {
  crm_id: string | null;
  existing_customer: boolean;
  previous_policies: Array<Record<string, unknown>>;
  claims_history: Array<Record<string, unknown>>;
  claims_count: number;
  total_claimed: number;
  loyalty_tier: string;
  degraded?: boolean;
}

export interface WorkflowSummary {
  run_id: string;
  status: "completed" | "blocked";
  customer: {
    name: string; age: number; location: string; occupation: string;
    income: number; marital_status: string; insurance_needs: string[];
    crm_id: string | null;
  };
  crm: CrmInfo;
  risk: RiskResult;
  compliance: ComplianceReport;
  recommendations: Recommendation[];
  explanations: Explanation[];
  trace: AgentTrace[];
  agent_status: Record<string, string>;
  errors: string[];
  completed_at: string;
}