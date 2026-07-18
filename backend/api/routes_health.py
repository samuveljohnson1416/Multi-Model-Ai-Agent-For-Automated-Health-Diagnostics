"""
Health routes — GET /api/health, GET /api/status
"""

import logging
from fastapi import APIRouter
from backend.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", summary="Basic health check")
def health_check():
    """Returns 200 OK when the backend is running."""
    return {
        "status": "ok",
        "app": settings.app_title,
        "version": settings.app_version,
    }


@router.get("/status", summary="Service availability status")
def service_status():
    """
    Check availability of external services:
    - OCR providers (Tesseract, cloud APIs)
    - LLM providers (Ollama, HuggingFace)
    """
    status: dict = {
        "ocr": _check_ocr_status(),
        "llm": _check_llm_status(),
        "ollama": _check_ollama(settings.ollama_url),
    }
    return status


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_ocr_status() -> dict:
    try:
        from utils.ocr_provider import get_ocr_status
        return get_ocr_status()
    except Exception as exc:
        logger.debug("OCR status check failed: %s", exc)
        return {"available": False, "error": str(exc)}


def _check_llm_status() -> dict:
    try:
        from utils.llm_provider import get_llm_status
        return get_llm_status()
    except Exception as exc:
        logger.debug("LLM status check failed: %s", exc)
        return {"available": False, "error": str(exc)}


def _check_ollama(url: str) -> dict:
    try:
        import requests as _requests
        resp = _requests.get(f"{url}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = [m.get("name") for m in resp.json().get("models", [])]
            return {"running": True, "url": url, "models": models}
        return {"running": False, "url": url}
    except Exception:
        return {"running": False, "url": url}
