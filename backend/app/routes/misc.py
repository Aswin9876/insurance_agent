"""Policies catalog, onboarding validation and chat endpoints."""
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.agents.guardrails import validate_customer_input
from backend.app.agents.recommendation_agent import load_catalog
from backend.app.services import chat_service

router = APIRouter(tags=["misc"])


@router.get("/api/policies")
def list_policies():
    """Full product catalog."""
    return {"policies": load_catalog()}


@router.post("/api/onboarding/validate")
def validate(data: Dict[str, Any]):
    """Pre-flight validation used by wizard steps (real-time feedback)."""
    ok, errors = validate_customer_input(data)
    return {"valid": ok, "errors": errors}


class ChatRequest(BaseModel):
    message: str
    context: Dict[str, Any] = {}


@router.post("/api/chat")
def chat(body: ChatRequest):
    """AI assistant with guardrails (injection detection + PII masking)."""
    return chat_service.answer(body.message, body.context)