# 🤖 AI Multi-Agent Insurance Onboarding & Policy Recommendation Platform

An end-to-end AI platform where **6 specialized agents** — orchestrated by a
**LangGraph Supervisor** — onboard customers, assess risk, verify compliance,
and explain personalized policy recommendations. Built for demo-readiness:
**SQLite, no external services required, works fully offline** (LLM optional).

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for diagrams.

---

## 🏗 Architecture

```
┌──────────────────────────────────┐       ┌──────────────────────────────────────┐
│   FRONTEND  (Next.js :3000)      │       │   BACKEND  (FastAPI :8000)           │
│                                  │       │                                      │
│  7-Step Onboarding Wizard        │       │  ┌────────────────────────────────┐  │
│  Result Dashboard                │ HTTP  │  │  SUPERVISOR AGENT (LangGraph)  │  │
│  Risk Gauge (animated SVG)       │──────▶│  │  routing · retry ×3 · fallback │  │
│  Agent Timeline & Trace          │  JWT  │  └───────────────┬────────────────┘  │
│  AI Chat Assistant (guardrails)  │       │                  │                   │
│  NextAuth (credentials + JWT)    │       │   1 Onboarding ──▶ 2 CRM ──▶ 3 Risk  │
│  Zustand (progress auto-save)    │       │        └── gate ──▶ 4 Compliance     │
└──────────────────────────────────┘       │             │ pass                   │
                                           │             ▼                        │
        TCS GenAI Lab LLM (optional)       │   5 Recommendation ──▶ 6 Explain     │
        https://genailab.tcs.in  ◀─────────│──  PII-masked prompts   │            │
                                           │                         ▼            │
        Mock CRM (synthetic JSON)  ◀───────│── /crm/*     7 Aggregate ──▶ SQLite  │
                                           └──────────────────────────────────────┘
```

### Agent Workflow (LangGraph StateGraph)

```
customer_input
    ▼
[Onboarding Agent]──✗ invalid/injection ──▶ [Aggregate] (blocked summary)
    ▼ ok
[CRM Agent]  ── mock CRM lookup: prior policies, claims, loyalty tier
    ▼
[Risk Agent] ── weighted score: age 25 · health 25 · claims 20 · occupation 15 · lifestyle 15
    ▼
[Compliance Agent] ──✗ consent/missing fields ──▶ [Aggregate] (blocked summary)
    ▼ pass
[Recommendation Agent] ── weighted match: needs 40 · risk-fit 25 · budget 20 · eligibility 15
    ▼
[Explainability Agent] ── LLM (GenAI Lab) or deterministic template
    ▼
[Aggregate] ──▶ summary { risk, recommendations, explanations, trace, compliance }
```

