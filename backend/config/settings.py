"""
Centralised application settings loaded from environment variables / .env file.

Usage:
    from backend.config.settings import settings
    print(settings.ollama_url)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    # ── Project paths ────────────────────────────────────────────────────────
    project_root: Path = PROJECT_ROOT
    config_dir: Path = PROJECT_ROOT / "config"

    # ── FastAPI ───────────────────────────────────────────────────────────────
    app_title: str = "Multi-Model AI Health Diagnostics"
    app_version: str = "2.0.0"
    debug: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins (React dev server + production)
    cors_origins: list[str] = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://localhost:8000",
        ).split(",")
        if o.strip()
    ]

    # ── Ollama ────────────────────────────────────────────────────────────────
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "mistral:instruct")

    # ── LLM provider ─────────────────────────────────────────────────────────
    hf_api_token: str = os.getenv("HF_API_TOKEN", "")
    hf_model_id: str = os.getenv(
        "HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2"
    )
    llm_provider_priority: str = os.getenv("LLM_PROVIDER_PRIORITY", "ollama_first")
    llm_timeout: int = int(os.getenv("LLM_TIMEOUT", "30"))
    llm_max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "3"))

    # ── OCR provider ─────────────────────────────────────────────────────────
    ocr_space_api_key: str = os.getenv("OCR_SPACE_API_KEY", "")
    google_vision_api_key: str = os.getenv("GOOGLE_VISION_API_KEY", "")
    ocr_provider_priority: str = os.getenv("OCR_PROVIDER_PRIORITY", "tesseract_first")
    ocr_timeout: int = int(os.getenv("OCR_TIMEOUT", "30"))


settings = Settings()
