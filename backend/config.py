"""
Configuration management for Supply Chain Orchestrator AI System.
Loads settings from environment variables / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM ───────────────────────────────────────────────────────────────────
    llm_provider: str = "ollama"  # openai, azure, ollama, groq
    
    # OpenAI / Azure
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.0
    openai_api_base: Optional[str] = None
    openai_api_version: Optional[str] = None

    # Ollama
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"

    # Groq
    groq_api_key: str = ""

    # ── External APIs ─────────────────────────────────────────────────────────
    tavily_api_key: str = ""

    # ── Vector DB ─────────────────────────────────────────────────────────────
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "supply_chain_memory"

    # ── Agent / Graph limits ──────────────────────────────────────────────────
    max_retries: int = 3
    max_iterations: int = 10
    approval_timeout_seconds: int = 300

    # ── Caching ───────────────────────────────────────────────────────────────
    cache_ttl_seconds: int = 300

    # ── Webhook / Notification ────────────────────────────────────────────────
    webhook_url: str = ""
    base_url: str = "http://localhost:8000"

    # ── CORS ──────────────────────────────────────────────────────────────────
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
