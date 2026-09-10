"""SUPERVISOR AGENT — LangGraph orchestration of the 6-agent pipeline.

Responsibilities:
  • Workflow routing (linear pipeline with conditional compliance gate)
  • Retry handling (3 attempts per agent)
  • Fallback responses (deterministic) on failure
  • Result aggregation + final summary
  • Error recovery + full execution trace
"""
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List

from langgraph.graph import END, StateGraph

from backend.app.agents import (
    compliance_agent,
    crm_agent,
    explainability_agent,
    onboarding_agent,
    recommendation_agent,
    risk_agent,
)
from backend.app.agents.state import WorkflowState
from backend.app.services.error_handler import classify_error, log_event

MAX_RETRIES = 3


# --------------------------------------------------------------------------
# Node wrapper: retries + fallback + trace bookkeeping
# --------------------------------------------------------------------------
def make_node(name: str, agent_run: Callable,
              fallback: Callable[[Dict[str, Any], Exception], Dict[str, Any]],
              state_key: str) -> Callable[[WorkflowState], Dict[str, Any]]:
    """Wrap an agent's run() with supervisor behavior:
    retry x3 -> fallback -> trace + error recording."""

    def node(state: WorkflowState) -> Dict[str, Any]:
        run_id = state.get("run_id", "-")
        trace = list(state.get("trace") or [])
        errors = list(state.get("errors") or [])
        agent_status = dict(state.get("agent_status") or {})
        updates: Dict[str, Any] = {"trace": trace, "errors": errors,
                                   "agent_status": agent_status}

        last_exc: Exception = Exception("unknown")
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = agent_run(state)
                # Extract the agent's trace entry and ACCUMULATE it —
                # agents return single-entry traces; LangGraph would
                # otherwise replace the whole state trace with it.
                agent_trace = result.pop("trace", [])
                for k, v in result.items():
                    updates[k] = v
                updates["trace"] = trace + agent_trace
                agent_status[name] = "success"
                updates["agent_status"] = agent_status
                log_event(run_id, name, f"completed on attempt {attempt}")
                return updates
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                strategy = classify_error(exc)
                log_event(run_id, name,
                          f"attempt {attempt}/{MAX_RETRIES} failed: {exc}",
                          level="WARN" if attempt < MAX_RETRIES else "ERROR",
                          detail={"strategy": strategy})
                if strategy == "input_error":
                    break  # retries cannot fix bad input
                time.sleep(0.05 * attempt)  # small backoff for transient errs

        # All retries exhausted (or non-retryable) -> fallback
        fb = fallback(state, last_exc)
        for k, v in fb.items():
            updates[k] = v
        fb_trace = list(updates.get("trace") or [])
        fb_trace.append({
            "agent": name,
            "status": "fallback",
            "latency_ms": 0,
            "message": f"Fallback used after error: {last_exc}",
            "attempts": MAX_RETRIES,
        })
        updates["trace"] = fb_trace
        errors.append(f"{name}: {last_exc}")
        updates["errors"] = errors
        agent_status[name] = "fallback"
        updates["agent_status"] = agent_status
        return updates

    return node


