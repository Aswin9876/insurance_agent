"""Agent workflow endpoints: run the multi-agent pipeline, fetch runs,
observability logs."""
import json
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.agents.state import WorkflowState
from backend.app.agents.supervisor_agent import run_workflow
from backend.app.database import get_db
from backend.app.models import (AuditLog, Customer, Recommendation,
                                RiskAssessment, WorkflowRun)
from backend.app.routes.auth import get_current_user
from backend.app.models import User

router = APIRouter(prefix="/api/agents", tags=["agents"])


class RunRequest(BaseModel):
    customer: Dict[str, Any]


@router.post("/run")
def run(body: RunRequest, db: Session = Depends(get_db),
        user: User = Depends(get_current_user)):
    """Execute the full 6-agent workflow for a customer."""
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    try:
        final: WorkflowState = run_workflow(body.customer, run_id=run_id)
    except Exception as exc:  # last-resort centralized handler
        raise HTTPException(status_code=500,
                            detail=f"Workflow crashed: {exc}") from exc

    summary = final.get("summary") or {}
    status = final.get("status", "completed")

    # Persist customer (upsert by email if present)
    profile = final.get("profile") or {}
    customer_id = None
    if profile:
        existing = None
        if profile.get("email"):
            existing = db.query(Customer).filter_by(
                email=profile["email"]).first()
        if existing:
            existing.status = status
            customer_id = existing.id
        else:
            cust = Customer(
                crm_id=(final.get("crm") or {}).get("crm_id"),
                first_name=profile.get("first_name", "Unknown"),
                last_name=profile.get("last_name", ""),
                email=profile.get("email", ""),
                phone=profile.get("phone", ""),
                age=profile.get("age", 0),
                gender=profile.get("gender", ""),
                location=profile.get("location", ""),
                occupation=profile.get("occupation", ""),
                annual_income=profile.get("annual_income", 0),
                marital_status=profile.get("marital_status", ""),
                health_conditions=",".join(
                    profile.get("health_conditions") or []),
                smoker=profile.get("smoker", "no"),
                insurance_needs=",".join(
                    profile.get("insurance_needs") or []),
                budget=profile.get("budget", 0),
                consent_given=1 if profile.get("consent_given") else 0,
                status=status,
            )
            db.add(cust)
            db.flush()
            customer_id = cust.id

    # Persist risk assessment
    risk = final.get("risk") or {}
    if risk:
        db.add(RiskAssessment(
            customer_id=customer_id, run_id=run_id,
            risk_score=risk.get("risk_score"),
            category=risk.get("category"),
            confidence=risk.get("confidence"),
            factors=risk.get("factors"),
            explanation=risk.get("explanation")))

    # Persist recommendations
    for rec in final.get("recommendations") or []:
        db.add(Recommendation(
            customer_id=customer_id, run_id=run_id,
            ranking=rec.get("ranking"), policy_name=rec.get("policy_name"),
            product_id=rec.get("product_id"),
            match_score=rec.get("match_score"), premium=rec.get("premium"),
            coverage_summary=rec.get("coverage_summary"),
            reasoning=(final.get("explanations") or [{}])[rec.get("ranking", 1) - 1]
            .get("explanation", "") if final.get("explanations") else ""))

    # Persist audit logs from trace
    for t in final.get("trace") or []:
        db.add(AuditLog(run_id=run_id, agent=t.get("agent"),
                        event=t.get("message", ""), level="INFO",
                        detail={"status": t.get("status"),
                                "latency_ms": t.get("latency_ms"),
                                "attempts": t.get("attempts")}))
    for e in final.get("errors") or []:
        db.add(AuditLog(run_id=run_id, agent="supervisor", event=e,
                        level="ERROR"))

    # Persist workflow run
    db.add(WorkflowRun(id=run_id, customer_id=customer_id, status=status,
                       final_state=summary))
    db.commit()

    return {"run_id": run_id, "status": status, "summary": summary}


@router.get("/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    run = db.query(WorkflowRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run.id, "status": run.status,
            "created_at": str(run.created_at), "summary": run.final_state}


@router.get("/runs/{run_id}/logs")
def get_run_logs(run_id: str, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    logs = db.query(AuditLog).filter_by(run_id=run_id) \
        .order_by(AuditLog.created_at).all()
    return {"run_id": run_id, "logs": [{
        "agent": l.agent, "event": l.event, "level": l.level,
        "detail": l.detail, "timestamp": str(l.created_at),
    } for l in logs]}