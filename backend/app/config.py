"""
config.py – Application configuration using pydantic-settings.
All sensitive values are loaded from environment variables; nothing is hard-coded.
"""

from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ─────────────────────────────────────────────────────────────────
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ── LLM ─────────────────────────────────────────────────────────────────
    llm_provider: Literal["ollama", "gemini"] = "ollama"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    ollama_temperature: float = 0.0

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./data/sample.db"

    # ── Query limits ─────────────────────────────────────────────────────────
    max_query_rows: int = 1000
    query_timeout_seconds: int = 30
    max_sql_retries: int = 3

    # ── Embeddings / FAISS ───────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    faiss_index_path: str = "./data/faiss_index"

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
