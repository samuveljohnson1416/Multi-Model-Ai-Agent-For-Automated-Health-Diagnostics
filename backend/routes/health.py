"""
GET /api/health — service health and provider status.
"""

from fastapi import APIRouter, Request

from ..models.health import HealthResponse, ProviderStatus
from ..config import get_settings

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """
    Check the health of all service providers.
    Returns status of Groq LLM, OCR, and Supabase.
    """
    settings = get_settings()
    providers = []

    # LLM status — one entry per configured provider
    llm = request.app.state.llm_service
    llm_status = llm.get_status()
    provider_details = llm_status.get("providers", {})
    if provider_details:
        for name, detail in provider_details.items():
            providers.append(ProviderStatus(
                name=f"llm_{name}",
                available=detail.get("available", False),
                model=detail.get("model"),
            ))
    else:
        providers.append(ProviderStatus(
            name="llm",
            available=llm_status.get("available", False),
            error="No LLM provider configured (rule-based fallback active)",
        ))

    # OCR status
    ocr = request.app.state.ocr_service
    ocr_status = ocr.get_status()
    providers.append(ProviderStatus(
        name="ocr",
        available=ocr_status["available"],
    ))

    # Database status
    providers.append(ProviderStatus(
        name="supabase",
        available=settings.has_supabase,
        error="Not configured" if not settings.has_supabase else None,
    ))

    # Overall status
    all_ok = all(p.available for p in providers)
    any_ok = any(p.available for p in providers)

    if all_ok:
        status = "ok"
    elif any_ok:
        status = "degraded"
    else:
        status = "error"

    return HealthResponse(
        status=status,
        version="3.0.0",
        providers=providers,
    )
