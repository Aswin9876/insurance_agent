// 7-step onboarding wizard: Welcome → Personal → Employment → Health →
// Preferences → Consent → Results. Step validation + save progress
// (Zustand persist) + Framer Motion transitions.
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useOnboarding } from "@/store/onboarding";
import { runAgents } from "@/lib/api";
import type { WorkflowSummary } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Dashboard } from "@/components/dashboard/Dashboard";

const STEPS = [
  "Welcome", "Personal Info", "Employment", "Health",
  "Preferences", "Consent", "Results",
];

const OCCUPATIONS = [
  "software_engineer", "teacher", "nurse", "accountant", "consultant",
  "manager", "designer", "retail_worker", "construction", "truck_driver",
  "mining", "farmer",
];

export function Wizard() {
  const { form, step, setField, setStep, summary, setSummary, reset } =
    useOnboarding();
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState("");

  function validateStep(current: number): boolean {
    const e: Record<string, string> = {};
    if (current === 1) {
      if (!form.first_name.trim()) e.first_name = "First name is required";
      if (!form.last_name.trim()) e.last_name = "Last name is required";
      const age = Number(form.age);
      if (!form.age || Number.isNaN(age) || age < 18 || age > 100)
        e.age = "Age must be 18–100";
      if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
        e.email = "Invalid email";
      if (form.phone && !/^\+?[0-9][0-9\- ]{7,14}$/.test(form.phone))
        e.phone = "Invalid phone";
    }
    if (current === 2) {
      if (!form.occupation) e.occupation = "Occupation is required";
      const inc = Number(form.annual_income);
      if (!form.annual_income || Number.isNaN(inc) || inc <= 0)
        e.annual_income = "Valid annual income is required";
    }
    if (current === 3) {
      if (!form.gender) e.gender = "Gender is required";
      if (!form.location.trim()) e.location = "Location is required";
      if (!form.marital_status) e.marital_status = "Marital status is required";
    }
    if (current === 4) {
      if (!form.insurance_needs.trim())
        e.insurance_needs = "Select at least one need";
      const bud = Number(form.budget);
      if (form.budget && (Number.isNaN(bud) || bud < 0))
        e.budget = "Budget must be a positive number";
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function next() {
    if (validateStep(step)) setStep(step + 1);
  }
  function back() {
    setErrors({});
    setStep(step - 1);
  }

  async function launch() {
    setRunning(true);
    setRunError("");
    try {
      const payload = {
        ...form,
        age: Number(form.age),
        annual_income: Number(form.annual_income),
        budget: form.budget ? Number(form.budget) : undefined,
        consent_given: form.consent_given,
      };
      const res = await runAgents(payload);
      setSummary(res.summary as WorkflowSummary);
      setStep(6);
    } catch (err) {
      setRunError(
        (err as Error).message +
          " — make sure the backend is running on :8000 and you are signed in (demo@agent.ai / demo1234)."
      );
    } finally {
      setRunning(false);
    }
  }

  const slide = {
    initial: { opacity: 0, x: 24 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -24 },
    transition: { duration: 0.25 },
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      {/* Progress indicator */}
      <div className="mb-8">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-sm font-medium text-slate-600">
            Step {Math.min(step + 1, 7)} of 7 — {STEPS[step]}
          </span>
          {step < 6 && (
            <button
              className="text-xs text-slate-400 hover:text-slate-600"
              onClick={() => setStep(6)}
              title="Progress is saved automatically"
            >
              Progress auto-saved ✓
            </button>
          )}
        </div>
        <div className="flex gap-1.5">
          {STEPS.map((s, i) => (
            <div
              key={s}
              className={`h-1.5 flex-1 rounded-full transition-colors ${
                i <= step ? "bg-indigo-600" : "bg-slate-200"
              }`}
              title={s}
            />
          ))}
        </div>
      </div>

      <AnimatePresence mode="wait">
        {step === 0 && (
          <motion.div key="welcome" {...slide} className="text-center">
            <h1 className="mb-3 text-3xl font-bold">
              AI-Powered Insurance Onboarding
            </h1>
            <p className="mx-auto mb-8 max-w-xl text-slate-600">
              Six intelligent agents work together to validate your profile,
              check CRM history, assess your risk, verify compliance, and
              recommend the best policies — with full transparency.
            </p>
            <div className="mx-auto mb-8 grid max-w-lg grid-cols-3 gap-3 text-xs text-slate-500">
              {["Onboarding Agent", "CRM Agent", "Risk Agent", "Compliance Agent", "Recommendation Agent", "Explainability Agent"].map(
                (a) => (
                  <div key={a} className="rounded-lg border border-slate-200 bg-white px-2 py-3 shadow-sm">
                    🤖 {a.replace(" Agent", "")}
                  </div>
                )
              )}
            </div>
            <Button size="lg" onClick={() => setStep(1)}>
              Start Onboarding →
            </Button>
          </motion.div>
        )}

        {step === 1 && (
          <motion.div key="personal" {...slide}>
            <h2 className="mb-4 text-xl font-semibold">Personal Information</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="First Name" required value={form.first_name}
                error={errors.first_name}
                onChange={(e) => setField("first_name", e.target.value)} />
              <Input label="Last Name" required value={form.last_name}
                error={errors.last_name}
                onChange={(e) => setField("last_name", e.target.value)} />
              <Input label="Age" required type="number" value={form.age}
                error={errors.age} hint="18–100"
                onChange={(e) => setField("age", e.target.value)} />
              <Input label="Email" type="email" value={form.email}
                error={errors.email} hint="Masked before AI processing"
                onChange={(e) => setField("email", e.target.value)} />
              <Input label="Phone" value={form.phone} error={errors.phone}
                hint="e.g. +1-555-123-4567"
                onChange={(e) => setField("phone", e.target.value)} />
            </div>
            <NavButtons onBack={back} onNext={next} />
          </motion.div>
        )}

        {step === 2 && (
          <motion.div key="employment" {...slide}>
            <h2 className="mb-4 text-xl font-semibold">Employment Information</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Select label="Occupation" required value={form.occupation}
                error={errors.occupation}
                onChange={(e) => setField("occupation", e.target.value)}
                options={OCCUPATIONS.map((o) => ({
                  value: o,
                  label: o.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
                }))} />
              <Input label="Annual Income ($)" required type="number"
                value={form.annual_income} error={errors.annual_income}
                onChange={(e) => setField("annual_income", e.target.value)} />
            </div>
            <NavButtons onBack={back} onNext={next} />
          </motion.div>
        )}

        {step === 3 && (
          <motion.div key="health" {...slide}>
            <h2 className="mb-4 text-xl font-semibold">Health Information</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Select label="Gender" required value={form.gender}
                error={errors.gender}
                onChange={(e) => setField("gender", e.target.value)}
                options={[{ value: "male", label: "Male" }, { value: "female", label: "Female" }]} />
              <Select label="Marital Status" required value={form.marital_status}
                error={errors.marital_status}
                onChange={(e) => setField("marital_status", e.target.value)}
                options={[{ value: "single", label: "Single" }, { value: "married", label: "Married" }]} />
              <div className="sm:col-span-2">
                <Input label="Location" required value={form.location}
                  error={errors.location} hint="City, State"
                  onChange={(e) => setField("location", e.target.value)} />
              </div>
              <div className="sm:col-span-2">
                <Input label="Existing Health Conditions"
                  value={form.health_conditions}
                  hint="Comma separated: asthma, diabetes, heart_disease, hypertension… (leave empty if none)"
                  onChange={(e) => setField("health_conditions", e.target.value)} />
              </div>
              <Select label="Smoker" value={form.smoker}
                onChange={(e) => setField("smoker", e.target.value)}
                options={[{ value: "no", label: "No" }, { value: "yes", label: "Yes" }]} />
            </div>
            <NavButtons onBack={back} onNext={next} />
          </motion.div>
        )}

        {step === 4 && (
          <motion.div key="preferences" {...slide}>
            <h2 className="mb-4 text-xl font-semibold">Insurance Preferences</h2>
            <p className="mb-4 text-sm text-slate-500">
              Select what you need coverage for (comma separated):
            </p>
            <div className="mb-4 flex flex-wrap gap-2">
              {["health", "life", "auto", "home"].map((n) => {
                const needs = form.insurance_needs
                  .split(",").map((s) => s.trim()).filter(Boolean);
                const active = needs.includes(n);
                return (
                  <button
                    key={n}
                    onClick={() =>
                      setField(
                        "insurance_needs",
                        active ? needs.filter((x) => x !== n).join(", ")
                               : [...needs, n].join(", ")
                      )
                    }
                    className={`rounded-full border px-4 py-1.5 text-sm font-medium transition
                      ${active ? "border-indigo-600 bg-indigo-600 text-white"
                               : "border-slate-300 bg-white hover:border-indigo-400"}`}
                  >
                    {n.charAt(0).toUpperCase() + n.slice(1)}
                  </button>
                );
              })}
            </div>
            {errors.insurance_needs && (
              <p className="mb-3 text-xs text-red-600">{errors.insurance_needs}</p>
            )}
            <Input label="Annual Budget ($)" type="number" value={form.budget}
              error={errors.budget}
              hint="Optional — defaults to ~5% of income"
              onChange={(e) => setField("budget", e.target.value)} />
            <NavButtons onBack={back} onNext={next} />
          </motion.div>
        )}

        {step === 5 && (
          <motion.div key="consent" {...slide}>
            <h2 className="mb-4 text-xl font-semibold">Consent (GDPR)</h2>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              <p className="mb-2 font-medium text-slate-700">Data processing consent</p>
              <ul className="mb-3 list-disc space-y-1 pl-5">
                <li>Your data is processed to assess risk and recommend policies.</li>
                <li>PII (email, phone, address) is masked before any AI processing.</li>
                <li>All agent actions are audit-logged.</li>
                <li>You may request erasure at any time (right to be forgotten).</li>
              </ul>
              <label className="flex cursor-pointer items-center gap-2 font-medium text-slate-800">
                <input type="checkbox" className="h-4 w-4 accent-indigo-600"
                  checked={form.consent_given}
                  onChange={(e) => setField("consent_given", e.target.checked)} />
                I consent to the processing of my data
              </label>
              {!form.consent_given && (
                <p className="mt-2 text-xs text-red-500">
                  The Compliance Agent will block the workflow without consent.
                </p>
              )}
            </div>
            <div className="mt-6 flex items-center justify-between">
              <Button variant="outline" onClick={back}>← Back</Button>
              <Button onClick={() => { setErrors({}); launch(); }}
                disabled={running || !form.consent_given}>
                {running ? "Running 6 agents…" : "🚀 Run AI Agents"}
              </Button>
            </div>
            {runError && (
              <p className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">
                {runError}
              </p>
            )}
          </motion.div>
        )}

        {step === 6 && (
          <motion.div key="results" {...slide}>
            {summary ? (
              <>
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-xl font-semibold">Results</h2>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => { reset(); setStep(0); }}>
                      New Onboarding
                    </Button>
                  </div>
                </div>
                {summary.status === "blocked" && (
                  <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4">
                    <p className="font-semibold text-red-700">
                      ⛔ Workflow blocked by Compliance Agent
                    </p>
                    <ul className="mt-1 list-disc pl-5 text-sm text-red-600">
                      {summary.compliance.violations.map((v) => (
                        <li key={v}>{v}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <Dashboard summary={summary} />
              </>
            ) : (
              <p>No results yet.</p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function NavButtons({ onBack, onNext }: { onBack: () => void; onNext: () => void }) {
  return (
    <div className="mt-6 flex items-center justify-between">
      <Button variant="outline" onClick={onBack}>← Back</Button>
      <Button onClick={onNext}>Continue →</Button>
    </div>
  );
}