# --------------------------------------------------------------------------
# Fallbacks (deterministic, keep workflow alive when possible)
# --------------------------------------------------------------------------
def fb_crm(state: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
    return {"crm": {
        "crm_id": None, "existing_customer": False,
        "previous_policies": [], "claims_history": [],
        "claims_count": 0, "total_claimed": 0,
        "loyalty_tier": "new", "degraded": True,
    }}


def fb_risk(state: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
    profile = state.get("profile") or {}
    age = int(profile.get("age") or 40)
    # Age-only conservative estimate
    score = min(100.0, max(10.0, (age - 18) * 1.1))
    from backend.app.agents.risk_agent import categorize
    return {"risk": {
        "risk_score": score, "category": categorize(score),
        "confidence": 0.4,
        "factors": {"weights": {}, "subscores": {}},
        "explanation": "Fallback risk estimate based on age only "
                       "(full scoring engine unavailable).",
    }}


def fb_recommendation(state: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
    catalog = recommendation_agent.load_catalog()
    profile = state.get("profile") or {}
    budget = float(profile.get("budget") or
                   float(profile.get("annual_income") or 0) * 0.05)
    affordable = [p for p in catalog if p["premium"] <= budget * 1.2] or catalog[:3]
    recs = []
    for i, p in enumerate(sorted(affordable, key=lambda x: x["premium"])[:3], 1):
        recs.append({
            "ranking": i, "product_id": p["product_id"],
            "policy_name": p["name"], "match_score": round(60.0 - i * 5, 1),
            "premium": p["premium"], "coverage_summary": p["coverage"],
            "summary": p["summary"], "score_breakdown": {},
        })
    return {"recommendations": recs}


def fb_explainability(state: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
    recs = state.get("recommendations") or []
    return {"explanations": [{
        "ranking": r.get("ranking", i + 1),
        "policy_name": r.get("policy_name", "Policy"),
        "explanation": "This policy matches your general profile. "
                       "Detailed explanation temporarily unavailable.",
        "risk_explanation": "", "coverage_comparison": "",
        "generated_by": "fallback",
    } for i, r in enumerate(recs)]}


# --------------------------------------------------------------------------
# Graph node functions (thin wrappers around agents)
# --------------------------------------------------------------------------
def onboarding_node(state: WorkflowState) -> Dict[str, Any]:
    """Onboarding with graceful failure: invalid input blocks the run."""
    try:
        return onboarding_agent.run(state)
    except Exception as exc:  # noqa: BLE001
        run_id = state.get("run_id", "-")
        log_event(run_id, onboarding_agent.NAME,
                  f"input rejected: {exc}", level="ERROR")
        trace = list(state.get("trace") or []) + [{
            "agent": onboarding_agent.NAME, "status": "blocked",
            "latency_ms": 0, "attempts": 1,
            "message": f"Input rejected: {exc}",
        }]
        return {
            "trace": trace,
            "errors": [f"{onboarding_agent.NAME}: {exc}"],
            "agent_status": {onboarding_agent.NAME: "blocked"},
            "blocked": True,
            "profile": {},
        }


def onboarding_gate(state: WorkflowState) -> str:
    if state.get("blocked"):
        return "aggregate"  # blocked runs still get a summary
    return "crm_agent"


crm_node = make_node("crm_agent", crm_agent.run, fb_crm, "crm")
risk_node = make_node("risk_agent", risk_agent.run, fb_risk, "risk")
compliance_node = make_node("compliance_agent", compliance_agent.run,
                            lambda s, e: {}, "compliance")
recommendation_node = make_node("recommendation_agent",
                                recommendation_agent.run,
                                fb_recommendation, "recommendations")
explainability_node = make_node("explainability_agent",
                                explainability_agent.run,
                                fb_explainability, "explanations")


def compliance_gate(state: WorkflowState) -> str:
    """Conditional edge: skip recommendations if compliance blocked,
    but always route to aggregate for a final summary."""
    if state.get("blocked"):
        log_event(state.get("run_id", "-"), "supervisor",
                  "workflow blocked by compliance — stopping pipeline",
                  level="WARN")
        return "aggregate"
    return "recommendation_agent"


def aggregate_node(state: WorkflowState) -> Dict[str, Any]:
    """Final aggregation: build summary for the dashboard."""
    run_id = state.get("run_id", "-")
    profile = state.get("profile") or {}
    risk = state.get("risk") or {}
    recs = state.get("recommendations") or []
    compliance = state.get("compliance") or {}
    trace = state.get("trace") or []
    agent_status = state.get("agent_status") or {}

    # Compliance trace entry if it produced none (blocked path)
    if compliance and compliance.get("status") == "blocked" and \
            not any(t["agent"] == compliance_agent.NAME for t in trace):
        trace = trace + [{
            "agent": compliance_agent.NAME, "status": "blocked",
            "latency_ms": 0, "attempts": 1,
            "message": "Compliance BLOCKED: "
                       + "; ".join(compliance.get("violations", [])),
        }]

    status = "blocked" if state.get("blocked") else "completed"
    summary = {
        "run_id": run_id,
        "status": status,
        "customer": {
            "name": f"{profile.get('first_name', '')} "
                    f"{profile.get('last_name', '')}".strip(),
            "age": profile.get("age"),
            "location": profile.get("location"),
            "occupation": profile.get("occupation"),
            "income": profile.get("annual_income"),
            "marital_status": profile.get("marital_status"),
            "insurance_needs": profile.get("insurance_needs"),
            "crm_id": (state.get("crm") or {}).get("crm_id"),
        },
        "crm": state.get("crm") or {},
        "risk": risk,
        "compliance": compliance,
        "recommendations": recs,
        "explanations": state.get("explanations") or [],
        "trace": trace,
        "agent_status": agent_status,
        "errors": state.get("errors") or [],
        "completed_at": datetime.utcnow().isoformat(),
    }
    log_event(run_id, "supervisor", f"workflow {status} with "
              f"{len(recs)} recommendations")
    return {"summary": summary, "status": status}


# --------------------------------------------------------------------------
# Graph assembly
# --------------------------------------------------------------------------
def build_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("onboarding_agent", onboarding_node)
    graph.add_node("crm_agent", crm_node)
    graph.add_node("risk_agent", risk_node)
    graph.add_node("compliance_agent", compliance_node)
    graph.add_node("recommendation_agent", recommendation_node)
    graph.add_node("explainability_agent", explainability_node)
    graph.add_node("aggregate", aggregate_node)

    graph.set_entry_point("onboarding_agent")
    graph.add_conditional_edges("onboarding_agent", onboarding_gate,
                                {"crm_agent": "crm_agent",
                                 "aggregate": "aggregate"})
    graph.add_edge("crm_agent", "risk_agent")
    graph.add_edge("risk_agent", "compliance_agent")
    graph.add_conditional_edges("compliance_agent", compliance_gate,
                                {"recommendation_agent": "recommendation_agent",
                                 "aggregate": "aggregate"})
    graph.add_edge("recommendation_agent", "explainability_agent")
    graph.add_edge("explainability_agent", "aggregate")
    graph.add_edge("aggregate", END)
    return graph.compile()


app_graph = build_graph()


def run_workflow(customer_input: Dict[str, Any],
                 run_id: str = None) -> Dict[str, Any]:
    """Execute the full multi-agent workflow. Returns final state."""
    run_id = run_id or f"run-{uuid.uuid4().hex[:12]}"
    initial: WorkflowState = {
        "run_id": run_id,
        "customer_input": customer_input,
        "trace": [], "errors": [], "blocked": False,
        "status": "running", "agent_status": {},
    }
    log_event(run_id, "supervisor", "workflow started")
    started = time.time()
    final = app_graph.invoke(initial, {"recursion_limit": 25})
    log_event(run_id, "supervisor",
              f"workflow finished in {(time.time() - started) * 1000:.0f}ms")
    return final