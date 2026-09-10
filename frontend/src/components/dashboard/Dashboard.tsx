// Result dashboard: customer summary, risk gauge, agent execution
// timeline, workflow trace, recommendations + reasoning, compliance.
import { motion } from "framer-motion";
import type { AgentTrace, Explanation, Recommendation, RiskResult, WorkflowSummary } from "@/lib/types";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const AGENT_LABELS: Record<string, string> = {
  onboarding_agent: "1 · Onboarding",
  crm_agent: "2 · CRM",
  risk_agent: "3 · Risk",
  compliance_agent: "4 · Compliance",
  recommendation_agent: "5 · Recommendation",
  explainability_agent: "6 · Explainability",
  aggregate: "· Aggregate",
};

export function Dashboard({ summary }: { summary: WorkflowSummary }) {
  return (
    <div className="space-y-5">
      {/* Top row: customer + risk gauge */}
      <div className="grid gap-5 md:grid-cols-3">
        <Card className="md:col-span-1">
          <CardHeader title="Customer Summary" />
          <CardBody className="space-y-2 text-sm">
            <Row k="Name" v={summary.customer.name || "—"} />
            <Row k="Age" v={String(summary.customer.age ?? "—")} />
            <Row k="Location" v={summary.customer.location} />
            <Row k="Occupation" v={summary.customer.occupation?.replace(/_/g, " ")} />
            <Row k="Income" v={fmtMoney(summary.customer.income)} />
            <Row k="Marital" v={summary.customer.marital_status} />
            <Row k="Needs" v={(summary.customer.insurance_needs || []).join(", ")} />
            <Row k="CRM ID" v={summary.customer.crm_id || "new customer"} />
            {summary.crm.existing_customer && (
              <div className="pt-1">
                <Badge tone="info">
                  {summary.crm.loyalty_tier} tier · {summary.crm.claims_count} claims ·{" "}
                  {summary.crm.previous_policies.length} prior policies
                </Badge>
              </div>
            )}
          </CardBody>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader title="Risk Assessment"
            subtitle={`Confidence ${(summary.risk.confidence * 100).toFixed(0)}% · deterministic weighted scoring`} />
          <CardBody className="flex flex-col items-center gap-4 sm:flex-row">
            <RiskGauge risk={summary.risk} />
            <div className="flex-1 text-sm">
              <Badge tone={summary.risk.category}>{summary.risk.category.toUpperCase()} RISK</Badge>
              <p className="mt-3 text-slate-600">{summary.risk.explanation}</p>
              {summary.risk.factors?.subscores &&
                Object.keys(summary.risk.factors.subscores).length > 0 && (
                  <div className="mt-3 space-y-1.5">
                    {Object.entries(summary.risk.factors.subscores).map(([k, v]) => (
                      <div key={k} className="flex items-center gap-2 text-xs">
                        <span className="w-20 capitalize text-slate-500">{k}</span>
                        <div className="h-1.5 flex-1 rounded-full bg-slate-100">
                          <motion.div
                            className="h-1.5 rounded-full bg-indigo-500"
                            initial={{ width: 0 }}
                            animate={{ width: `${v}%` }}
                            transition={{ duration: 0.6 }}
                          />
                        </div>
                        <span className="w-8 text-right text-slate-400">{Math.round(v)}</span>
                      </div>
                    ))}
                  </div>
                )}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Agent execution status + trace */}
      <Card>
        <CardHeader title="Agent Execution & Workflow Trace"
          subtitle={`Run ${summary.run_id} · ${summary.trace.reduce((a, t) => a + t.latency_ms, 0)}ms total`} />
        <CardBody className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {summary.trace.map((t, i) => (
            <TraceCard key={i} trace={t} />
          ))}
        </CardBody>
      </Card>

      {/* Recommendations + reasoning */}
      <Card>
        <CardHeader title="Recommended Policies" subtitle="Top 3 matches by weighted scoring" />
        <CardBody className="space-y-4">
          {summary.recommendations.length === 0 && (
            <p className="text-sm text-slate-500">No recommendations (workflow blocked).</p>
          )}
          {summary.recommendations.map((rec) => (
            <PolicyCard key={rec.product_id} rec={rec}
              explanation={summary.explanations.find((e) => e.ranking === rec.ranking)} />
          ))}
        </CardBody>
      </Card>

      {/* Compliance */}
      <Card>
        <CardHeader title="Compliance & GDPR" />
        <CardBody className="text-sm">
          <div className="mb-3 flex items-center gap-3">
            <Badge tone={summary.compliance.status === "passed" ? "success" : "blocked"}>
              {summary.compliance.status === "passed" ? "✓ PASSED" : "⛔ BLOCKED"}
            </Badge>
            <span className="text-slate-500">
              Lawful basis: {summary.compliance.gdpr?.lawful_basis || "none"} ·
              retention {summary.compliance.gdpr?.data_retention_days ?? 0} days ·
              PII masked for LLM: {summary.compliance.pii_checks?.masking_applied_for_llm ? "yes" : "no"}
            </span>
          </div>
          {summary.compliance.violations?.length > 0 && (
            <ul className="list-disc pl-5 text-red-600">
              {summary.compliance.violations.map((v) => <li key={v}>{v}</li>)}
            </ul>
          )}
          {summary.errors.length > 0 && (
            <div className="mt-3 rounded-lg bg-amber-50 p-3 text-xs text-amber-700">
              <p className="mb-1 font-semibold">Recovered errors (auto-handled by supervisor):</p>
              <ul className="list-disc pl-4">{summary.errors.map((e) => <li key={e}>{e}</li>)}</ul>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}

function TraceCard({ trace }: { trace: AgentTrace }) {
  const tone = trace.status === "success" ? "success" : trace.status;
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      className="rounded-lg border border-slate-200 p-3"
    >
      <div className="mb-1 flex items-center justify-between">
        <span className="text-sm font-medium">
          {AGENT_LABELS[trace.agent] || trace.agent}
        </span>
        <Badge tone={tone}>{trace.status}</Badge>
      </div>
      <p className="text-xs text-slate-500">{trace.message}</p>
      <p className="mt-1 text-[10px] text-slate-400">
        {trace.latency_ms}ms · attempts: {trace.attempts}
      </p>
    </motion.div>
  );
}

function PolicyCard({ rec, explanation }: { rec: Recommendation; explanation?: Explanation }) {
  const bd = rec.score_breakdown;
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className={`rounded-xl border p-4 ${rec.ranking === 1 ? "border-indigo-300 bg-indigo-50/40" : "border-slate-200"}`}
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className={`flex h-7 w-7 items-center justify-center rounded-full text-sm font-bold
            ${rec.ranking === 1 ? "bg-indigo-600 text-white" : "bg-slate-200 text-slate-600"}`}>
            {rec.ranking}
          </span>
          <span className="font-semibold">{rec.policy_name}</span>
          {rec.ranking === 1 && <Badge tone="info">BEST MATCH</Badge>}
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="font-semibold text-indigo-700">{rec.match_score}% match</span>
          <span className="text-slate-600">{fmtMoney(rec.premium)}/yr</span>
        </div>
      </div>
      <p className="text-sm text-slate-600">{rec.coverage_summary}</p>
      {bd && (
        <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-500">
          <Chip label="needs" v={bd.needs_fit} />
          <Chip label="risk" v={bd.risk_fit} />
          <Chip label="budget" v={bd.budget_fit} />
        </div>
      )}
      {explanation && (
        <div className="mt-3 rounded-lg bg-slate-50 p-3 text-sm">
          <p className="text-slate-700">💬 {explanation.explanation}</p>
          {explanation.coverage_comparison && (
            <p className="mt-1 text-xs text-slate-500">{explanation.coverage_comparison}</p>
          )}
          <p className="mt-1 text-[10px] text-slate-400">generated by: {explanation.generated_by}</p>
        </div>
      )}
    </motion.div>
  );
}

