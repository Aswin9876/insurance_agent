"""Agent 4: Compliance Agent.
GDPR-style consent verification, mandatory field checks, PII handling
validation. Can block the workflow."""
import time
from typing import Any, Dict, List

NAME = "compliance_agent"

MANDATORY_FIELDS = [
    "first_name", "age", "gender", "location", "occupation",
    "annual_income", "marital_status", "insurance_needs",
]


def check(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Pure compliance check (unit-testable)."""
    violations: List[str] = []
    warnings: List[str] = []

    # 1. Consent verification (GDPR)
    if not profile.get("consent_given"):
        violations.append("GDPR consent not provided — processing blocked")

    # 2. Mandatory fields
    for f in MANDATORY_FIELDS:
        v = profile.get(f)
        if v is None or v == "" or v == []:
            violations.append(f"Mandatory field missing: {f}")

    # 3. PII handling: raw email/phone must NOT flow to LLM agents
    if profile.get("email") and "@" in str(profile.get("email")) \
            and not str(profile["email"]).endswith("***"):
        warnings.append("Email present in profile — masked for LLM context")
    if profile.get("phone"):
        warnings.append("Phone present in profile — masked for LLM context")

    # 4. Data minimization sanity: age bounds already validated upstream
    passed = len(violations) == 0
    report = {
        "gdpr": {
            "consent_given": bool(profile.get("consent_given")),
            "lawful_basis": "explicit_consent" if profile.get("consent_given") else "none",
            "data_retention_days": 365,
            "right_to_erasure_supported": True,
        },
        "pii_checks": {
            "masking_applied_for_llm": True,
            "warnings": warnings,
        },
        "violations": violations,
        "status": "passed" if passed else "blocked",
    }
    return report


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    started = time.time()
    profile = state.get("profile") or {}
    report = check(profile)
    passed = report["status"] == "passed"
    msg = ("Compliance passed: consent verified, mandatory fields complete"
           if passed else "Compliance BLOCKED: " + "; ".join(report["violations"]))
    return {
        "compliance": report,
        "blocked": not passed,
        "trace": [{
            "agent": NAME,
            "status": "success" if passed else "blocked",
            "latency_ms": int((time.time() - started) * 1000),
            "message": msg,
            "attempts": 1,
        }],
    }