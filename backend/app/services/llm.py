"""Centralized LLM factory — TCS GenAI Lab (OpenAI-compatible endpoint).
All agents use this so base_url/model/key/SSL are configured in one place.
If no API key is set, callers fall back to deterministic templates."""
from functools import lru_cache
from typing import Optional

import httpx

from backend.app.config import settings

DEFAULT_MODEL = "genailab-maas-gpt-4o"

# Candidate models queried from /v1/models, in preference order.
PREFERRED_MODELS = [
    "genailab-maas-gpt-4o",
    "azure/genailab-maas-gpt-4o-mini",
    "genailab-maas-gpt-5-mini",
    "genailab-maas-gpt-5.4-mini",
    "gemini-2.5-flash",
]


@lru_cache(maxsize=1)
def _client() -> httpx.Client:
    """Shared httpx client (SSL verify configurable for internal certs)."""
    return httpx.Client(verify=settings.llm_verify_ssl, timeout=30)


def discover_model() -> Optional[str]:
    """Best available model for the key by querying /v1/models."""
    try:
        r = _client().get(f"{settings.llm_base_url}/v1/models",
                          headers={"Authorization":
                                   f"Bearer {settings.openai_api_key}"},
                          timeout=15)
        if r.status_code == 200:
            ids = [m.get("id", "") for m in r.json().get("data", [])]
            for cand in PREFERRED_MODELS:
                if cand in ids:
                    return cand
            return ids[0] if ids else None
    except Exception:  # noqa: BLE001
        return None
    return None


@lru_cache(maxsize=1)
def get_llm():
    """Build the ChatOpenAI instance for the GenAI Lab endpoint.
    Returns None when no API key is configured (offline mode)."""
    if not settings.openai_api_key:
        return None
    try:
        from langchain_openai import ChatOpenAI
        model = settings.llm_model or discover_model() or DEFAULT_MODEL
        return ChatOpenAI(
            base_url=settings.llm_base_url,
            model=model,
            api_key=settings.openai_api_key,
            temperature=0.3,
            timeout=30,
            max_retries=0,
            http_client=_client(),
        )
    except Exception:  # noqa: BLE001 — offline fallback
        return None


def llm_available() -> bool:
    """True when an API key is present AND the client builds."""
    return get_llm() is not None


def invoke_llm(messages) -> str | None:
    """Safe invoke: returns content string or None on any failure."""
    llm = get_llm()
    if llm is None:
        return None
    try:
        resp = llm.invoke(messages)
        return str(resp.content)
    except Exception:  # noqa: BLE001 — network/auth/model errors
        return None