**Error recovery:** every agent node is wrapped by the supervisor —
log → retry ×3 → deterministic fallback → continue. Compliance/input errors
fail fast (retrying can't fix bad input).

---

## ⚡ Quick Start

### 1. Backend (FastAPI + SQLite + LangGraph)

```bash
pip install -r backend/requirements.txt
python backend/seed.py                 # 100 synthetic customers + CRM data + demo user
python -m uvicorn backend.main:app --reload --port 8000
```

Interactive API docs: **http://localhost:8000/docs**

### 2. Frontend (Next.js + Tailwind + Framer Motion)

```bash
cd frontend
npm install
npm run dev        # → http://localhost:3000
```

### 3. Sign in

Demo account (pre-filled in the login dialog):

| Email           | Password   |
|-----------------|------------|
| `demo@agent.ai` | `demo1234` |

### 4. Optional — enable the LLM (TCS GenAI Lab)

Put the event-provided key in `.env` (project root):

```env
OPENAI_API_KEY=<your-key>
LLM_BASE_URL=https://genailab.tcs.in
LLM_MODEL=azure_ai/genailab-maas-DeepSeek-V3-0324
LLM_VERIFY_SSL=false
```

Restart the backend. The Explainability Agent and Chat Assistant then use the
LLM (DeepSeek-V3). **Without a key everything still works** via deterministic
templates — the demo can never break.

---

## 📁 Folder Structure

```
insurance_agent/
├── backend/
│   ├── main.py                  # FastAPI app (CORS, routers, health)
│   ├── seed.py                  # synthetic data generator + DB seeder
│   ├── requirements.txt
│   ├── app/
│   │   ├── config.py            # env settings (LLM base URL/model/key)
│   │   ├── database.py          # SQLAlchemy engine (SQLite)
│   │   ├── models.py            # Users, Customers, Policies, Recommendations,
│   │   │                        # RiskAssessments, AuditLogs, WorkflowRuns
│   │   ├── agents/
│   │   │   ├── state.py         # LangGraph WorkflowState TypedDict
│   │   │   ├── guardrails.py    # validation · injection · PII · SQL/XSS
│   │   │   ├── onboarding_agent.py
│   │   │   ├── crm_agent.py
│   │   │   ├── risk_agent.py
│   │   │   ├── compliance_agent.py
│   │   │   ├── recommendation_agent.py
│   │   │   ├── explainability_agent.py
│   │   │   └── supervisor_agent.py   # LangGraph graph + retries + fallbacks
│   │   ├── routes/              # auth · agents · crm · misc (policies/chat)
│   │   └── services/            # crm_mock · chat_service · llm · error_handler
│   ├── data/                    # policy_catalog.json · synthetic_customers.json
│   │                            # crm_customers.json · crm_policies.json · crm_claims.json
│   └── tests/                   # pytest: unit + integration (90% coverage)
├── frontend/
│   ├── src/
│   │   ├── components/          # Wizard · Dashboard · ChatAssistant · ui/*
│   │   ├── store/onboarding.ts  # Zustand + localStorage persistence
│   │   ├── lib/                 # api client · shared types
│   │   └── pages/               # index + NextAuth route
│   └── src/__tests__/           # jest unit tests
├── docker-compose.yml           # optional one-command demo
├── .env                         # LLM key / base URL / model
└── pytest.ini
```

---

## 🔌 API Documentation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Credentials login → JWT |
| GET | `/api/auth/me` | Current user (Bearer) |
| POST | `/api/agents/run` | **Run the full 6-agent workflow** (Bearer) |
| GET | `/api/agents/runs/{run_id}` | Fetch a stored run summary (Bearer) |
| GET | `/api/agents/runs/{run_id}/logs` | Audit logs for a run (Bearer) |
| POST | `/api/onboarding/validate` | Guardrail pre-flight validation |
| GET | `/api/policies` | 8-product catalog |
| POST | `/api/chat` | AI assistant (guardrails + LLM/rules) |
| GET | `/crm/customer/{id}` | Mock CRM customer (e.g. `CUST-0001`) |
| GET | `/crm/policies/{id}` | Mock CRM prior policies |
| GET | `/crm/claims/{id}` | Mock CRM claims history |

Example run:

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@agent.ai","password":"demo1234"}' | jq -r .access_token)

curl -s -X POST localhost:8000/api/agents/run \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"customer":{"first_name":"Sarah","last_name":"Connor","email":"sarah@example.com",
       "age":34,"gender":"female","location":"Austin, TX","occupation":"software_engineer",
       "annual_income":85000,"marital_status":"married","health_conditions":"asthma",
       "smoker":"no","insurance_needs":"health,life","budget":9000,"consent_given":true}}'
```

---

## 🛡 Guardrails & Security

| Layer | Implementation |
|-------|----------------|
| Input validation | Required fields, age 18–100, email/phone regex, income bounds |
| Prompt injection | 11 regex patterns (ignore instructions, reveal prompt, jailbreak, DAN…) → rejected at onboarding + chat |
| PII protection | Emails/phones masked before any LLM call (`mask_pii`, `mask_customer`) |
| SQL/XSS | Free-text sanitization; SQLAlchemy parameterized queries |
| Auth | JWT bearer on all agent-run endpoints |
| GDPR | Consent gate, retention policy, right-to-erasure flags, full audit logs |

## 📊 Observability

- Structured console logs per agent per run (`[run=…][agent]`)
- `AuditLogs` table + `/runs/{id}/logs` endpoint
- Dashboard shows agent status (success/fallback/blocked), latency, attempts,
  recovered errors, compliance report, and the full workflow trace

---

## 🧪 Testing

```bash
# Backend — unit (risk, recommendation, compliance, guardrails, onboarding, CRM)
#           + integration (workflow, fallbacks, API, chat) — 90% coverage
python -m pytest backend/tests --cov=backend/app --cov-report=term

# Frontend — jest (store + wizard validation)
cd frontend && npm test
```

**Demo script for error-recovery:** set `CRM_FAILURE_RATE=1.0`, restart the
backend, run onboarding — the CRM agent fails ×3, the supervisor swaps in the
fallback CRM response and the workflow still completes (visible on the dashboard).

---

## 🐳 Docker (optional)

```bash
docker compose up --build
# backend :8000 · frontend :3000
```

## ✅ Success Criteria

- [x] Customer onboarding (7-step wizard, save progress, validation)
- [x] CRM lookup (mock CRM + synthetic data, 60% match rate)
- [x] Risk assessment (deterministic weighted 0–100 scoring, 4 bands)
- [x] Compliance validation (GDPR consent gate blocks workflow)
- [x] Policy recommendation (top-3 weighted match scoring, eligibility filters)
- [x] Explainability (LLM + deterministic template fallback)
- [x] Multi-agent orchestration (LangGraph supervisor, retry ×3, fallbacks)
- [x] Dashboard visualization (risk gauge, agent timeline, trace)
- [x] Test coverage (65 backend tests / 90%, 11 jest tests)
- [x] Error recovery (CRM outage demo, LLM fallback, input fail-fast)