function Chip({ label, v }: { label: string; v: number }) {
  return (
    <span className="rounded-full bg-slate-100 px-2 py-0.5">
      {label}: {Math.round(v)}
    </span>
  );
}

function RiskGauge({ risk }: { risk: RiskResult }) {
  const score = Math.max(0, Math.min(100, risk.risk_score));
  const colors: Record<string, string> = {
    low: "#10b981", medium: "#f59e0b", high: "#f97316", critical: "#ef4444",
  };
  const color = colors[risk.category] || "#6366f1";
  // Semicircle gauge SVG
  const r = 70;
  const circumference = Math.PI * r;
  const offset = circumference * (1 - score / 100);
  return (
    <div className="relative">
      <svg width="180" height="105" viewBox="0 0 180 105">
        <path d="M 20 95 A 70 70 0 0 1 160 95" fill="none" stroke="#e2e8f0" strokeWidth="14" strokeLinecap="round" />
        <motion.path
          d="M 20 95 A 70 70 0 0 1 160 95" fill="none" stroke={color} strokeWidth="14" strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center">
        <div className="text-3xl font-bold" style={{ color }}>{Math.round(score)}</div>
        <div className="text-[10px] uppercase tracking-wider text-slate-400">risk score</div>
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v?: string | number }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-slate-400">{k}</span>
      <span className="text-right font-medium text-slate-700">{v || "—"}</span>
    </div>
  );
}

function fmtMoney(n?: number | null): string {
  if (n === null || n === undefined) return "—";
  return `$${Number(n).toLocaleString()}`;
}