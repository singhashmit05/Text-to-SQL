"""
Centralized configuration loaded from environment variables (.env).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- LLM ---
    # Free tier via Google AI Studio: https://aistudio.google.com/apikey
    google_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    
    # Groq configuration
    # groq_api_key: str | None = None
  
    # Groq configuration
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"  


    # --- Database ---
    # Full SQLAlchemy URL for the READ-ONLY role the agent queries with.
    # e.g. postgresql+psycopg2://sql_agent_ro:pass@host:5432/dbname
    database_url: str

    # Full SQLAlchemy URL for a role with CREATE TABLE / INSERT privileges.
    # Used ONLY by the dataset-upload endpoint (app/db/loader.py) to create
    # tables from user-uploaded files — the agent itself NEVER uses this
    # connection. On Supabase this is your default "postgres" role connection.
    database_admin_url: str

    # --- Uploads ---
    max_upload_mb: int = 15
    max_upload_rows: int = 200_000

    # --- Guardrails ---
    max_rows_returned: int = 200          # hard cap on rows the agent can pull back
    default_top_k: int = 5                # default LIMIT suggested to the model
    query_timeout_seconds: int = 15       # statement_timeout applied per query
    max_agent_retries: int = 2            # how many times the agent may self-correct a failing query

    # --- LangSmith (optional tracing) ---
    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str = "text2sql-agent"

    # --- API ---
    cors_allow_origins: str = "http://localhost:5173"  # comma-separated list; add your Vercel URL in prod

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
