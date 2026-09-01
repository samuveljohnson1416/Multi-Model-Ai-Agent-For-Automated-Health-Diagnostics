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
        default="openai/gpt-oss-20b",
        description="Groq model ID for general agents (openai/gpt-oss-20b, groq/compound, etc.)"
    )
    groq_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    groq_max_tokens: int = Field(default=1024, ge=1, le=8192)
    groq_timeout: int = Field(default=30, description="Request timeout in seconds")
    groq_risk_model: str = Field(
        default="openai/gpt-oss-120b",
        description="Groq model ID used by the Risk Agent (larger reasoning model).",
    )

    # ── Google Gemini LLM ─────────────────────────────────────
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_model: str = Field(
        default="gemini-flash-latest",
        description="Gemini model ID (gemini-flash-latest, gemini-3.6-flash, etc.)",
    )
    gemini_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    gemini_max_tokens: int = Field(default=1024, ge=1, le=8192)

    # ── Agent → Provider mapping ──────────────────────────────
    # Which provider each agent prefers. Falls back to any available
    # provider (then rule-based) when the preferred one is not configured.
    agent_extraction_provider: str = Field(default="gemini")
    agent_diagnosis_provider: str = Field(default="groq")
    agent_risk_provider: str = Field(default="groq")
    agent_nutrition_provider: str = Field(default="gemini")
    agent_chat_provider: str = Field(default="groq")

    # ── OCR ────────────────────────────────────────────────────
    nvidia_api_key: str = Field(default="", description="NVIDIA API key for Nemotron OCR-v2")
    ocr_timeout: int = Field(default=30)
    tesseract_cmd: Optional[str] = Field(
        default=None,
        description="Path to tesseract binary. Auto-detected if None."
    )
    # ── Developer / debug flags ────────────────────────────────
    ocr_disable_tesseract: bool = Field(
        default=False,
        description=(
            "[DEV] Set to true to skip local Tesseract OCR entirely. "
            "Useful for testing NVIDIA Nemotron in isolation."
        ),
    )
    poppler_path: Optional[str] = Field(
        default=None,
        description="Path to poppler bin folder for pdf2image on Windows."
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

    # ── Security ───────────────────────────────────────────────
    api_key: str = Field(
        default="",
        description="Optional API key for endpoint protection. If set, all /api/* requests must include X-API-Key header."
    )
    max_upload_mb: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum allowed file upload size in megabytes."
    )

    # ── Derived properties ─────────────────────────────────────

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def has_llm(self) -> bool:
        """True when at least one LLM provider is configured."""
        return self.has_groq or self.has_gemini

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    @property
    def has_nvidia_ocr(self) -> bool:
        return bool(self.nvidia_api_key)

    @property
    def tesseract_enabled(self) -> bool:
        """False when OCR_DISABLE_TESSERACT=true (developer override)."""
        return not self.ocr_disable_tesseract

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

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
