"""Agent 1: Customer Onboarding Agent.
Collects, validates and structures the customer profile."""
import time
from typing import Any, Dict

from backend.app.agents.guardrails import (
    detect_prompt_injection,
    sanitize_text,
    validate_customer_input,
)

NAME = "onboarding_agent"

STRING_FIELDS = [
    "first_name", "last_name", "email", "phone", "gender", "location",
    "occupation", "marital_status", "health_conditions", "insurance_needs",
]


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """Validate raw input and produce a structured customer profile.
    Raises ValueError on invalid input so the supervisor can handle retries."""
    started = time.time()
    data: Dict[str, Any] = dict(state.get("customer_input") or {})

    # Sanitize all free-text fields (SQL/XSS) and check for prompt injection
    for field in STRING_FIELDS:
        if isinstance(data.get(field), str):
            data[field] = sanitize_text(data[field])
    joined = " ".join(str(data.get(f, "")) for f in STRING_FIELDS)
    is_injection, pattern = detect_prompt_injection(joined)
    if is_injection:
        raise ValueError(
            f"Input rejected by guardrail: potential prompt injection "
            f"detected ('{pattern}')"
        )

    ok, errors = validate_customer_input(data)
    if not ok:
        raise ValueError("Validation failed: " + "; ".join(errors))

    profile = {
        "first_name": str(data["first_name"]).strip(),
        "last_name": str(data.get("last_name") or "").strip(),
        "email": str(data.get("email") or "").strip().lower(),
        "phone": str(data.get("phone") or "").strip(),
        "age": int(data["age"]),
        "gender": str(data["gender"]).strip(),
        "location": str(data["location"]).strip(),
        "occupation": str(data["occupation"]).strip(),
        "annual_income": float(data["annual_income"]),
        "marital_status": str(data["marital_status"]).strip().lower(),
        "health_conditions": [
            c.strip().lower()
            for c in str(data.get("health_conditions") or "").split(",")
            if c.strip()
        ],
        "smoker": str(data.get("smoker") or "no").strip().lower(),
        "insurance_needs": [
            n.strip().lower()
            for n in str(data["insurance_needs"]).split(",")
            if n.strip()
        ],
        "budget": float(data.get("budget") or data["annual_income"] * 0.05),
        "consent_given": bool(data.get("consent_given", False)),
    }

    return {
        "profile": profile,
        "trace": [{
            "agent": NAME,
            "status": "success",
            "latency_ms": int((time.time() - started) * 1000),
            "message": f"Profile created for {profile['first_name']} "
                       f"({profile['age']}y, {profile['occupation']})",
            "attempts": 1,
        }],
    }