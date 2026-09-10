"""Agent 3: Risk Assessment Agent.
Deterministic weighted scoring: 0-100 risk score, category, confidence,
factor breakdown and plain-language explanation."""
import time
from typing import Any, Dict, List, Tuple

NAME = "risk_agent"

# Weights must sum to 100
WEIGHTS = {
    "age": 25,
    "occupation": 15,
    "health": 25,
    "lifestyle": 15,
    "claims": 20,
}

HIGH_RISK_OCCUPATIONS = {"mining", "construction", "pilot", "fisherman",
                         "roofer", "truck_driver", "logging", "firefighter"}
MILD_CONDITIONS = {"hypertension", "asthma", "obesity", "diabetes_pre"}
SEVERE_CONDITIONS = {"diabetes", "heart_disease", "cancer", "stroke",
                     "kidney_disease", "copd"}


def _age_subscore(age: int) -> float:
    """0 (safe) .. 100 (risky)."""
    if age < 30:
        return 10
    if age < 40:
        return 25
    if age < 50:
        return 45
    if age < 60:
        return 65
    if age < 70:
        return 85
    return 100


def _occupation_subscore(occupation: str) -> float:
    occ = (occupation or "").lower().replace(" ", "_").replace("-", "_")
    if occ in HIGH_RISK_OCCUPATIONS:
        return 90
    if any(k in occ for k in ("driver", "engineer_field", "worker", "labor")):
        return 60
    if occ in ("police", "soldier", "athlete"):
        return 50
    if not occ or occ in ("student", "homemaker", "retired"):
        return 30
    return 15  # office / professional


def _health_subscore(conditions: List[str]) -> float:
    score = 0.0
    for c in conditions:
        if c in SEVERE_CONDITIONS:
            score += 45
        elif c in MILD_CONDITIONS:
            score += 20
        else:
            score += 10  # unknown condition counts mildly
    return min(100.0, score)


def _lifestyle_subscore(profile: Dict[str, Any]) -> float:
    score = 20.0  # baseline
    if str(profile.get("smoker", "no")).lower() in ("yes", "true", "1"):
        score += 55
    if profile.get("bmi") and float(profile["bmi"]) >= 30:
        score += 25
    return min(100.0, score)


def _claims_subscore(claims_count: int, total_claimed: float) -> float:
    score = claims_count * 22.0
    if total_claimed > 100000:
        score += 25
    elif total_claimed > 25000:
        score += 12
    return min(100.0, score)


def categorize(score: float) -> str:
    if score <= 25:
        return "low"
    if score <= 50:
        return "medium"
    if score <= 75:
        return "high"
    return "critical"


def assess(profile: Dict[str, Any], crm: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function so it can be unit-tested directly."""
    age = int(profile.get("age") or 30)
    subscores = {
        "age": _age_subscore(age),
        "occupation": _occupation_subscore(profile.get("occupation", "")),
        "health": _health_subscore(profile.get("health_conditions") or []),
        "lifestyle": _lifestyle_subscore(profile),
        "claims": _claims_subscore(
            int(crm.get("claims_count") or 0),
            float(crm.get("total_claimed") or 0),
        ),
    }
    risk_score = round(
        sum(subscores[k] * WEIGHTS[k] for k in WEIGHTS) / 100.0, 1)

    # Confidence: more data + clear band => higher confidence
    confidence = 0.6
    if crm.get("existing_customer"):
        confidence += 0.15
    if profile.get("health_conditions"):
        confidence += 0.10
    band_mid_distance = abs(risk_score - 50) / 50  # away from band edges
    confidence = round(min(0.95, confidence + band_mid_distance * 0.1), 2)

    category = categorize(risk_score)

    drivers = sorted(
        ((k, v) for k, v in subscores.items()), key=lambda kv: -kv[1])[:2]
    driver_txt = ", ".join(f"{k} ({v:.0f}/100)" for k, v in drivers)
    explanation = (
        f"Risk score {risk_score} places this customer in the "
        f"'{category}' band. Primary drivers: {driver_txt}. "
        f"Age {age}, occupation '{profile.get('occupation')}', "
        f"{len(profile.get('health_conditions') or [])} declared health "
        f"condition(s), {crm.get('claims_count', 0)} prior claim(s)."
    )
    return {
        "risk_score": risk_score,
        "category": category,
        "confidence": confidence,
        "factors": {"weights": WEIGHTS, "subscores": subscores},
        "explanation": explanation,
    }


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    started = time.time()
    profile = state.get("profile") or {}
    crm = state.get("crm") or {}
    risk = assess(profile, crm)
    return {
        "risk": risk,
        "trace": [{
            "agent": NAME,
            "status": "success",
            "latency_ms": int((time.time() - started) * 1000),
            "message": f"Risk {risk['risk_score']} ({risk['category']}) "
                       f"confidence {risk['confidence']}",
            "attempts": 1,
        }],
    }