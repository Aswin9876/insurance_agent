"""Centralized error handling: logging, classification, audit trail."""
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("insurance_platform")


def log_event(run_id: str, agent: str, event: str,
              level: str = "INFO", detail: Optional[Dict[str, Any]] = None):
    """Log to console (observability) and return a structured entry
    the supervisor can persist into AuditLogs."""
    entry = {
        "run_id": run_id,
        "agent": agent,
        "event": event,
        "level": level,
        "detail": detail or {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    log = logger.error if level == "ERROR" else \
        logger.warning if level == "WARN" else logger.info
    log(f"[run={run_id}] [{agent}] {event} {detail or ''}")
    return entry


def classify_error(exc: Exception) -> str:
    """Classify an exception into a recovery strategy."""
    text = str(exc).lower()
    if "validation" in text or "guardrail" in text or "invalid" in text:
        return "input_error"       # retrying won't help — fail fast
    if "connection" in text or "timeout" in text or "unavailable" in text:
        return "transient"         # retry with fallback
    return "recoverable"           # retry then fallback