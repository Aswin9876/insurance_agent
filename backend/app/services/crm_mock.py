"""Mock CRM service backed by synthetic data files.
Simulates an external CRM API (with failure simulation for demo of retries)."""
import json
import os
import random
from typing import Any, Dict, List

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# Simulated outage probability per call (0 for deterministic demos)
FAILURE_RATE = float(os.getenv("CRM_FAILURE_RATE", "0"))

_cache: Dict[str, Any] = {}


def _load(filename: str) -> Any:
    if filename not in _cache:
        path = os.path.join(DATA_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            _cache[filename] = json.load(f)
    return _cache[filename]


def _maybe_fail() -> None:
    """Randomly simulate an upstream CRM outage (used to demo retries)."""
    if FAILURE_RATE and random.random() < FAILURE_RATE:
        raise ConnectionError("Mock CRM upstream unavailable")


def get_customer(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Match a customer by email or (first_name+last_name); else new customer."""
    _maybe_fail()
    customers: List[Dict[str, Any]] = _load("crm_customers.json")
    email = str(profile.get("email") or "").lower()
    fname = str(profile.get("first_name") or "").lower()
    lname = str(profile.get("last_name") or "").lower()

    for c in customers:
        if email and c.get("email", "").lower() == email:
            return {**c, "found": True}
        if fname and c.get("first_name", "").lower() == fname \
                and lname and c.get("last_name", "").lower() == lname:
            return {**c, "found": True}
    return {"found": False, "crm_id": None}


def get_policies(crm_id: str) -> List[Dict[str, Any]]:
    """Return previous policy enrollments for a CRM customer."""
    _maybe_fail()
    enrollments: List[Dict[str, Any]] = _load("crm_policies.json")
    return [p for p in enrollments if p.get("crm_id") == crm_id]


def get_claims(crm_id: str) -> List[Dict[str, Any]]:
    """Return claims history for a CRM customer."""
    _maybe_fail()
    claims: List[Dict[str, Any]] = _load("crm_claims.json")
    return [c for c in claims if c.get("crm_id") == crm_id]