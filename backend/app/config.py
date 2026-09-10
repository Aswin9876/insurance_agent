"""Application configuration loaded from environment (with safe defaults)."""
import os

try:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        app_name: str = "Insurance Multi-Agent Platform"
        database_url: str = "sqlite:///./backend/insurance.db"
        jwt_secret: str = "demo-secret-change-me"
        jwt_algorithm: str = "HS256"
        jwt_expire_minutes: int = 60 * 24
        openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        llm_base_url: str = os.getenv("LLM_BASE_URL", "https://genailab.tcs.in")
        llm_model: str = os.getenv("LLM_MODEL", "genailab-maas-gpt-4o")
        llm_verify_ssl: bool = os.getenv("LLM_VERIFY_SSL", "false").lower() != "false" \
            if os.getenv("LLM_VERIFY_SSL") is not None else False
        cors_origins: list = ["http://localhost:3000"]

        class Config:
            env_file = ".env"

    settings = Settings()
except ImportError:  # fallback if pydantic-settings missing
    class _S:
        app_name = "Insurance Multi-Agent Platform"
        database_url = "sqlite:///./backend/insurance.db"
        jwt_secret = "demo-secret-change-me"
        jwt_algorithm = "HS256"
        jwt_expire_minutes = 60 * 24
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        llm_base_url = os.getenv("LLM_BASE_URL", "https://genailab.tcs.in")
        llm_model = os.getenv("LLM_MODEL", "genailab-maas-gpt-4o")
        llm_verify_ssl = False
        cors_origins = ["http://localhost:3000"]

    settings = _S()

LLM_ENABLED = bool(settings.openai_api_key)