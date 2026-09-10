"""Input guardrails: validation, prompt-injection detection, PII masking,
and basic security sanitization."""
import re
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------- validation
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9\- ]{7,14}$")

REQUIRED_FIELDS = [
    "first_name", "age", "gender", "location", "occupation",
    "annual_income", "marital_status", "insurance_needs",
]


class GuardrailError(ValueError):
    """Raised when input fails validation."""


def validate_customer_input(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate required fields, age, email, phone, income.
    Returns (ok, errors)."""
    errors: List[str] = []
    for field in REQUIRED_FIELDS:
        v = data.get(field)
        if v is None or (isinstance(v, str) and not v.strip()):
            errors.append(f"Missing required field: {field}")

    # Age validation
    try:
        age = int(data.get("age", 0))
        if not (18 <= age <= 100):
            errors.append("Age must be between 18 and 100")
    except (TypeError, ValueError):
        if data.get("age") is not None:
            errors.append("Age must be a number")

    # Email validation (optional but must be valid if present)
    email = str(data.get("email") or "").strip()
    if email and not EMAIL_RE.match(email):
        errors.append("Invalid email address")

    # Phone validation (optional but must be valid if present)
    phone = str(data.get("phone") or "").strip()
    if phone and not PHONE_RE.match(phone):
        errors.append("Invalid phone number")

    # Income validation
    try:
        income = float(data.get("annual_income", 0))
        if income < 0:
            errors.append("Income cannot be negative")
        if income > 100_000_000:
            errors.append("Income exceeds maximum supported value")
    except (TypeError, ValueError):
        errors.append("Income must be a number")

    return (len(errors) == 0, errors)


# --------------------------------------------------- prompt injection filter
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"reveal\s+(your\s+)?(system\s+)?(prompt|instructions)",
    r"show\s+(me\s+)?(your\s+)?(system\s+)?(prompt|instructions)",
    r"override\s+(your\s+)?(instructions|rules|directives)",
    r"you\s+are\s+now\s+(a|an|free|unrestricted|DAN)",
    r"jailbreak",
    r"developer\s+mode",
    r"pretend\s+(you\s+)?(are|to\s+be)\s+not\s+bound",
    r"print\s+(your\s+)?(prompt|instructions|secrets)",
    r"repeat\s+(everything|your\s+prompt)",
]

INJECTION_RE = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)


def detect_prompt_injection(text: str) -> Tuple[bool, str]:
    """Return (is_injection, matched_pattern_description)."""
    if not text:
        return False, ""
    m = INJECTION_RE.search(text)
    if m:
        return True, m.group(0)
    return False, ""


# ------------------------------------------------------------- PII masking
EMAIL_MASK_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_MASK_RE = re.compile(r"\+?\d[\d\- ]{7,14}\d")


def mask_pii(text: str) -> str:
    """Mask emails, phones and long digit sequences before sending to LLM."""
    if not text:
        return text
    text = EMAIL_MASK_RE.sub("[EMAIL]", text)
    text = PHONE_MASK_RE.sub("[PHONE]", text)
    return text


def mask_customer(cust: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of a customer dict with PII fields masked for LLM use."""
    safe = dict(cust or {})
    if safe.get("email"):
        local, _, domain = str(safe["email"]).partition("@")
        safe["email"] = f"{local[:2]}***@{domain}" if local else "***"
    if safe.get("phone"):
        p = str(safe["phone"])
        safe["phone"] = "***" + p[-3:] if len(p) > 3 else "***"
    if safe.get("location"):
        safe["location"] = str(safe["location"]).split(",")[0].strip() or "[REDACTED]"
    return safe


# ------------------------------------------------------------- sanitization
SQL_INJECTION_RE = re.compile(
    r"(\b(union\s+select|drop\s+table|insert\s+into|delete\s+from|"
    r"update\s+\w+\s+set)\b|--|/\*|\*/|;)", re.IGNORECASE)
XSS_RE = re.compile(r"(<script|javascript:|onerror\s*=|onload\s*=|<iframe)", re.IGNORECASE)


def sanitize_text(text: str) -> str:
    """Neutralize SQL/XSS/script injection payloads in free text."""
    if not text:
        return text
    cleaned = SQL_INJECTION_RE.sub("", text)
    cleaned = XSS_RE.sub("", cleaned)
    return cleaned.strip()