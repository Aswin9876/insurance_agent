"""Agent 5: Policy Recommendation Agent.
Reads the product catalog, checks eligibility, and produces the top-3
matches using a weighted scoring algorithm."""
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

NAME = "recommendation_agent"

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# Weighted scoring components (sum = 100)
W_NEEDS = 40     # category overlap with insurance needs
W_RISK = 25      # risk appetite fit
W_BUDGET = 20    # affordability
W_ELIGIBILITY = 15  # age/income/marital eligibility headroom

NEED_TO_CATEGORY = {
    "health": "health", "medical": "health", "family": "health",
    "life": "life", "term": "life", "protection": "life",
    "auto": "auto", "vehicle": "auto", "car": "auto",
    "home": "home", "property": "home",
}


def load_catalog() -> List[Dict[str, Any]]:
    path = os.path.join(DATA_DIR, "policy_catalog.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _needs_score(needs: List[str], category: str) -> float:
    if category in [NEED_TO_CATEGORY.get(n, n) for n in needs]:
        return 100.0
    return 0.0


def _risk_score(risk_score: float, policy: Dict[str, Any]) -> float:
    appetite = policy.get("risk_appetite") or {}
    lo, hi = float(appetite.get("min_score", 0)), float(appetite.get("max_score", 100))
    if lo <= risk_score <= hi:
        # Comfort: closer to middle of appetite band scores higher
        mid = (lo + hi) / 2
        return 100.0 - (abs(risk_score - mid) / max((hi - lo) / 2, 1)) * 20
    # Outside appetite: distance penalty
    distance = min(abs(risk_score - lo), abs(risk_score - hi))
    return max(0.0, 60.0 - distance * 2)


def _budget_score(policy: Dict[str, Any], budget: float,
                  income: float) -> float:
    premium = float(policy.get("premium") or 0)
    effective_budget = budget or income * 0.05
    if premium <= 0:
        return 50.0
    if premium <= effective_budget:
        # Cheaper than budget is good; very cheap loses some richness score
        ratio = premium / effective_budget
        return 100.0 - ratio * 30  # 70..100
    over = premium / effective_budget
    if over <= 1.2:
        return 55.0  # slightly over budget — acceptable
    return max(0.0, 55.0 - (over - 1.2) * 60)


def _eligibility_score(profile: Dict[str, Any],
                       policy: Dict[str, Any]) -> Optional[float]:
    """Returns None if NOT eligible at all, else 0-100 headroom score."""
    elig = policy.get("eligibility") or {}
    age = int(profile.get("age") or 0)
    if age < elig.get("min_age", 18) or age > elig.get("max_age", 100):
        return None
    marital = elig.get("marital_status")
    if marital and str(profile.get("marital_status", "")).lower() not in marital:
        return None
    min_income = elig.get("min_income")
    if min_income and float(profile.get("annual_income") or 0) < float(min_income):
        return None
    return 100.0


def score_policies(profile: Dict[str, Any], risk: Dict[str, Any],
                   catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Pure scoring function (unit-testable). Returns ranked list."""
    needs = [n.lower() for n in (profile.get("insurance_needs") or [])]
    risk_score = float(risk.get("risk_score") or 0)
    category = str(risk.get("category") or "low")
    scored: List[Tuple[float, Dict[str, Any]]] = []

    for policy in catalog:
        elig = _eligibility_score(profile, policy)
        if elig is None:
            continue
        # Risk-category hard filter via allowed_risk
        allowed = (policy.get("eligibility") or {}).get("allowed_risk") or \
            ["low", "medium", "high", "critical"]
        if category not in allowed:
            continue

        needs_s = _needs_score(needs, policy.get("category", ""))
        risk_s = _risk_score(risk_score, policy)
        budget_s = _budget_score(
            policy, float(profile.get("budget") or 0),
            float(profile.get("annual_income") or 0))
        total = (needs_s * W_NEEDS + risk_s * W_RISK + budget_s * W_BUDGET
                 + elig * W_ELIGIBILITY) / 100.0
        total = round(total, 1)
        scored.append((total, {
            "ranking": 0,
            "product_id": policy["product_id"],
            "policy_name": policy["name"],
            "match_score": total,
            "premium": policy["premium"],
            "coverage_summary": policy.get("coverage", ""),
            "summary": policy.get("summary", ""),
            "score_breakdown": {
                "needs_fit": round(needs_s, 1),
                "risk_fit": round(risk_s, 1),
                "budget_fit": round(budget_s, 1),
                "eligibility": elig,
            },
        }))

    scored.sort(key=lambda t: -t[0])
    results = []
    for i, (total, rec) in enumerate(scored[:3], start=1):
        rec["ranking"] = i
        results.append(rec)
    return results


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    started = time.time()
    profile = state.get("profile") or {}
    risk = state.get("risk") or {}
    catalog = load_catalog()
    recs = score_policies(profile, risk, catalog)
    if not recs:
        raise ValueError("No eligible policies found for profile")
    top = recs[0]
    return {
        "recommendations": recs,
        "trace": [{
            "agent": NAME,
            "status": "success",
            "latency_ms": int((time.time() - started) * 1000),
            "message": f"Top match: {top['policy_name']} "
                       f"({top['match_score']}%) — {len(recs)} recommendations",
            "attempts": 1,
        }],
    }