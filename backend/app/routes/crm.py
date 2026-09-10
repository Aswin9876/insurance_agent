"""Mock CRM API endpoints (synthetic data).
GET /crm/customer/{id}  GET /crm/policies/{id}  GET /crm/claims/{id}"""
from fastapi import APIRouter, HTTPException

from backend.app.services.crm_mock import get_claims, get_policies

router = APIRouter(prefix="/crm", tags=["crm"])

# id here is the CRM id, e.g. CUST-0001 — but we also accept lookup by
# customer JSON body via the agents. These endpoints serve direct demo.
from backend.app.services.crm_mock import _load  # noqa: E402


@router.get("/customer/{crm_id}")
def customer(crm_id: str):
    customers = _load("crm_customers.json")
    for c in customers:
        if c.get("crm_id") == crm_id:
            return {"found": True, **c}
    raise HTTPException(status_code=404, detail=f"Customer {crm_id} not found")


@router.get("/policies/{crm_id}")
def policies(crm_id: str):
    return {"crm_id": crm_id, "policies": get_policies(crm_id)}


@router.get("/claims/{crm_id}")
def claims(crm_id: str):
    return {"crm_id": crm_id, "claims": get_claims(crm_id)}