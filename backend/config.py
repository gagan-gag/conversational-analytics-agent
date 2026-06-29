"""
config.py — Centralised settings loaded from .env via pydantic-settings.
All secrets are read once at import time; never hardcoded.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────────────────────────
    groq_api_key: str = ""
    openai_api_key: str = ""
    model_name: str = "llama-3.1-70b-versatile"
    embedding_model: str = "text-embedding-3-small"

    # ── Paths ─────────────────────────────────────────────────────────────────
    chroma_db_path: str = "./data/chroma"
    sqlite_db_path: str = "./data/analytics.db"

    # ── App ───────────────────────────────────────────────────────────────────
    max_upload_size_mb: int = 50
    log_level: str = "INFO"

    # ── RAG ───────────────────────────────────────────────────────────────────
    chunk_size: int = 512          # tokens
    chunk_overlap: int = 50        # tokens
    retriever_k: int = 5           # top-k chunks

    # ── Memory ────────────────────────────────────────────────────────────────
    memory_window_k: int = 5       # last N turns kept in context

    # ── SQL ───────────────────────────────────────────────────────────────────
    sql_max_rows: int = 500


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
