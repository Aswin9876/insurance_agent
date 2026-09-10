"""Shared workflow state for the LangGraph multi-agent pipeline."""
from typing import Any, Dict, List

from typing_extensions import TypedDict


class AgentTrace(TypedDict, total=False):
    agent: str
    status: str          # success | fallback | blocked | skipped
    latency_ms: int
    message: str
    attempts: int


class WorkflowState(TypedDict, total=False):
    # input
    run_id: str
    customer_input: Dict[str, Any]

    # per-agent outputs
    profile: Dict[str, Any]
    crm: Dict[str, Any]
    risk: Dict[str, Any]
    compliance: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    explanations: List[Dict[str, Any]]
    summary: Dict[str, Any]

    # orchestration bookkeeping
    trace: List[AgentTrace]
    errors: List[str]
    blocked: bool
    status: str          # running | completed | blocked | failed
    agent_status: Dict[str, str]  # agent name -> success|fallback|blocked|failed