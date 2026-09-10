"""FastAPI application entry point.
Run: uvicorn backend.main:app --reload --port 8000  (from project root)"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import Base, engine
from backend.app.routes import agents, auth, crm, misc

app = FastAPI(
    title=settings.app_name,
    description="AI Multi-Agent Insurance Onboarding & Policy "
                "Recommendation Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup (idempotent)
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(crm.router)
app.include_router(misc.router)


@app.get("/", tags=["health"])
def root():
    return {"service": settings.app_name, "status": "ok",
            "docs": "/docs", "llm_enabled": bool(settings.openai_api_key)}


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}