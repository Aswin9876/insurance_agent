"""Agent 2: CRM Intelligence Agent.
Looks up existing customer records, previous policies and claims history
from the mock CRM service, then merges data into the profile context."""
import time
from typing import Any, Dict

from backend.app.services.crm_mock import get_claims, get_customer, get_policies

NAME = "crm_agent"


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    started = time.time()
    profile = dict(state.get("profile") or {})

    crm_customer = get_customer(profile)
    crm_id = crm_customer.get("crm_id")
    policies = get_policies(crm_id) if crm_id else []
    claims = get_claims(crm_id) if crm_id else []

    crm = {
        "crm_id": crm_id,
        "existing_customer": crm_customer.get("found", False),
        "previous_policies": policies,
        "claims_history": claims,
        "claims_count": len(claims),
        "total_claimed": sum(c.get("amount", 0) for c in claims),
        "customer_since": crm_customer.get("customer_since"),
        "loyalty_tier": crm_customer.get("loyalty_tier", "new"),
    }

    # Merge CRM insight into profile (non-destructive enrichment)
    profile["crm_id"] = crm_id
    profile["existing_customer"] = crm["existing_customer"]
    profile["claims_count"] = crm["claims_count"]

    msg = (
        f"Existing customer {crm_id} ({crm['loyalty_tier']} tier): "
        f"{len(policies)} prior policies, {len(claims)} claims"
        if crm["existing_customer"]
        else "New customer — no prior CRM records found"
    )
    return {
        "profile": profile,
        "crm": crm,
        "trace": [{
            "agent": NAME,
            "status": "success",
            "latency_ms": int((time.time() - started) * 1000),
            "message": msg,
            "attempts": 1,
        }],
    }