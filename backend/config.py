"""
Application configuration using pydantic-settings.
Single source of truth for all environment variables.
"""

import os
from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All config lives here — no scattered os.getenv() calls.
    """

    # ── Groq LLM ──────────────────────────────────────────────
    groq_api_key: str = Field(default="", description="Groq API key for LLM inference")
    groq_model: str = Field(
        default="llama-3.1-8b-instant",
        description="Groq model ID (llama-3.1-8b-instant, mixtral-8x7b-32768, etc.)"
    )
    groq_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    groq_max_tokens: int = Field(default=1024, ge=1, le=8192)
    groq_timeout: int = Field(default=30, description="Request timeout in seconds")

    # ── OCR ────────────────────────────────────────────────────
    nvidia_api_key: str = Field(default="", description="NVIDIA API key for Nemotron OCR-v2")
    ocr_space_api_key: str = Field(default="", description="OCR.space API key (free tier: 500/day)")
    ocr_timeout: int = Field(default=30)
    tesseract_cmd: Optional[str] = Field(
        default=None,
        description="Path to tesseract binary. Auto-detected if None."
    )

    # ── Supabase ───────────────────────────────────────────────
    supabase_url: str = Field(default="", description="Supabase project URL")
    supabase_key: str = Field(default="", description="Supabase anon/service key")

    # ── Application ────────────────────────────────────────────
    debug: bool = Field(default=False)
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    cors_origins: str = Field(
        default="*",
        description="Comma-separated CORS origins"
    )

    # ── Derived properties ─────────────────────────────────────

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    @property
    def has_nvidia_ocr(self) -> bool:
        return bool(self.nvidia_api_key)

    @property
    def has_ocr_space(self) -> bool:
        return bool(self.ocr_space_api_key)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance. Call this everywhere instead of Settings()."""
    return Settings()
